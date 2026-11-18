#!/usr/bin/env python3
"""Parse the three pasted pages of V2EX thread 1248284 into corpus_old.json."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'data' / 'raw_old'
OUT = ROOT / 'data' / 'corpus_old.json'


def load_lines():
    lines = []
    for name in ('page1.txt', 'page2.txt', 'page3.txt'):
        lines += (RAW / name).read_text(encoding='utf-8').splitlines()
    return lines


def parse():
    lines = load_lines()
    anchors = []
    for i, line in enumerate(lines):
        if line.strip() == 'Reply' and i + 1 < len(lines) and lines[i + 1].strip().isdigit():
            anchors.append((i, int(lines[i + 1].strip())))

    floors = [n for _, n in anchors]
    assert floors == list(range(1, 262)), (len(floors), floors[:3], floors[-3:])

    BADGES = {'PRO', 'OP'}

    replies = []
    for k, (i, floor) in enumerate(anchors):
        block = lines[max(0, i - 6):i]
        date_idx = next((j for j, x in enumerate(block) if '月' in x and '日' in x), None)
        assert date_idx is not None and date_idx >= 2, (floor, block)
        # Header is "author \t\t" / "author" / optional badge / date.
        if block[date_idx - 1].strip() in BADGES:
            author = block[date_idx - 2].strip()
            header_rel = date_idx - 3
        else:
            author = block[date_idx - 1].strip()
            header_rel = date_idx - 2
        assert author and author not in BADGES, (floor, author, block)
        date_line = block[date_idx].strip()
        likes = 0
        m = re.search(r'❤️(\d+)', date_line)
        if m:
            likes = int(m.group(1))
        date_text = re.sub(r'❤️\d+', '', date_line).strip()
        date_text = re.sub(r'\s+via\s+.*$', '', date_text).strip()
        dm = re.match(r'(\d+)\s*月\s*(\d+)\s*日', date_text)
        assert dm, (floor, date_text)
        date = f'2026-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}'
        start = i + 2
        if k + 1 < len(anchors):
            ni = anchors[k + 1][0]
            nblock = lines[max(0, ni - 6):ni]
            ndate = next(j for j, x in enumerate(nblock) if '月' in x and '日' in x)
            nheader_rel = ndate - (3 if nblock[ndate - 1].strip() in BADGES else 2)
            end = max(0, ni - 6) + nheader_rel
        else:
            end = len(lines)
        text = '\n'.join(lines[start:end]).strip()
        replies.append({
            'floor': floor,
            'author': author,
            'time': date,
            'likes': likes,
            'text': text,
        })

    authors = {r['author'] for r in replies}
    meta = {
        'title': '马克思的按需分配，是不是高估了人性？',
        'op': 'space2020',
        'created_at': '2026-10-13',
        'last_reply': '2026-10-24 11:27:38 +08:00',
        'views': 14183,
        'reply_count': 261,
        'pages': 3,
        'url': 'https://v2ex.com/t/1248284',
        'op_content': '最近读马克思，说社会主义制度下，一切都是按需分配的，不会有人多拿多占么',
        'tags': ['马克思', '按需分配', '人性'],
        'authors': len(authors),
    }
    data = {'meta': meta, 'replies': replies}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {OUT} with {len(replies)} replies, {len(authors)} authors')
    return data


if __name__ == '__main__':
    data = parse()
    dates = {}
    for r in data['replies']:
        dates[r['time']] = dates.get(r['time'], 0) + 1
    print('dates:', dates)
    print('empty text:', [r['floor'] for r in data['replies'] if not r['text']])
    print('longest:', max(data['replies'], key=lambda r: len(r['text']))['floor'])
