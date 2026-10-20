#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
매체·광역별 건수를 지난 회차와 비교해, 원본에서 통째로 빠진 것 같은 곳을 짚는다 (2026-10-20).

260803 대구·경북 타운보드S −353, 260901 전북·전남광주 −154 처럼 원본 결손은 「정상 변동」이 아니라
사장님 판단 사항인데, 지금까지는 대화 속 눈으로만 잡았다. 이 스크립트가 같은 기준으로 매번 짚는다.

쓰는 법:
  .venv/bin/python check_counts.py                 # git HEAD 의 data.json ↔ 지금 data.json
  .venv/bin/python check_counts.py 옛.json 새.json  # 두 파일
결과: 표(JSON 한 줄 요약 포함). 짚을 곳이 있으면 종료 코드 3.
"""
import json
import subprocess
import sys
from collections import Counter

LABEL = {
    'focusmedia': '포커스', 'townboard_op': '타운보드S', 'townboard_l': '타운보드L', 'townboard': '만첨',
    'htpost': 'HTPOST 영상', 'htpost_leaflet': 'HTPOST 전단지',
    'mediameet_interior': 'MM 내부', 'mediameet_waiting': 'MM 대기공간',
}
# 광역 이름을 짧게 맞춘다(엑셀마다 '대구'·'대구광역시'가 섞여 같은 곳이 둘로 갈리지 않게)
SHORT = [('서울', '서울'), ('부산', '부산'), ('대구', '대구'), ('인천', '인천'), ('광주', '광주'), ('대전', '대전'),
         ('울산', '울산'), ('세종', '세종'), ('경기', '경기'), ('강원', '강원'), ('충청북', '충북'), ('충북', '충북'),
         ('충청남', '충남'), ('충남', '충남'), ('전라북', '전북'), ('전북', '전북'), ('전라남', '전남'), ('전남', '전남'),
         ('경상북', '경북'), ('경북', '경북'), ('경상남', '경남'), ('경남', '경남'), ('제주', '제주')]
# 짚는 기준: 매체 전체가 3% 넘게 줄거나 / 광역 하나가 20건 이상 그리고 25% 이상 줄거나 / 10건 넘던 광역이 0건
TYPE_DROP = 0.03
REGION_MIN, REGION_RATE = 20, 0.25
# 만첨은 해제가 몰리는 주가 잦아 매체 전체 기준만 본다(261006 107→49 · 260928 −102 모두 원본 그대로였음)
REGION_SKIP = {'townboard'}


def region(city):
    c = (city or '').strip()
    for k, v in SHORT:
        if c.startswith(k):
            return v
    return c or '(지역 없음)'


def tally(items):
    by_type, by_reg = Counter(), Counter()
    for it in items:
        t = it.get('type')
        by_type[t] += 1
        by_reg[(t, region(it.get('city')))] += 1
    return by_type, by_reg


def compare(old, new):
    ot, orr = tally(old)
    nt, nr = tally(new)
    flags = []
    for t in sorted(set(ot) | set(nt), key=lambda x: -ot.get(x, 0)):
        o, n = ot.get(t, 0), nt.get(t, 0)
        if o and (o - n) / o > TYPE_DROP:
            flags.append({'type': t, 'region': None, 'old': o, 'new': n})
    for (t, r) in sorted(set(orr) | set(nr)):
        if t in REGION_SKIP:
            continue
        o, n = orr.get((t, r), 0), nr.get((t, r), 0)
        if (o - n >= REGION_MIN and (o - n) / o >= REGION_RATE) or (o > 10 and n == 0):
            flags.append({'type': t, 'region': r, 'old': o, 'new': n})
    rows = [{'type': t, 'label': LABEL.get(t, t), 'old': ot.get(t, 0), 'new': nt.get(t, 0)}
            for t in sorted(set(ot) | set(nt), key=lambda x: -max(ot.get(x, 0), nt.get(x, 0)))]
    return rows, flags, len(old), len(new)


def head_json():
    out = subprocess.run(['git', 'show', 'HEAD:data.json'], capture_output=True, check=True).stdout
    return json.loads(out)


def main():
    if len(sys.argv) == 3:
        old = json.load(open(sys.argv[1], encoding='utf-8'))
        new = json.load(open(sys.argv[2], encoding='utf-8'))
    else:
        old = head_json()
        new = json.load(open('data.json', encoding='utf-8'))
    rows, flags, o, n = compare(old, new)
    print(f"총 {o:,} → {n:,} ({n - o:+,})")
    for r in rows:
        d = r['new'] - r['old']
        print(f"  {r['label']:<12} {r['old']:>6,} → {r['new']:>6,} ({d:+,})")
    if flags:
        print("⚠️ 원본에서 빠졌는지 확인할 곳:")
        for f in flags:
            where = f"{LABEL.get(f['type'], f['type'])} {f['region']}" if f['region'] else f"{LABEL.get(f['type'], f['type'])} 전체"
            print(f"  - {where}: {f['old']:,} → {f['new']:,} ({f['new'] - f['old']:+,})")
    else:
        print("줄어든 지역 없음")
    print("SUMMARY " + json.dumps({'old': o, 'new': n, 'rows': rows, 'flags': flags}, ensure_ascii=False))
    return 3 if flags else 0


if __name__ == '__main__':
    sys.exit(main())
