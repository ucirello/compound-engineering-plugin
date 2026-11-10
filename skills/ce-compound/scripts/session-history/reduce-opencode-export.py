#!/usr/bin/env python3
"""Reduce a supported OpenCode JSON export to bounded text/tool evidence.

Usage: reduce-opencode-export.py export.json evidence.jsonl
Both paths must be inside the current workspace's local .tmp directory.
"""
import json
import os
import sys


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root = os.path.realpath(os.path.join(os.getcwd(), '.tmp'))
    paths = [os.path.realpath(p) for p in sys.argv[1:]]
    if not all(os.path.commonpath([root, p]) == root for p in paths):
        raise SystemExit('export and evidence must remain under workspace .tmp')
    with open(paths[0], encoding='utf-8') as source:
        data = json.load(source)
    messages = data.get('messages', []) if isinstance(data, dict) else data
    budget = 2_000_000
    with os.fdopen(os.open(paths[1], os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as output:
        for message in messages:
            info = message.get('info', message)
            role = info.get('role')
            if role not in ('user', 'assistant'):
                continue
            for part in message.get('parts', []):
                kind = part.get('type')
                if kind == 'text':
                    evidence = part.get('text', '')
                elif kind == 'tool':
                    state = part.get('state', {})
                    # Bound fields independently so bulky inputs cannot hide
                    # the tool name or its short result. Never copy reasoning.
                    def short(value, limit):
                        text = value if isinstance(value, str) else json.dumps(value)
                        return text[:limit] + (' [truncated]' if len(text) > limit else '')

                    evidence = {'tool': part.get('tool'),
                                'input': short(state.get('input'), 2000),
                                'output': short(state.get('output'), 2000),
                                'error': short(state.get('error'), 1000)}
                else:
                    continue
                text = evidence if isinstance(evidence, str) else json.dumps(evidence)
                record = json.dumps({'role': role, 'type': kind,
                                         'evidence': text[:12000],
                                         'truncated': len(text) > 12000}) + '\n'
                if len(record) > budget:
                    output.write(json.dumps({'omitted': 'remaining evidence exceeds budget; reduce a narrower source range'}) + '\n')
                    return
                output.write(record)
                budget -= len(record)


if __name__ == '__main__':
    main()
