#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
매체 리스트 입력 파일을 한곳에서 정한다 (2026-10-20 — 메일 자동 최신화).

전에는 회차마다 convert_xlsx_251201.py · convert_mediameet.py · merge_all_data.py 안의
파일명 6곳과 만첨 시트명, HTPOST 변환 함수를 손으로 바꿔 끼웠다. 이제 세 스크립트는
inputs.json 을 읽고, 이번 회차에 온 파일은 `adopt` 로 inputs.json 에 올린다.
안 온 매체는 inputs.json 의 이전 파일을 그대로 쓴다(전에 옛 파일명을 코드에 남겨 두던 것과 같은 효과).

쓰는 법:
  .venv/bin/python media_inputs.py adopt _inbox/rounds/261019   # 이 폴더의 매체 엑셀을 이번 회차로
  .venv/bin/python media_inputs.py show                         # 지금 매체별 입력 파일
"""
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime

# pandas 는 시트를 읽을 때만 쓴다 — 메일 지켜보기(맥 기본 파이썬, pandas 없음)도 classify 를 같이 쓰게 하려고 (10-20)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS = os.path.join(BASE_DIR, 'inputs.json')

# 파일명 → 매체 종류. 위에서부터 먼저 맞는 것 하나(송출요청서 등 목록이 아닌 첨부는 어디에도 안 맞음)
KINDS = [
    ('focus', r'엘리베이터\s*TV\s*설치리스트'),
    ('townboard', r'타운보드\s*가동리스트'),
    ('mancheom_s', r'타운보드\s*S\s*만첨'),
    ('mancheom_l', r'타운보드\s*L\s*만첨'),
    ('mediameet', r'MEDIA\s*MEET\s*설치리스트'),
    ('htpost_partner', r'HTPOST\s*가동리스트.{0,3}로컬\s*파트너사'),
    ('htpost_hyundai', r'현대에이치티.*단지별\s*로컬광고단가'),
]
LABEL = {
    'focus': '엘리베이터TV(포커스)', 'townboard': '타운보드 가동', 'mancheom_s': '만첨 S',
    'mancheom_l': '만첨 L', 'mediameet': 'MEDIA MEET', 'htpost_partner': 'HTPOST 파트너사',
    'htpost_hyundai': 'HTPOST 현대에이치티',
}


def nfc(s):
    return unicodedata.normalize('NFC', s or '')


def classify(filename):
    name = nfc(os.path.basename(filename))
    if not name.lower().endswith('.xlsx') or name.startswith(('~$', '.')):
        return None
    for kind, pat in KINDS:
        if re.search(pat, name, re.I):
            return kind
    return None


def file_date(filename):
    """파일명 끝쪽 6자리 날짜(YYMMDD). 현대에이치티처럼 월만 있으면 그 달 1일로 본다."""
    name = nfc(os.path.basename(filename))
    six = re.findall(r'(?<!\d)(\d{6})(?!\d)', name)
    if six:
        return six[-1]
    m = re.search(r'_(\d{1,2})\s*월?', name)
    if m and 1 <= int(m.group(1)) <= 12:
        mon, today = int(m.group(1)), date.today()
        year = today.year - 1 if mon > today.month else today.year  # 1월에 온 12월 파일은 작년 것
        return f"{year % 100:02d}{mon:02d}01"
    return '000000'


def load():
    with open(INPUTS, encoding='utf-8') as f:
        return json.load(f)


def resolve(kind):
    """그 매체의 지금 입력 파일 절대경로. 없으면 이유를 말하고 멈춘다(조용히 다른 파일로 대신하지 않는다)."""
    ent = load().get(kind)
    if not ent:
        raise SystemExit(f"inputs.json 에 {kind} 입력이 없습니다")
    path = os.path.join(BASE_DIR, ent['file'])
    if not os.path.exists(path):
        raise SystemExit(f"{LABEL.get(kind, kind)} 입력 파일이 없습니다: {ent['file']}")
    return path


def htpost_video_source():
    """HTPOST 영상은 더 최근에 들어온 쪽(현대에이치티 통합 / 로컬파트너사)에서 읽는다.
    260901: 통합파일이 와서 영상·전단지 모두 통합에서 / 261006: 파트너사만 와서 영상은 파트너사, 전단지는 통합 유지."""
    d = load()
    h, p = d.get('htpost_hyundai', {}), d.get('htpost_partner', {})
    if p and p.get('adopted', '') > h.get('adopted', ''):
        return 'htpost_partner'
    return 'htpost_hyundai'


def pick_sheet(path, pattern):
    """시트 이름이 pattern 에 맞는 것이 정확히 하나일 때만 그 이름. 0개·여러 개면 멈춘다(첫 시트로 대신 읽지 않는다)."""
    import pandas as pd
    sheets = pd.ExcelFile(path).sheet_names
    hits = [s for s in sheets if re.search(pattern, nfc(s))]
    if len(hits) != 1:
        raise SystemExit(f"{os.path.basename(path)}: 시트 '{pattern}' 후보 {len(hits)}개 — 시트 목록 {sheets}")
    return hits[0]


def read_sheet(path, sheet, required, header_default):
    """필수 컬럼이 모두 잡히는 헤더행을 고른다. 지난 회차 값(header_default)을 먼저 보고, 안 되면 0~9행."""
    import pandas as pd
    tried = [header_default] + [h for h in range(10) if h != header_default]
    for hdr in tried:
        df = pd.read_excel(path, sheet_name=sheet, header=hdr)
        cols = {str(c).strip() for c in df.columns}
        if set(required).issubset(cols):
            df.columns = [str(c).strip() if str(c).strip() in required else c for c in df.columns]
            if hdr != header_default:
                print(f"⚠️ {os.path.basename(path)} [{sheet}] 헤더행이 {header_default}→{hdr} 로 바뀌어 자동으로 맞춤")
            return df
    raise SystemExit(f"{os.path.basename(path)} [{sheet}]: 필수 컬럼 {sorted(required)} 이 있는 헤더행을 못 찾음")


def adopt(folder):
    folder = os.path.abspath(folder)
    found = {}
    skipped = []
    for fn in sorted(os.listdir(folder)):
        kind = classify(fn)
        if not kind:
            if fn.lower().endswith('.xlsx'):
                skipped.append(fn)
            continue
        if kind not in found or file_date(fn) > file_date(found[kind]):
            found[kind] = fn
    d = load()
    today = datetime.now().isoformat(timespec='minutes')  # 같은 날 두 파일(현대·파트너사)의 앞뒤를 가리려고 시각까지
    changed = []
    for kind, fn in found.items():
        rel = os.path.relpath(os.path.join(folder, fn), BASE_DIR)
        if d.get(kind, {}).get('file') != rel:
            changed.append(kind)
        d[kind] = {'file': rel, 'date': file_date(fn), 'adopted': today}
    tmp = INPUTS + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, INPUTS)
    result = {
        'round_folder': os.path.relpath(folder, BASE_DIR),
        'updated': {k: found[k] for k in changed},
        'kept': {k: d[k]['file'] for k in d if k not in changed},
        'skipped': skipped,
        'htpost_video_from': htpost_video_source(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def show():
    d = load()
    for kind, _ in KINDS:
        ent = d.get(kind)
        print(f"{LABEL[kind]:<16} {ent['file'] if ent else '(없음)'}  · 들인 날 {ent.get('adopted', '-') if ent else '-'}")
    print(f"HTPOST 영상 읽는 곳: {LABEL[htpost_video_source()]}")


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'adopt':
        adopt(sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == 'show':
        show()
    else:
        print(__doc__)
        sys.exit(2)
