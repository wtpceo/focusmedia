#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 좌표를 유지하면서 새 필드 추가
"""

import csv
import json

def clean_number(value):
    if not value:
        return 0
    try:
        return int(value.replace(',', '').strip())
    except:
        return 0

def clean_text(value):
    if not value:
        return ''
    return value.strip()

def main():
    csv_file = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages/03.focus/엘리베이터TV 설치리스트(외부용)_251114.csv'
    existing_json = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages/03.focus/data.json'
    output_file = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages/03.focus/data_new.json'

    # 기존 JSON 로드 (좌표 정보 포함)
    with open(existing_json, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)

    # 기존 좌표 맵 생성 (이름 기준)
    coords_map = {}
    for item in existing_data:
        if item.get('lat') and item.get('lng'):
            coords_map[item['name']] = {'lat': item['lat'], 'lng': item['lng']}

    print(f"기존 좌표 {len(coords_map)}개 로드")

    # CSV 읽기
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # 헤더 찾기
    header_row = None
    for i, row in enumerate(rows):
        if '단지명' in row:
            header_row = i
            break

    headers = rows[header_row]

    # 컬럼 인덱스
    col = {}
    for i, h in enumerate(headers):
        h = h.strip().replace('\n', ' ')
        if '단지명' in h: col['name'] = i
        elif '단지코드' in h: col['code'] = i
        elif h == '도시': col['city'] = i
        elif h == '구': col['gu'] = i
        elif '동(법정동)' in h: col['dong'] = i
        elif '주소(도로명)' in h: col['address'] = i
        elif '주소(지번)' in h: col['address_jibun'] = i
        elif '건물유형' in h: col['building_type'] = i
        elif '준공연도' in h: col['year'] = i
        elif '건물층수' in h: col['floors'] = i
        elif '기준평형' in h: col['area'] = i
        elif '총 세대수' in h: col['households'] = i
        elif '총 인구수' in h: col['population'] = i
        elif '판매등급' in h: col['grade'] = i
        elif '판매수량' in h: col['quantity'] = i
        elif '대당단가' in h: col['unit_price'] = i
        elif '4주 금액' in h: col['price_4w'] = i
        elif '최초 설치일자' in h: col['install_date'] = i

    print(f"컬럼: {col}")

    locations = []
    for row in rows[header_row + 1:]:
        if len(row) <= col.get('name', 5):
            continue

        name = clean_text(row[col.get('name', 5)])
        if not name:
            continue

        address = clean_text(row[col.get('address', 11)])
        if not address:
            address = clean_text(row[col.get('address_jibun', 10)])
        if not address:
            continue

        location = {
            'name': name,
            'code': clean_text(row[col.get('code', 6)]),
            'city': clean_text(row[col.get('city', 7)]),
            'gu': clean_text(row[col.get('gu', 8)]),
            'dong': clean_text(row[col.get('dong', 9)]),
            'address': address,
            'building_type': clean_text(row[col.get('building_type', 12)]),
            'year': clean_number(row[col.get('year', 13)]),
            'floors': clean_number(row[col.get('floors', 14)]),
            'area': clean_number(row[col.get('area', 15)]),
            'households': clean_number(row[col.get('households', 16)]),
            'population': clean_number(row[col.get('population', 17)]),
            'grade': clean_text(row[col.get('grade', 19)]),
            'quantity': clean_number(row[col.get('quantity', 20)]),
            'unit_price': clean_number(row[col.get('unit_price', 21)]),
            'price_4w': clean_number(row[col.get('price_4w', 22)]),
            'install_date': clean_text(row[col.get('install_date', 18)])
        }

        # 기존 좌표 적용
        if name in coords_map:
            location['lat'] = coords_map[name]['lat']
            location['lng'] = coords_map[name]['lng']

        locations.append(location)

    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)

    with_coords = len([l for l in locations if l.get('lat')])
    print(f"총 {len(locations)}개, 좌표 포함 {with_coords}개")
    print(f"저장: {output_file}")

    if locations:
        print("\n샘플:")
        print(json.dumps(locations[0], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
