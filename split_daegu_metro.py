#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대구교통공사 1/2/3호선 집계 데이터를 역별로 분리하여 data.json에 반영
"""
import json
import urllib.request
import urllib.parse
import ssl
import time
import copy

KAKAO_REST_API_KEY = 'd82eba93079458f667f074cb979a694d'
ssl._create_default_https_context = ssl._create_unverified_context

LINES = {
    '대구교통공사_1호선': [
        '설화명곡역','화원역','대곡역','진천역','월배역','상인역','월촌역','송현역',
        '서부정류장역','대명역','안지랑역','현충로역','영대병원역','교대역','명덕역',
        '반월당역','중앙로역','대구역','칠성시장역','신천역','동대구역','동구청역',
        '아양교역','동촌역','해안역','방촌역','용계역','율하역','신기역','반야월역',
        '각산역','안심역'
    ],
    '대구교통공사_2호선': [
        '문양역','다사역','대실역','강창역','계명대역','성서산업단지역','이곡역','용산역',
        '죽전역','감삼역','두류역','내당역','반고개역','청라언덕역','반월당역','경대병원역',
        '대구은행역','범어역','수성구청역','만촌역','담티역','연호역','대공원역','고산역',
        '신매역','사월역','정평역','임당역','영남대역'
    ],
    '대구교통공사_3호선': [
        '칠곡경대병원역','학정역','팔거역','동천역','칠곡운암역','구암역','태전역','매천역',
        '매천시장역','팔달역','공단역','만평역','팔달시장역','원대역','북구청역','달성공원역',
        '서문시장역','신남역','남산역','명덕역','건들바위역','대봉교역','수성시장역',
        '수성구민운동장역','어린이회관역','황금역','수성못역','지산역','범물역','용지역'
    ],
}

def geocode_keyword(keyword):
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    params = urllib.parse.urlencode({'query': keyword})
    req = urllib.request.Request(f"{url}?{params}")
    req.add_header('Authorization', f'KakaoAK {KAKAO_REST_API_KEY}')
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            d = json.loads(response.read().decode('utf-8'))
            if d.get('documents'):
                doc = d['documents'][0]
                return float(doc['y']), float(doc['x']), doc.get('address_name','')
    except Exception as e:
        print(f"  오류: {e}")
    return None, None, ''

def main():
    path = '/Users/kimminwoo/Documents/업무/00.개발/1.focus/data.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 원본 집계 항목 추출
    originals = {}
    for d in data:
        if d.get('name') in LINES:
            originals[d['name']] = d

    # 집계 항목 제거
    data = [d for d in data if d.get('name') not in LINES]

    new_items = []
    failed = []

    for line_name, stations in LINES.items():
        original = originals.get(line_name)
        if not original:
            print(f"⚠️ {line_name} 원본 없음")
            continue

        total_qty = original.get('quantity', 0) or 0
        n = len(stations)
        base = total_qty // n
        rem = total_qty % n
        print(f"\n=== {line_name}: {total_qty}개 → {n}역 (역당 {base}개, 앞 {rem}역은 +1) ===")

        for i, station in enumerate(stations):
            qty = base + (1 if i < rem else 0)
            keyword = f"대구 {station}"
            lat, lng, addr = geocode_keyword(keyword)
            if not lat:
                # 호선 정보 추가하여 재시도
                line_no = line_name.split('_')[1]
                lat, lng, addr = geocode_keyword(f"대구 도시철도 {line_no} {station}")

            if not lat:
                print(f"  ❌ {station}")
                failed.append(f"{line_name} - {station}")
                continue

            item = copy.deepcopy(original)
            item['name'] = f"{line_name}_{station}"
            item['address'] = addr or f"대구광역시 {station}"
            item['quantity'] = qty
            item['lat'] = lat
            item['lng'] = lng
            new_items.append(item)
            print(f"  ✓ {station} ({qty}개) {lat:.4f},{lng:.4f}")
            time.sleep(0.05)

    data.extend(new_items)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== 결과 ===")
    print(f"신규 역 항목: {len(new_items)}개")
    print(f"실패: {len(failed)}개")
    for x in failed:
        print(f"  - {x}")
    print(f"\n총 data.json: {len(data)}개")

if __name__ == '__main__':
    main()
