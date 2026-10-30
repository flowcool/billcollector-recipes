"""Classify changed inputs; a missing comparison always requires full checks."""
import argparse
import os
import subprocess


def requires_checks(paths):
    return any(not path.endswith('.md') for path in paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    event = os.environ['CI_EVENT']
    base = os.environ.get('CI_BASE', '')
    head = os.environ.get('CI_HEAD', '')
    full = True
    if event in {'pull_request', 'push'} and base and head and set(base) != {'0'}:
        comparison = f'{base}...{head}' if event == 'pull_request' else f'{base}..{head}'
        names = subprocess.check_output(['git', 'diff', '--name-only', '-z', comparison])
        full = requires_checks([p for p in names.decode().split('\0') if p])
    with open(args.output, 'a') as output:
        output.write(f'full={str(full).lower()}\n')


if __name__ == '__main__':
    main()
