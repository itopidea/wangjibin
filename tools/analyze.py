#!/usr/bin/env python3
"""Compute every statistic used on the page. No hand-typed numbers in prose.

Two samples share one codebook:
  main = t/1257906, 174 replies, 2026-11-18, minute-level timestamps
  old  = t/1248284, 261 replies, 2026-10-13..24, day-level timestamps
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ST = {'A': '明确否定', 'B': '有条件成立', 'C': '明确肯定', 'D': '概念悬置', 'E': '元讨论'}
TAGS = {
    'T1': '人性与欲望', 'T2': '稀缺与物理限制', 'T3': '分配权与监督',
    'T4': '需求定义与语义', 'T5': '生产力与极大丰富', 'T6': '制度与激励',
    'T7': '思想觉悟', 'T8': '技术路径', 'T9': '文本与作者考据',
    'T10': '经验与历史案例', 'T11': '意识形态与道德审判', 'T12': '元讨论',
    'T13': '文化类比', 'N': '无论证断言',
}
LEX = {
    '需/需求': ['需'],
    '物质/物资': ['物质', '物资'],
    '分配': ['分配'],
    '人性/欲望': ['人性', '欲望', '贪婪', '自私'],
    '生产力': ['生产力'],
    '觉悟/精神': ['觉悟', '精神'],
    '稀缺/有限': ['稀缺', '有限', '不够'],
    '权力/腐败': ['权力', '权利', '腐败', '官僚', '特权'],
    '制度/法律': ['制度', '法律'],
    '马克思': ['马克思', '老马'],
    'AI/机器人': ['AI', '机器人', '天网'],
    '空气': ['空气'],
    '洗手液': ['洗手液'],
    '低保/福利': ['低保', '福利', '全民基本收入'],
    '位置性资源': ['杨幂', '刘亦菲', '媳妇', '处女', '湖景房', '城堡', '火星'],
    '苏联/红色高棉': ['苏联', '红色高棉'],
    '北欧': ['瑞典', '丹麦', '挪威', '芬兰', '冰岛', '北欧'],
    '乌托邦/宗教': ['乌托邦', '宗教', '信仰', '天堂'],
    '共享单车': ['共享单车'],
    '自助餐': ['自助餐'],
    '配给/粮票': ['配给', '粮票', '大锅饭'],
    '插管/虚拟': ['插管', '矩阵', '虚拟世界', '海洛因'],
    '核聚变/能源': ['核聚变', '能源'],
}


def mean(xs):
    return sum(xs) / len(xs) if xs else 0


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return 0
    return s[n // 2 - 1] / 2 + s[n // 2] / 2 if n % 2 == 0 else s[n // 2]


def analyze(coded, sample):
    R = coded['replies']
    n = len(R)
    author_counts = Counter(r['author'] for r in R)
    stance_counts = Counter(r['stance'] for r in R)
    tag_counts = Counter(t for r in R for t in r['tags'])

    matrix = {s: {t: 0 for t in TAGS} for s in ST}
    for r in R:
        for t in r['tags']:
            matrix[r['stance']][t] += 1

    thirds = []
    for i in range(3):
        lo, hi = i * n // 3, (i + 1) * n // 3
        seg = R[lo:hi]
        c = Counter(x['stance'] for x in seg)
        thirds.append({
            'label': f'{lo + 1}–{hi} 楼',
            'range': [lo + 1, hi],
            'counts': {s: c.get(s, 0) for s in ST},
            'total': len(seg),
            't3': sum(1 for x in seg if 'T3' in x['tags']),
            't1': sum(1 for x in seg if 'T1' in x['tags']),
            't4': sum(1 for x in seg if 'T4' in x['tags']),
            't10': sum(1 for x in seg if 'T10' in x['tags']),
        })

    if sample == 'main':
        times = [datetime.strptime(r['time'], '%Y-%m-%d %H:%M:%S %z') for r in R]
        start, end = times[0], times[-1]
        span_min = (end - start).total_seconds() / 60
        span_text = f'{int(span_min // 60)} 小时 {int(span_min % 60)} 分'
        span_days = None
        bins = defaultdict(lambda: Counter())
        for r, t in zip(R, times):
            key = t.replace(minute=(t.minute // 10) * 10, second=0, microsecond=0)
            bins[key]['total'] += 1
            bins[key][r['stance']] += 1
        bin_list = [{
            'time': k.strftime('%H:%M'),
            'total': bins[k]['total'],
            'counts': {s: bins[k].get(s, 0) for s in ST},
        } for k in sorted(bins)]
        five = Counter()
        for t in times:
            five[t.replace(minute=(t.minute // 5) * 5, second=0, microsecond=0)] += 1
        peak_t, peak_v = five.most_common(1)[0]
        peak = {
            'time': peak_t.strftime('%H:%M'),
            'count': peak_v,
            'floors': [r['floor'] for r, t in zip(R, times)
                       if t.replace(minute=(t.minute // 5) * 5, second=0, microsecond=0) == peak_t],
        }
        first_time = start.strftime('%H:%M:%S')
        last_time = end.strftime('%H:%M:%S')
    else:
        days = [datetime.strptime(r['time'], '%Y-%m-%d') for r in R]
        start, end = days[0], days[-1]
        span_days = (end - start).days
        span_min = None
        span_text = f'{span_days} 天'
        bins = defaultdict(lambda: Counter())
        for r, t in zip(R, days):
            bins[t]['total'] += 1
            bins[t][r['stance']] += 1
        keys = []
        d = start
        while d <= end:
            keys.append(d)
            d += timedelta(days=1)
        bin_list = [{
            'time': k.strftime('%m-%d'),
            'total': bins[k]['total'] if k in bins else 0,
            'counts': {s: bins[k].get(s, 0) if k in bins else 0 for s in ST},
        } for k in keys]
        peak_k = max(bins, key=lambda k: bins[k]['total'])
        peak_v = bins[peak_k]['total']
        peak = {
            'time': peak_k.strftime('%m-%d'),
            'count': peak_v,
            'floors': [r['floor'] for r, t in zip(R, days) if t == peak_k],
        }
        first_time = None
        last_time = None

    mention_re = re.compile(r'@([A-Za-z0-9_\-]+)')
    mentions = Counter()
    mention_replies = 0
    for r in R:
        ms = mention_re.findall(r['text'])
        if ms:
            mention_replies += 1
        for m in ms:
            mentions[m] += 1

    lengths = [len(r['text']) for r in R]
    kw = {}
    for label, words in LEX.items():
        hits = [r['floor'] for r in R if any(w in r['text'] for w in words)]
        kw[label] = {'count': len(hits), 'floors': hits}

    direct = sum(1 for r in R if r['stance'] in 'ABC')
    basic_floors = [r['floor'] for r in R if r['basic']]
    doubt_floors = [r['floor'] for r in R if r['doubt']]
    b_floors = [r['floor'] for r in R if r['stance'] == 'B']
    meta_dup = [r['floor'] for r in R if 'T12' in r['tags']]

    pair_mentions = Counter()
    for r in R:
        for m in mention_re.findall(r['text']):
            pair_mentions[tuple(sorted((r['author'], m)))] += 1

    result = {
        'sample': sample,
        'n': n,
        'authors': len(author_counts),
        'span_minutes': round(span_min) if span_min is not None else None,
        'span_days': span_days,
        'span_text': span_text,
        'first_time': first_time,
        'last_time': last_time,
        'first_date': start.strftime('%Y-%m-%d'),
        'last_date': end.strftime('%Y-%m-%d'),
        'views': coded['meta']['views'],
        'created_at': coded['meta']['created_at'],
        'stance_counts': {s: stance_counts.get(s, 0) for s in ST},
        'stance_pct': {s: round(100 * stance_counts.get(s, 0) / n, 1) for s in ST},
        'tag_counts': {t: tag_counts.get(t, 0) for t in TAGS},
        'tag_pct': {t: round(100 * tag_counts.get(t, 0) / n, 1) for t in TAGS},
        'matrix': matrix,
        'thirds': thirds,
        'bins': bin_list,
        'peak': peak,
        'top_authors': author_counts.most_common(8),
        'mention_replies': mention_replies,
        'top_mentions': mentions.most_common(8),
        'median_len': median(lengths),
        'mean_len': round(mean(lengths), 1),
        'max_len': max(lengths),
        'keywords': kw,
        'direct_answers': direct,
        'negative_share_of_direct': round(100 * stance_counts.get('A', 0) / direct, 1) if direct else 0,
        'definitional': sum(1 for r in R if 'T4' in r['tags']),
        't4_by_stance': {s: matrix[s]['T4'] for s in ST},
        'basic_floors': basic_floors,
        'doubt_floors': doubt_floors,
        'b_floors': b_floors,
        'meta_dup': meta_dup,
        'first_a': round(100 * thirds[0]['counts']['A'] / thirds[0]['total'], 1),
        'last_a': round(100 * thirds[2]['counts']['A'] / thirds[2]['total'], 1),
        'first_de': round(100 * (thirds[0]['counts']['D'] + thirds[0]['counts']['E']) / thirds[0]['total'], 1),
        'last_de': round(100 * (thirds[2]['counts']['D'] + thirds[2]['counts']['E']) / thirds[2]['total'], 1),
        'top_pair_mentions': pair_mentions.most_common(5),
    }
    return result


main = json.loads((BASE / 'data' / 'coded.json').read_text(encoding='utf-8'))
old = json.loads((BASE / 'data' / 'coded_old.json').read_text(encoding='utf-8'))
A = analyze(main, 'main')
O = analyze(old, 'old')
A['old'] = O

# preserved named-author detail used by the narrative
qx = [r for r in main['replies'] if r['author'] == 'QingXuJiaZhi']
qx_to = [r['floor'] for r in main['replies'] if '@QingXuJiaZhi' in r['text']]
A['qx_count'] = len(qx)
A['qx_floors'] = [r['floor'] for r in qx]
A['qx_mentions'] = len(qx_to)
A['qx_mentioned_floors'] = qx_to

# ---------------- cross-sample comparisons ----------------
main_R, old_R = main['replies'], old['replies']
combined_n = len(main_R) + len(old_R)
combined_authors = len({r['author'] for r in main_R} | {r['author'] for r in old_R})
combined_stance = Counter()
for r in main_R + old_R:
    combined_stance[r['stance']] += 1

stance_diff = {}
for s in ST:
    stance_diff[s] = {
        'main': A['stance_pct'][s],
        'old': O['stance_pct'][s],
        'diff': round(A['stance_pct'][s] - O['stance_pct'][s], 1),
    }

TAG_COMPARE = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T9', 'T10', 'T11', 'T12']
tag_rate = {}
for t in TAG_COMPARE:
    tag_rate[t] = {
        'main': A['tag_pct'][t],
        'old': O['tag_pct'][t],
        'diff': round(A['tag_pct'][t] - O['tag_pct'][t], 1),
    }

KEY_COMPARE = ['需/需求', '物质/物资', '分配', '人性/欲望', '生产力', '权力/腐败',
               '马克思', '空气', '共享单车', '自助餐', '配给/粮票', '北欧', 'AI/机器人']
key_compare = {}
for label in KEY_COMPARE:
    m = A['keywords'][label]['count']
    o = O['keywords'][label]['count']
    key_compare[label] = {
        'main': m, 'old': o,
        'main_pct': round(100 * m / len(main_R), 1),
        'old_pct': round(100 * o / len(old_R), 1),
    }

old_day1 = [r for r in old_R if r['time'] == '2026-10-13']
old_tail = [r for r in old_R if r['time'] != '2026-10-13']


def share(rows):
    c = Counter(r['stance'] for r in rows)
    return {
        'n': len(rows),
        'counts': {s: c.get(s, 0) for s in ST},
        'pct': {s: round(100 * c.get(s, 0) / len(rows), 1) if rows else 0 for s in ST},
        'a_t1': sum(1 for r in rows if r['stance'] == 'A' and 'T1' in r['tags']),
        't3': sum(1 for r in rows if 'T3' in r['tags']),
        'e': c.get('E', 0),
    }


report_floor = next(r['floor'] for r in main_R if r.get('report'))
pre_report = [r for r in main_R if r['floor'] < report_floor]
post_report = [r for r in main_R if r['floor'] > report_floor]
direct_report_replies = [
    r['floor'] for r in post_report
    if 'itopidea' in r['text'] or '报告' in r['text'] or '研究' in r['text']
]
cross_refs = [
    r['floor'] for r in main_R + old_R
    if '1248284' in r['text'] or '上一个讨论' in r['text']
]

compare = {
    'combined_n': combined_n,
    'combined_authors': combined_authors,
    'combined_stance_counts': {s: combined_stance.get(s, 0) for s in ST},
    'stance': stance_diff,
    'tag_rate': tag_rate,
    'keywords': key_compare,
    'old_day1': share(old_day1),
    'old_tail': share(old_tail),
    'main_pre_report': share(pre_report),
    'main_post_report': share(post_report),
    'report_floor': report_floor,
    'post_report_floors': [post_report[0]['floor'], post_report[-1]['floor']],
    'post_report_count': len(post_report),
    'post_report_a': sum(1 for r in post_report if r['stance'] == 'A'),
    'direct_report_replies': direct_report_replies,
    'cross_ref_floors': cross_refs,
    'old_duel_authors': ['tf2', 'jayhuang0044'],
    'old_duel_replies': sum(1 for r in old_R if r['author'] in ('tf2', 'jayhuang0044')),
    'old_duel_tail_replies': sum(1 for r in old_R if r['author'] in ('tf2', 'jayhuang0044') and r['floor'] >= 172),
    'old_duel_range': [172, 259],
}

A['compare'] = compare
(BASE / 'data' / 'analysis.json').write_text(
    json.dumps(A, ensure_ascii=False, indent=2), encoding='utf-8')
(BASE / 'data' / 'analysis_old.json').write_text(
    json.dumps(O, ensure_ascii=False, indent=2), encoding='utf-8')

print(json.dumps({k: v for k, v in A.items()
                  if k not in ('matrix', 'thirds', 'bins', 'keywords', 'old', 'compare')},
                 ensure_ascii=False, indent=2))
print('\nOLD SUMMARY')
print(json.dumps({k: v for k, v in O.items()
                  if k not in ('matrix', 'thirds', 'bins', 'keywords')},
                 ensure_ascii=False, indent=2))
print('\nCOMPARE')
print(json.dumps(compare, ensure_ascii=False, indent=2))
