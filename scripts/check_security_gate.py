"""Enforce complete CodeQL processing and the repository's alert thresholds."""
import json
import os
import subprocess


def validate_analyses(analyses, revision):
    categories = {row.get('category') for row in analyses
                  if row.get('commit_sha') == revision
                  and row.get('tool', {}).get('name') == 'CodeQL'
                  and not row.get('error')}
    if not {'/language:python', '/language:actions'} <= categories:
        raise ValueError('Both successful CodeQL analyses must match this commit')


def validate_alerts(alerts):
    for alert in alerts:
        rule = alert.get('rule', {})
        if rule.get('severity') == 'error' or rule.get('security_severity_level') in {'high', 'critical'}:
            raise ValueError('CodeQL error or high/critical alert blocks this change')


def fetch(endpoint):
    raw = subprocess.check_output(['gh', 'api', '--paginate', '--slurp', endpoint])
    return [row for page in json.loads(raw) for row in page]


def main():
    repository = os.environ['GITHUB_REPOSITORY']
    reference = os.environ['GITHUB_REF']
    analyses = fetch(f'repos/{repository}/code-scanning/analyses?ref={reference}&per_page=100')
    validate_analyses(analyses, os.environ['GITHUB_SHA'])
    alerts = fetch(f'repos/{repository}/code-scanning/alerts?ref={reference}&state=open&per_page=100')
    validate_alerts(alerts)
    print('CodeQL analyses match this commit; no blocking alerts')


if __name__ == '__main__':
    main()
