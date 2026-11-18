#!/usr/bin/env python3
"""Parse the two saved V2EX pages into a structured JSON corpus."""
import html as htmllib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = [Path('/tmp/v2ex_p1.html'), Path('/tmp/v2ex_p2.html')]

TAG_RE = re.compile(r'<[^>]+>')
AT_RE = re.compile(r'@<a href="/member/[^"]+">([^<]+)</a>')


def clean(fragment: str) -> str:
    s = AT_RE.sub(lambda m: '@' + m.group(1) + ' ', fragment)
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = TAG_RE.sub('', s)
    s = htmllib.unescape(s)
    s = s.replace('\u00a0', ' ')
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s.strip()


def parse_page(path: Path):
    doc = path.read_text(encoding='utf-8')
    meta = {}
    title = re.search(r'<title>(.*?) - V2EX</title>', doc, re.S)
    if title:
        meta['title'] = htmllib.unescape(title.group(1).strip())
    h1 = re.search(r'<h1>(.*?)</h1>', doc, re.S)
    if h1:
        meta['title'] = clean(h1.group(1))
    op = re.search(
        r'<small class="gray"><a href="/member/([^"]+)">[^<]+</a> · '
        r'<span title="([^"]+)">[^<]+</span> · (\d+) views', doc)
    if op:
        meta['op'] = op.group(1)
        meta['created_at'] = op.group(2)
        meta['views'] = int(op.group(3))
    content = re.search(r'<div class="topic_content">(.*?)</div>', doc, re.S)
    if content:
        meta['op_content'] = clean(content.group(1))
    tags = re.findall(r'<a href="/tag/[^"]+" class="tag"><li class="fa fa-tag"></li> ([^<]+)</a>', doc)
    if tags:
        meta['tags'] = tags

    replies = []
    blocks = re.split(r'<div id="r_\d+" class="cell"', doc)[1:]
    for block in blocks:
        floor = re.search(r'<span class="no">(\d+)</span>', block)
        author = re.search(r'<img[^>]+alt="([^"]+)"[^>]+class="avatar"', block)
        if not author:
            author = re.search(r'<a href="/member/[^"]+" class="dark">([^<]+)</a>', block)
        ts = re.search(r'<span class="ago" title="([^"]+)">', block)
        body = re.search(r'<div class="reply_content">(.*?)</div>', block, re.S)
        if not (floor and body):
            continue
        replies.append({
            'floor': int(floor.group(1)),
            'author': htmllib.unescape(author.group(1)) if author else '',
            'time': ts.group(1) if ts else '',
            'text': clean(body.group(1)),
        })
    return meta, replies


def main():
    metas, replies = [], []
    for p in RAW:
        m, r = parse_page(p)
        metas.append(m)
        replies.extend(r)
    seen, corpus = set(), []
    for r in sorted(replies, key=lambda x: x['floor']):
        if r['floor'] in seen:
            continue
        seen.add(r['floor'])
        corpus.append(r)
    meta = next((m for m in metas if 'op' in m), metas[0])
    meta['reply_count'] = len(corpus)
    out = {'meta': meta, 'replies': corpus}
    (BASE / 'data' / 'corpus.json').parent.mkdir(parents=True, exist_ok=True)
    (BASE / 'data' / 'corpus.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    print('replies:', len(corpus), 'floors:', corpus[0]['floor'], '-', corpus[-1]['floor'])
    missing = [i for i in range(1, corpus[-1]['floor'] + 1) if i not in seen]
    print('missing floors:', missing)


if __name__ == '__main__':
    main()
