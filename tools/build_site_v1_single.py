#!/usr/bin/env python3
"""Render the static research page from the coded corpus + analysis."""
import html
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SITE = BASE / 'site'
coded = json.loads((BASE / 'data' / 'coded.json').read_text(encoding='utf-8'))
analysis = json.loads((BASE / 'data' / 'analysis.json').read_text(encoding='utf-8'))

ST = coded['stances']
TAGS = coded['tag_labels']
COLORS = {'A': 'var(--a)', 'B': 'var(--b)', 'C': 'var(--c)', 'D': 'var(--d)', 'E': 'var(--e)'}
N = analysis['n']


def esc(s):
    return html.escape(str(s), quote=False)


def pct(v, total=N):
    return f'{100 * v / total:.1f}%'


def svg_open(w, h, label):
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}" '
            f'xmlns="http://www.w3.org/2000/svg">')


def text(x, y, s, size=11, fill='var(--ink)', anchor='start', weight=400,
         extra='', opacity=None):
    op = f' opacity="{opacity}"' if opacity is not None else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{op}{extra}>{esc(s)}</text>')


def donut():
    w = h = 250
    cx = cy = 125
    r = 92
    sw = 26
    circ = 2 * math.pi * r
    parts = [svg_open(w, h, '立场分布环形图：' + '，'.join(
        f'{s} {ST[s]} {analysis["stance_counts"][s]} 条' for s in 'ABCDE')),
             '<title>立场分布</title>',
             '<circle cx="125" cy="125" r="92" fill="none" stroke="var(--line-2)" stroke-width="26"/>']
    acc = 0.0
    for s in 'ABCDE':
        v = analysis['stance_counts'][s]
        if not v:
            continue
        seg = v / N * circ
        gap = 3.0
        dash = max(seg - gap, 0.8)
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{COLORS[s]}" '
            f'stroke-width="{sw}" stroke-dasharray="{dash:.2f} {circ - dash:.2f}" '
            f'stroke-dashoffset="{-acc:.2f}" transform="rotate(-90 {cx} {cy})">'
            f'<title>{s} {ST[s]}：{v} 条（{pct(v)}）</title></circle>')
        acc += seg
    parts.append(text(125, 120, str(N), size=44, anchor='middle', weight=600,
                      extra=' style="font-family:var(--serif)"'))
    parts.append(text(125, 140, '条回复', size=10.5, fill='var(--muted)', anchor='middle'))
    parts.append(text(125, 156, '5 类立场', size=9, fill='var(--faint)', anchor='middle'))
    parts.append('</svg>')

    legend = ['<div class="legend">']
    for s in 'ABCDE':
        v = analysis['stance_counts'][s]
        legend.append(
            f'<div class="legend-row"><span class="legend-dot" style="background:{COLORS[s]}"></span>'
            f'<span>{s} {ST[s]}</span><span class="cnt">{v} <span class="pct">{pct(v)}</span></span></div>')
    legend.append('</div>')
    return '<div class="donut-wrap">' + ''.join(parts) + ''.join(legend) + '</div>'


TAG_FAMILY = {
    'T1': 'var(--a)', 'T2': 'var(--a)',
    'T3': 'var(--teal)', 'T6': 'var(--teal)',
    'T4': 'var(--d)',
    'T5': 'var(--c)', 'T7': 'var(--c)', 'T8': 'var(--c)',
    'T9': 'var(--b)', 'T10': 'var(--b)',
    'T11': 'var(--e)', 'T12': 'var(--e)', 'T13': 'var(--e)', 'N': 'var(--e)',
}


def tag_bars():
    w = 760
    top = 34
    row_h = 31
    h = top + len(TAGS) * row_h + 14
    left = 118
    bar_max = 520
    maxv = max(analysis['tag_counts'].values())
    rows = sorted(analysis['tag_counts'].items(), key=lambda kv: (-kv[1], kv[0]))
    parts = [svg_open(w, h, '论证标签条形图：' + '，'.join(
        f'{TAGS[t]} {v} 条' for t, v in rows[:5]) + '，其余见条形')]
    parts.append('<title>论证资源出场次数</title>')
    for gv in (0, 10, 20, 30):
        x = left + gv / maxv * bar_max
        parts.append(f'<line x1="{x:.1f}" y1="24" x2="{x:.1f}" y2="{top + len(TAGS) * row_h - 4}" stroke="var(--line-2)" stroke-width="1" stroke-dasharray="2 3"/>')
        parts.append(text(x, 18, str(gv), size=9, fill='var(--faint)', anchor='middle'))
    parts.append(text(w - 6, 14, '点击条形可在附录筛选', size=9, fill='var(--faint)', anchor='end'))
    for i, (t, v) in enumerate(rows):
        y = top + i * row_h
        cy = y + row_h / 2
        bw = v / maxv * bar_max
        label = TAGS[t]
        parts.append(
            f'<g data-filter-tag="{t}" tabindex="0" role="button" aria-label="在附录中筛选 {esc(label)}">'
            f'<title>{t} {esc(label)}：{v} 条（{pct(v)}）</title>'
            f'<rect x="0" y="{y}" width="{w}" height="{row_h}" fill="transparent"/>'
            + text(left - 10, cy + 4, label, size=10.5, fill='var(--ink-2)', anchor='end')
            + f'<rect x="{left}" y="{cy - 7:.1f}" width="{bw:.1f}" height="14" rx="1" fill="{TAG_FAMILY[t]}"/>'
            + text(left + bw + 7, cy + 4, str(v), size=10.5, fill='var(--ink)', weight=600)
            + text(left + bw + 30, cy + 4, pct(v), size=8.5, fill='var(--faint)')
            + '</g>')
    parts.append('</svg>')
    legend = ('<div class="legend-inline">'
              '<span><i style="background:var(--a)"></i>人性 / 稀缺</span>'
              '<span><i style="background:var(--d)"></i>需求定义</span>'
              '<span><i style="background:var(--teal)"></i>权力 / 制度</span>'
              '<span><i style="background:var(--c)"></i>生产力 / 觉悟 / 技术</span>'
              '<span><i style="background:var(--b)"></i>文本 / 经验</span>'
              '<span><i style="background:var(--e)"></i>审判 / 元讨论 / 文化 / 断言</span>'
              '</div>')
    return legend + ''.join(parts)


HEAT_TAGS = ['T4', 'T1', 'T11', 'T10', 'T2', 'T9', 'T6', 'T3', 'T5', 'T12']
HEAT_LABELS = {
    'T4': ('需求定义', '与语义'), 'T1': ('人性', '与欲望'), 'T11': ('意识形态', '与审判'),
    'T10': ('经验与', '历史案例'), 'T2': ('稀缺与', '物理限制'), 'T9': ('文本与', '作者考据'),
    'T6': ('制度', '与激励'), 'T3': ('分配权', '与监督'), 'T5': ('生产力与', '极大丰富'),
    'T12': ('元讨论', ''),
}


def heatmap():
    w, h = 900, 386
    left, top, cw, ch = 130, 66, 74, 52
    parts = [svg_open(w, h, '立场与论证标签热力图：否定派多用人性与稀缺，条件肯定多用生产力与文本考据，概念悬置多用需求定义')]
    parts.append('<title>立场 × 论证标签</title>')
    for c, t in enumerate(HEAT_TAGS):
        x = left + c * cw + (cw - 4) / 2
        l1, l2 = HEAT_LABELS[t]
        parts.append(
            f'<g data-filter-tag="{t}" tabindex="0" role="button" aria-label="在附录中筛选 {esc(TAGS[t])}">'
            f'<title>{t} {esc(TAGS[t])}</title>'
            f'<rect x="{left + c * cw}" y="14" width="{cw - 4}" height="42" fill="transparent"/>'
            + text(x, 30, l1, size=9.5, fill='var(--muted)', anchor='middle')
            + (text(x, 42, l2, size=9.5, fill='var(--muted)', anchor='middle') if l2 else '')
            + '</g>')
    for r, s in enumerate('ABCDE'):
        total = analysis['stance_counts'][s]
        y = top + r * ch
        parts.append(text(left - 12, y + ch / 2 + 4,
                          f'{s} {ST[s]} · {total}', size=10.5, fill='var(--ink-2)', anchor='end'))
        for c, t in enumerate(HEAT_TAGS):
            v = analysis['matrix'][s][t]
            p = 100 * v / total if total else 0
            x = left + c * cw
            if v == 0:
                parts.append(f'<rect x="{x}" y="{y}" width="{cw - 4}" height="{ch - 4}" fill="#f1ebde"/>')
                parts.append(text(x + (cw - 4) / 2, y + ch / 2 + 3, '–', size=11, fill='var(--faint)', anchor='middle'))
            else:
                op = min(0.10 + 0.72 * (p / 75), 0.88)
                fill_text = '#fff' if p >= 30 else 'var(--ink)'
                parts.append(
                    f'<g><title>{s} {ST[s]} × {t} {esc(TAGS[t])}：{v} 条，占 {p:.1f}%</title>'
                    f'<rect x="{x}" y="{y}" width="{cw - 4}" height="{ch - 4}" fill="var(--d)" fill-opacity="{op:.2f}"/>'
                    + text(x + (cw - 4) / 2, y + 21, str(v), size=12.5, fill=fill_text,
                           anchor='middle', weight=600)
                    + text(x + (cw - 4) / 2, y + 35, f'{p:.1f}%', size=8.5, fill=fill_text, anchor='middle', opacity=.85)
                    + '</g>')
    # scale legend
    lx, ly = 400, 352
    parts.append(text(left, ly + 7, '底色 = 占该立场回复的百分比（行内归一）', size=9, fill='var(--muted)'))
    for i in range(6):
        v = i * 15
        op = 0.10 + 0.72 * (v / 75)
        x = lx + i * 34
        parts.append(f'<rect x="{x}" y="{ly}" width="30" height="9" fill="var(--d)" fill-opacity="{op:.2f}"/>')
        parts.append(text(x + 15, ly + 22, f'{v}%', size=8, fill='var(--faint)', anchor='middle'))
    parts.append('</svg>')
    return ''.join(parts)


def timeline():
    w, h = 920, 330
    left, right, top = 46, 52, 34
    plot_w = w - left - right
    plot_h = 220
    maxv = 22
    start = datetime(2026, 11, 18, 10, 20)
    bmap = {b['time']: b for b in analysis['bins']}
    first = min(datetime.strptime(k, '%H:%M') for k in bmap)
    last = max(datetime.strptime(k, '%H:%M') for k in bmap)
    keys = []
    t = first
    while t <= last:
        keys.append(t.strftime('%H:%M'))
        t += timedelta(minutes=10)
    bins = [bmap.get(k, {'time': k, 'total': 0, 'counts': {s: 0 for s in 'ABCDE'}}) for k in keys]
    maxv = max(22, max(b['total'] for b in bins) + 1)
    peak_idx = next((i for i, b in enumerate(bins) if b['time'] == analysis['peak']['time']), 6)
    band = plot_w / len(bins)
    barw = 27
    parts = [svg_open(w, h, '回复时间线：每 10 分钟一个柱，堆叠显示五种立场；11:20 至 11:25 出现峰值 12 条；折线为累计回复数')]
    parts.append('<title>三小时回复时间线</title>')
    for gv in (0, 5, 10, 15, 20):
        y = top + plot_h - gv / maxv * plot_h
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - right}" y2="{y:.1f}" stroke="var(--line-2)" stroke-width="1" stroke-dasharray="2 4"/>')
        parts.append(text(left - 8, y + 3.5, str(gv), size=9, fill='var(--faint)', anchor='end'))
    # bars
    cum = 0
    cum_points = []
    for i, b in enumerate(bins):
        x = left + i * band + (band - barw) / 2
        acc = 0.0
        for s in 'ABCDE':
            v = b['counts'].get(s, 0)
            if not v:
                continue
            seg = v / maxv * plot_h
            y = top + plot_h - acc - seg
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{barw}" height="{seg:.1f}" fill="{COLORS[s]}" stroke="var(--paper-2)" stroke-width="0.8"><title>{b["time"]} {s} {ST[s]}：{v} 条</title></rect>')
            acc += seg
        cum += b['total']
        cx = x + barw / 2
        cy = top + plot_h - cum / N * plot_h
        cum_points.append((cx, cy))
    # cumulative line
    if cum_points:
        d = 'M ' + ' L '.join(f'{x:.1f} {y:.1f}' for x, y in cum_points)
        parts.append(f'<path d="{d}" fill="none" stroke="var(--ink)" stroke-width="1.3" opacity="0.62"/>')
        for x, y in cum_points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="var(--paper-2)" stroke="var(--ink)" stroke-width="1.1" opacity="0.75"/>')
        parts.append(text(cum_points[-1][0] + 6, cum_points[-1][1] + 3, str(N), size=9, fill='var(--ink)', weight=600))
    # axes labels
    for i in range(0, len(bins), 2):
        x = left + i * band + band / 2
        parts.append(text(x, top + plot_h + 18, bins[i]['time'], size=8.5, fill='var(--faint)', anchor='middle'))
    parts.append(f'<line x1="{left}" y1="{top + plot_h}" x2="{w - right}" y2="{top + plot_h}" stroke="var(--line)" stroke-width="1"/>')
    # peak
    px = left + peak_idx * band + band / 2
    parts.append(f'<line x1="{px:.1f}" y1="{top - 4}" x2="{px:.1f}" y2="{top + plot_h}" stroke="var(--accent)" stroke-width="1" stroke-dasharray="3 4" opacity="0.45"/>')
    peak_end = (datetime.strptime(analysis['peak']['time'], '%H:%M') + timedelta(minutes=5)).strftime('%H:%M')
    parts.append(text(px + 6, 18, f'{analysis["peak"]["time"]}–{peak_end} 峰值 {analysis["peak"]["count"]} 条', size=9, fill='var(--accent)'))
    # right axis
    for v in (0, N // 2, N):
        y = top + plot_h - v / N * plot_h
        parts.append(text(w - right + 6, y + 3.5, str(v), size=8.5, fill='var(--faint)'))
    parts.append(text(w - right + 6, top - 8, '累计', size=8.5, fill='var(--faint)'))
    parts.append('</svg>')
    legend = ('<div class="legend-inline">'
              + ''.join(f'<span><i style="background:{COLORS[s]}"></i>{s} {ST[s]}</span>' for s in 'ABCDE')
              + '</div>')
    return legend + ''.join(parts)


def thirds():
    w, h = 900, 340
    left, barw = 120, 610
    rows = analysis['thirds']
    parts = [svg_open(w, h, '三段演化图：' + '、'.join(
        f"{row['counts']['A'] / row['total'] * 100:.1f}%" for row in rows) + '；分配权标签 ' + '、'.join(str(row.get('t3', 0)) for row in rows) + ' 条')]
    parts.append('<title>三段演化</title>')
    parts.append(text(left + barw, 28, '各段内归一为 100%', size=9, fill='var(--faint)', anchor='end'))
    for r, row in enumerate(rows):
        y = 46 + r * 58
        total = row['total']
        parts.append(text(left - 12, y + 18, row['label'], size=11.5, fill='var(--ink-2)', anchor='end'))
        parts.append(f'<rect x="{left}" y="{y}" width="{barw}" height="26" fill="var(--line-2)"/>')
        acc = 0.0
        for s in 'ABCDE':
            v = row['counts'][s]
            if not v:
                continue
            seg = v / total * barw
            x = left + acc
            parts.append(f'<rect x="{x:.1f}" y="{y}" width="{seg:.1f}" height="26" fill="{COLORS[s]}" stroke="var(--paper-2)" stroke-width="0.8"><title>{row["label"]} {s} {ST[s]}：{v} 条</title></rect>')
            if seg > 30:
                parts.append(text(x + seg / 2, y + 17.5, str(v), size=9.5, fill='#fff', anchor='middle', weight=600))
            acc += seg
        negpct = 100 * row['counts']['A'] / total
        parts.append(text(left + barw + 12, y + 18, f'否定 {negpct:.1f}%', size=10, fill='var(--accent)', weight=600))
    # divider
    t3 = [row.get('t3', 0) for row in rows]
    parts.append('<line x1="70" y1="204" x2="830" y2="204" stroke="var(--line)" stroke-width="1"/>')
    parts.append(text(left, 226, f'分配权标签（T3）的条数：{t3[0]} → {t3[1]} → {t3[2]}', size=10, fill='var(--muted)'))
    # mini line
    xs = [180, 430, 680]
    vals = t3
    ymax = max(vals) or 1
    ys = [288 - v / ymax * 48 for v in vals]
    parts.append('<line x1="150" y1="288" x2="710" y2="288" stroke="var(--line-2)" stroke-width="1"/>')
    d = 'M ' + ' L '.join(f'{x} {y:.1f}' for x, y in zip(xs, ys))
    parts.append(f'<path d="{d}" fill="none" stroke="var(--teal)" stroke-width="2"/>')
    for x, y, v in zip(xs, ys, vals):
        parts.append(f'<circle cx="{x}" cy="{y:.1f}" r="4" fill="var(--teal)"/>')
        parts.append(text(x, y - 10, str(v), size=10.5, fill='var(--teal)', anchor='middle', weight=600))
    for x, lab in zip(xs, [f"{row['range'][0]}–{row['range'][1]}" for row in rows]):
        parts.append(text(x, 306, lab, size=8.5, fill='var(--faint)', anchor='middle'))
    parts.append('</svg>')
    legend = ('<div class="legend-inline">'
              + ''.join(f'<span><i style="background:{COLORS[s]}"></i>{s} {ST[s]}</span>' for s in 'ABCDE')
              + '<span><i style="background:var(--teal)"></i>T3 分配权</span>'
              + '</div>')
    return legend + ''.join(parts)


MAP_POINTS = [
    # floor, xnorm, ynorm, short description
    (18, 0.60, 0.74, 'QingXuJiaZhi · 阶段论 / 低保'),
    (23, 0.72, 0.82, 'QingXuJiaZhi · 物质 + 觉悟双条件'),
    (120, 0.83, 0.66, 'doudouisamomo · 天网 / 机器决策'),
    (27, 0.26, 0.74, 'acthtml · 制度让获利依赖创造价值'),
    (46, 0.17, 0.62, 'Cheons · 道德上限 / 法律下限'),
    (20, 0.70, 0.38, 'Eathein · 即使可控核聚变也不行'),
    (74, 0.82, 0.28, 'dnfQzjPBXtWmML · 物化与等级在基因里'),
    (99, 0.90, 0.43, 'firechat · 丰裕下的 99% 奴隶'),
    (102, 0.62, 0.22, 'Eathein · 控制空气制造短缺'),
    (63, 0.22, 0.35, 'PoorBe · 欲望存在就不可能'),
    (98, 0.35, 0.22, 'wupher · 只要世界是物质的'),
    (138, 0.48, 0.32, 'erbin · 分配权悖论'),
]


def concept_map():
    w, h = 760, 560
    left, right, top, bottom = 70, 700, 50, 470
    midx, midy = 385, 260
    by_floor = {r['floor']: r for r in coded['replies']}
    parts = [svg_open(w, h, '争论地图：横轴为物质极大丰富是否可达，纵轴为人的利他与觉悟是否可塑；四个象限分别放置代表楼层')]
    parts.append('<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="6" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="var(--muted)"/></marker></defs>')
    parts.append('<title>争论地图</title>')
    # quadrant fills
    parts.append(f'<rect x="{left}" y="{top}" width="{midx-left}" height="{midy-top}" fill="#f8f3e8"/>')
    parts.append(f'<rect x="{midx}" y="{top}" width="{right-midx}" height="{midy-top}" fill="#f4ede0"/>')
    parts.append(f'<rect x="{left}" y="{midy}" width="{midx-left}" height="{bottom-midy}" fill="#f2ede4"/>')
    parts.append(f'<rect x="{midx}" y="{midy}" width="{right-midx}" height="{bottom-midy}" fill="#eef0e8"/>')
    # axes
    parts.append(f'<line x1="{midx}" y1="{bottom}" x2="{midx}" y2="{top}" stroke="var(--muted)" stroke-width="1.2" marker-end="url(#arrow)"/>')
    parts.append(f'<line x1="{left}" y1="{midy}" x2="{right}" y2="{midy}" stroke="var(--muted)" stroke-width="1.2" marker-end="url(#arrow)"/>')
    parts.append(text(midx, 36, '人心可塑', size=10, fill='var(--muted)', anchor='middle'))
    parts.append(text(midx, 492, '人心难塑', size=10, fill='var(--muted)', anchor='middle'))
    parts.append(text(left + 4, 248, '物质难至', size=9.5, fill='var(--muted)'))
    parts.append(text(right - 4, 248, '物质可至', size=9.5, fill='var(--muted)', anchor='end'))
    # quadrant labels
    quads = [
        (left + 18, 82, '制度 / 觉悟先行', '物质难至 · 人心可塑', 'start'),
        (right - 18, 82, '乐观方案', '物质可至 · 人心可塑', 'end'),
        (left + 18, 446, '双重否定', '物质难至 · 人心难塑', 'start'),
        (right - 18, 446, '丰裕但不自由', '物质可至 · 人心难塑', 'end'),
    ]
    for x, y, title, sub, anchor in quads:
        parts.append(text(x, y, title, size=14, fill='var(--ink)', anchor=anchor, weight=600,
                          extra=' style="font-family:var(--serif)"'))
        parts.append(text(x, y + 17, sub, size=9.5, fill='var(--faint)', anchor=anchor))
    # points
    for floor, nx, ny, desc in MAP_POINTS:
        r = by_floor[floor]
        x = left + nx * (right - left)
        y = bottom - ny * (bottom - top)
        s = r['stance']
        parts.append(
            f'<g><title>#{floor} {esc(r["author"])}：{esc(desc)}</title>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="{COLORS[s]}" stroke="var(--paper-2)" stroke-width="2.5"/>'
            + text(x, y + 4, str(floor), size=10.5, fill='#fff', anchor='middle', weight=600)
            + '</g>')
    parts.append('</svg>')
    legend = ['<div class="map-legend">']
    for floor, _, _, desc in MAP_POINTS:
        s = by_floor[floor]['stance']
        legend.append(f'<div class="mi"><b style="color:{COLORS[s]}">#{floor}</b><span>{esc(desc)}</span></div>')
    legend.append('</div>')
    return ''.join(parts) + ''.join(legend)


KW_ROWS = [(label, analysis['keywords'][label]['count']) for label in (
    '需/需求', '分配', '物质/物资', '人性/欲望', '马克思',
    '觉悟/精神', 'AI/机器人', '位置性资源', '稀缺/有限', '权力/腐败')]


def kw_rows():
    out = []
    maxv = KW_ROWS[0][1]
    for i, (label, v) in enumerate(KW_ROWS):
        color = 'var(--accent)' if i == 0 else 'var(--teal)'
        out.append(f'<div class="kw-row"><span>{esc(label)}</span>'
                   f'<div class="kw-bar"><i style="width:{v/maxv*100:.1f}%;background:{color}"></i></div>'
                   f'<span class="n">{v}</span></div>')
    return ''.join(out)


def appendix_rows():
    out = []
    for r in coded['replies']:
        s = r['stance']
        tags = r['tags']
        tag_html = ''.join(
            f'<span class="tag" title="{esc(TAGS[t])}">{t} {esc(TAGS[t])}</span>' for t in tags)
        flags = []
        if r.get('doubt'):
            flags.append('<span class="tiny">条件存疑</span>')
        if r.get('basic'):
            flags.append('<span class="tiny">基本需求可行</span>')
        note = esc(r['note']) if r['note'] else '—'
        if flags:
            note = note + '<br>' + ' · '.join(flags)
        body = esc(r['text']).replace('\n', '<br>')
        out.append(
            f'<tr id="f{r["floor"]}" data-stance="{s}" data-tags="{" ".join(tags)}">'
            f'<td class="floor"><a href="#f{r["floor"]}">{r["floor"]}</a></td>'
            f'<td class="when">{r["time"][11:16]}</td>'
            f'<td class="author">{esc(r["author"])}</td>'
            f'<td class="stance-cell"><span class="chip st-{s}"><span class="dot"></span>{s} {ST[s]}</span></td>'
            f'<td class="tags-cell">{tag_html}</td>'
            f'<td class="note">{note}</td>'
            f'<td class="txt">{body}</td>'
            f'</tr>')
    return ''.join(out)


def tag_options():
    out = ['<option value="">全部标签</option>']
    for t, v in sorted(analysis['tag_counts'].items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(f'<option value="{t}">{t} {esc(TAGS[t])} ({v})</option>')
    return ''.join(out)


def main():
    template = (SITE / 'template.html').read_text(encoding='utf-8')
    replacements = {
        '{{DONUT}}': donut(),
        '{{TAG_BARS}}': tag_bars(),
        '{{HEATMAP}}': heatmap(),
        '{{TIMELINE}}': timeline(),
        '{{THIRDS}}': thirds(),
        '{{CONCEPT_MAP}}': concept_map(),
        '{{KW_ROWS}}': kw_rows(),
        '{{APPENDIX_ROWS}}': appendix_rows(),
        '{{TAG_OPTIONS}}': tag_options(),
    }
    for k, v in replacements.items():
        if k not in template:
            raise SystemExit(f'missing placeholder: {k}')
        template = template.replace(k, v)
    data_js = json.dumps(coded, ensure_ascii=False).replace('</', '<\\/')
    template = template.replace('/* __CODED_JSON__ */', 'window.__CODED__ = ' + data_js + ';')
    if '{{' in template:
        import re
        left = re.findall(r'\{\{[A-Z_]+\}\}', template)
        raise SystemExit(f'unreplaced placeholders: {left}')
    out = BASE / 'index.html'
    out.write_text(template, encoding='utf-8')
    print('wrote', out, len(template.encode('utf-8')), 'bytes')
    print('donut segments:', template.count('stroke-dasharray'))
    print('appendix rows:', template.count('data-stance="'))
    print('svg count:', template.count('<svg'))
    print('chart groups:', template.count('data-filter-tag='))


if __name__ == '__main__':
    main()
