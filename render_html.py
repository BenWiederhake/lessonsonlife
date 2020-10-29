#!/usr/bin/env python3

import datetime
import html
import json
import shutil
import urllib.parse
import uuid
import yaml


LESSONS_FILE = 'lessons.yml'
COUNT_FIRST = 0
COUNT_PATTERN = "#{:02}"

TEMPLATE_BASE_FILE = 'template.html'
TEMPLATE_OVERVIEW = '<li><a class="text-monospace font-weight-light" href="#{uuid}">{number}</a> {title}</li>'
TEMPLATE_LESSON = '''\
<h3 id="{uuid}"><a class="text-reset text-monospace font-weight-light" href="#{uuid}">{number}</a> {title}</h3>
<p><dl class="row">
{items}
</dl></p>
'''
TEMPLATE_LESSON_ITEM = '''\
<dt class="col-sm-2">{key}</dt>
<dd class="col-sm-9">{value}</dd>\
'''
TEMPLATE_KEYS = ['Abstract', 'Negative example', 'Positive example', 'Consequence', 'See also']
# Raw HTML!
TEMPLATE_KEY_ALTERNATIVES = {'Consequence': 'Conse&shy;quence'}
TEMPLATE_IGNORE = set(['Title', 'UUID'])
EXPLAIN_UUID_CHECK = True


def convert_uuids(lessons):
    for lesson in lessons:
        lesson['UUID'] = str(uuid.UUID(lesson['UUID']))
        assert len(lesson['UUID']) == 2 * 16 + 4, lesson['UUID']
    for i in range(len(lessons)):
        for j in range(i):
            u_i = lessons[i]['UUID']
            u_j = lessons[j]['UUID']
            matches = sum(a == b for a, b in zip(u_i, u_j))
            # Even if you take a thousand UUIDs, and some pessimistic assumptions,
            # Less than half the time you see 8 matches, and only 5% of the time you see more than that.
            if matches > 4 + 1 + 8:
                if EXPLAIN_UUID_CHECK:
                    print(i, j, u_i, u_j, matches)
                print('ERROR: These UUIDs seem unrandom. Use actual UUIDs.\nHere are some actually-random ones:')
                for _ in range(round(len(lessons) * 1.01) + 5):
                    print(uuid.uuid4().urn)
                exit(1)


def wrap_value(string_or_list):
    if isinstance(string_or_list, str):
        return [string_or_list]
    elif isinstance(string_or_list, list):
        return string_or_list
    else:
        raise ValueError('Value "{}" is neither string nor list. Wat?'.format(string_or_list))


def render_html(lessons_dict):
    overview = []
    lessons_html = []
    for (i, lesson) in enumerate(lessons_dict):
        # Check format
        for k in TEMPLATE_IGNORE:
            if k not in lesson.keys():
                print('ERROR: Missing mandatory key "{}" in lesson {} (entry {}), will crash soon'.format(k, lesson, i))
        for k in lesson.keys():
            if k not in TEMPLATE_KEYS and k not in TEMPLATE_IGNORE:
                print('WARNING: Superfluous key "{}" in lesson {}'.format(k, lesson['UUID']))

        html_uuid = lesson['UUID']
        html_number = COUNT_PATTERN.format(i + COUNT_FIRST)
        html_title = html.escape(lesson['Title'])

        html_items = []
        for key in TEMPLATE_KEYS:
            if key not in lesson or not lesson[key]:
                print('WARNING: Missing recommended key "{}" in lesson {}'.format(key, lesson['UUID']))
                continue
            for value in wrap_value(lesson[key]):
                if isinstance(value, str):
                    formatted_value = html.escape(value)
                elif isinstance(value, dict):
                    assert len(value) == 1, value
                    value_text, value_url = list(value.items())[0]  # FIXME: Ugly!
                    formatted_value = '{}: <a class="text-monospace" href="{}">{}</a>'.format(
                        html.escape(value_text),
                        html.escape(urllib.parse.quote(value_url, safe=':/')),
                        html.escape(value_url))
                else:
                    raise AssertionError('tf is this shit?', value)
                if key in TEMPLATE_KEY_ALTERNATIVES:
                    key_html = TEMPLATE_KEY_ALTERNATIVES[key]
                else:
                    key_html = key
                html_items.append(TEMPLATE_LESSON_ITEM.format(key=key_html, value=formatted_value))

        lessons_html.append(TEMPLATE_LESSON.format(uuid=html_uuid, number=html_number, title=html_title, items='\n'.join(html_items)))
        overview.append(TEMPLATE_OVERVIEW.format(uuid=html_uuid,number=html_number, title=html_title))
    with open(TEMPLATE_BASE_FILE) as fp:
        template_base = fp.read()
    return template_base.format(
        overview='\n'.join(overview),
        lessons='\n'.join(lessons_html),
        last_build=datetime.datetime.now().astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M %Z'))


def install(filename):
    shutil.copyfile(filename, 'gh-pages/' + filename)


def run():
    print('In case you need a UUID:', uuid.uuid4().urn)
    with open(LESSONS_FILE) as fp:
        lessons_raw = yaml.safe_load(fp)
    # print(lessons_raw)
    with open('gh-pages/' + LESSONS_FILE + '.json', 'w') as fp:
        json.dump(lessons_raw, fp, separators=',:')
    convert_uuids(lessons_raw)
    with open('gh-pages/index.html', 'w') as fp:
        fp.write(render_html(lessons_raw))
    install('favicon.png')
    install('favicon.ico')
    install('bootstrap_4.5.1.min.css')
    install('LICENSE')
    install('logo.gif')
    install(LESSONS_FILE)


if __name__ == '__main__':
    run()
