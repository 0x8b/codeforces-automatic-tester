#!/usr/bin/env python

import os
import sys
import json
import shutil
import argparse

from time import time
from html import unescape
from pathlib import Path
from subprocess import PIPE, run
from html.parser import HTMLParser
from urllib.request import urlopen

VERSION = '0.1'
URL = 'https://codeforces.com'
RESET  = '\033[0m'
LANGUAGES = {
    'python': {
        'template': 'main.py',
        'run': 'python main.py',
    },
}


class ContestParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag == 'option':
            attrs = dict(attrs)

            if attrs['value'].isupper() and 'data-problem-name' in attrs:
                self.problems.append((attrs['value'], attrs['data-problem-name']))


class ProblemParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.data = ''
        self.tests = []
        self.toggle = True
        self.reading = False
        self.tests_div = False

    def handle_starttag(self, tag, attrs):
        if tag == 'pre' and self.tests_div:
            self.reading = True
        elif tag == 'div':
            attrs = dict(attrs)

            if 'class' in attrs and attrs['class'] == 'sample-test':
                self.tests_div = True
            elif 'class' in attrs and attrs['class'] not in ('input', 'output', 'title'):
                self.tests_div = False

    def handle_endtag(self, tag):
        if tag == 'pre' and self.tests_div:
            data = unescape(self.data)

            if self.toggle:
                self.tests.append([data])
            else:
                self.tests[-1].append(data)

            self.reading = False
            self.toggle = not self.toggle
            self.data = ''

    def handle_data(self, data):
        if self.reading:
            if data[0] == '\n':
                data = data[1:]

            self.data += data


def get_input(label):
    buff = []
    print(f'{label.upper()}:')

    while True:
        inp = input()

        if inp == '.':
            return '\n'.join(buff)

        buff.append(inp)


def print_red(text):
    print(f'\033[41m{text}{RESET}')

def print_green(text):
    print(f'\033[42m{text}{RESET}')

def print_label(label):
    print(f'\033[04m{label}{RESET}')


parser = argparse.ArgumentParser(
    description = f'Automatic tester for programming Codeforces contests.')

subparsers = parser.add_subparsers(dest = 'command')

parser_contest = subparsers.add_parser('contest')
parser_contest.add_argument('id', help = 'Contest id')
parser_contest.add_argument('-t', '--type', default = 'contest', help = 'Type of contest (contest or gym)')
parser_contest.add_argument('-l', '--lang', default = 'python', help = 'Language you want to use')

parser_test = subparsers.add_parser('test')
parser_test.add_argument('problem', help = 'Problem letter')
parser_test.add_argument('-a', '--add',    action = 'store_true', help = 'Add your test')
parser_test.add_argument('-r', '--remove', action = 'store_true', help = 'Remove last test')

args = parser.parse_args()

last_contest = Path('.last-codeforces-contest')

if args.command == 'contest':
    contest_id = args.id.zfill(6)

    assert args.type in ('contest', 'gym')
    assert args.lang in LANGUAGES

    last_contest.write_text(contest_id)
    contest_path = Path(contest_id)

    if contest_path.exists():
        exit(0)

    contest_path.mkdir()
    contest_path.joinpath('.language').write_text(args.lang)

    contest_url = '/'.join([URL, args.type, args.id])

    contest_parser = ContestParser()
    html = urlopen(contest_url).read()
    contest_parser.feed(html.decode('utf-8'))

    for symbol, name in contest_parser.problems:
        problem_parser = ProblemParser()
        html = urlopen(contest_url + f'/problem/{symbol}').read()
        problem_parser.feed(html.decode('utf-8'))
        tests = problem_parser.tests

        print(f'Downloading problem {symbol}...')
        sys.stdout.flush()

        problem_path = contest_path / symbol
        problem_path.mkdir()
        problem_path.joinpath('tests.json').write_text(json.dumps(tests))
        template = LANGUAGES[args.lang]['template']
        shutil.copy2(Path('templates') / template, problem_path / template)
elif args.command == 'test':
    problem = args.problem.upper()
    contest_id = last_contest.read_text()
    tests_path = Path(contest_id) / problem / 'tests.json'

    try:
        tests = json.loads(tests_path.read_text())
    except FileNotFoundError as fnfe:
        print_red('Problem not found')
        exit(0)


    if args.add or args.remove:
        if args.add:
            tests += [get_input('input'), get_input('output')]
        else:
            try:
                tests.pop()
            except IndexError:
                pass

        tests_path.write_text(json.dumps(tests))
        exit(0)

    passed, total = 0, len(tests)

    lang = (Path(contest_id) / '.language').read_text()

    os.chdir(Path(contest_id) / problem)

    for inp, out in tests:
        start = time()
        run_cmd = LANGUAGES[lang]['run']
        completed_run = run(run_cmd, input = inp.encode('utf-8'), stdout = PIPE)
        stop = time()

        output = completed_run.stdout.decode('utf-8').replace('\r', '').strip()

        print_label('input')
        print(inp)
        print_label('expected output')
        print(out)
        print_label('received output')
        print(output)

        duration = round(stop - start, 3)

        if output == out:
            passed += 1
            print_green(f'PASSED {duration}s')
        else:
            print_red(f'FAILED {duration}s')

        print('_' * 80)

        sys.stdout.flush()

    print(f'\033[44mPASSED {passed} of {total}{RESET}')
