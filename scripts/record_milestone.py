"""Commit only this project's verified work and retain honest local evidence.

The resulting hash is appended after the commit and included in the next one.
Run a final documentation commit to close the ledger. No network operations.
"""
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('message')
parser.add_argument('--phase', required=True)
parser.add_argument('--summary', required=True)
parser.add_argument('--checks', required=True)
parser.add_argument('--decision', default='Follow the approved local-only development plan.')
parser.add_argument('--paths', nargs='+', default=['.'])
args = parser.parse_args()

def git(*parts):
    return subprocess.check_output(['git', '-C', str(ROOT), *parts], text=True).strip()

assert git('config', '--local', '--get', 'user.name') in {'prettyglory', 'gloria-mbilinyi'}
assert git('config', '--local', '--get', 'user.email') == 'gloriambilinyi5@gmail.com'
log = ROOT / 'docs' / 'AGENT_DEVELOPMENT_LOG.md'
changed = git('status', '--short', '--', *args.paths)
assert changed, 'No changes; refusing an empty milestone.'
with log.open('a', encoding='utf-8') as stream:
    stream.write(f'\n## {args.phase}\n\nDate (UTC): {datetime.now(timezone.utc).isoformat()}\n\n'
                 'Human guidance: implement the TFPMDS master brief; continue locally, preserve identity, and never push.\n\n'
                 f'Agent work: {args.summary}\n\nTechnical decision: {args.decision}\n\n'
                 f'Checks actually executed: {args.checks}\n\nFiles changed at this milestone:\n\n```text\n{changed}\n```\n')
git('add', '--all', '--', *args.paths, 'docs/AGENT_DEVELOPMENT_LOG.md')
print(git('commit', '-m', args.message))
sha = git('rev-parse', 'HEAD')
with log.open('a', encoding='utf-8') as stream:
    stream.write(f'\nVerified milestone commit: `{sha}`.\n')
print(sha)
