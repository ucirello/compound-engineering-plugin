#!/usr/bin/env python3
"""Export one exact OpenCode source session and reduce before model reading."""
import argparse
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_session')
    parser.add_argument('--workspace-root', required=True)
    args = parser.parse_args()
    root = Path(args.workspace_root)
    if not root.is_absolute() or not (root / '.jj').is_dir():
        parser.error('workspace root must be an absolute JJ workspace root')
    if not args.source_session.startswith('ses_') or not all(c.isalnum() or c == '_' for c in args.source_session):
        parser.error('invalid exact source session ID')
    if args.source_session == os.environ.get('OPENCODE_SESSION_ID'):
        parser.error('source is the delegate own session, not the parent source')
    scratch = root / '.tmp' / 'rocketclaw-session-exports'
    scratch.mkdir(parents=True, exist_ok=True, mode=0o700)
    if scratch.is_symlink() or not scratch.resolve().is_relative_to(root.resolve()):
        parser.error('unsafe local export directory')
    raw = scratch / (args.source_session + '.json')
    reduced = scratch / (args.source_session + '.reduced.json')
    result = subprocess.run(['opencode', 'session', 'export', args.source_session], cwd=str(root), capture_output=True, text=True, timeout=120)
    if result.returncode:
        # Supported API fallback retains the exact ID; never inspect storage.
        result = subprocess.run(['opencode', 'api', 'get', '/api/session/' + args.source_session + '/message'], cwd=str(root), capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise SystemExit('Exact source export unavailable: ' + result.stderr[:500])
    data = json.loads(result.stdout)
    if isinstance(data, dict):
        exported_id = data.get('info', {}).get('id')
        if exported_id is not None and exported_id != args.source_session:
            raise SystemExit('Export returned a different source session; evidence rejected')
    messages = data.get('messages', []) if isinstance(data, dict) else data
    if not isinstance(messages, list) or not messages:
        raise SystemExit('Exact source export contains no supported messages; evidence incomplete')
    output = []
    for message in messages:
        info = message.get('info', message)
        if info.get('sessionID') not in (None, args.source_session):
            raise SystemExit('Message belongs to another source session; evidence rejected')
        role = info.get('role')
        if role not in ('user', 'assistant'):
            continue
        parts = []
        for part in message.get('parts', []):
            if part.get('type') == 'text':
                parts.append({'text': part.get('text', '')})
            elif part.get('type') == 'tool':
                state = part.get('state', {})
                parts.append({'tool': part.get('tool', ''), 'status': state.get('status'), 'short_result': str(state.get('output', state.get('error', '')))[:1000]})
        output.append({'role': role, 'parts': parts})
    if not output:
        raise SystemExit('No user/assistant evidence; coverage incomplete')
    for path, content in ((raw, result.stdout), (reduced, json.dumps({'source_session': args.source_session, 'messages': output}, ensure_ascii=False))):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
    print(reduced)


if __name__ == '__main__':
    main()
