#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 데이터를 병합하는 스크립트 (260223 버전)
- 포커스미디어 (data_focusmedia.json)
- 타운보드S 가동 (엑셀 직접 변환)
- 타운보드L 가동 (엑셀 직접 변환)
- 타운보드 만첨 (기존 data.json에서 보존)
- HTPOST (data_htpost.json)
- MEDIA MEET (data_mediameet.json)
- 기존 좌표 정보 유지
"""

import json
import os
import pandas as pd
from collections import Counter

BASE_DIR = '/Users/kimminwoo/Documents/업무/00.개발/1.focus'

def clean_number(value):
    if pd.isna(value):
        return 0
    try:
        return int(float(value))
    except:
        return 0

def clean_text(value):
    if pd.isna(value):
        return ''
    return str(value).strip()

CITY_MAP = {
    '서울': '서울특별시', '부산': '부산광역시', '대구': '대구광역시',
    '인천': '인천광역시', '광주': '광주광역시', '대전': '대전광역시',
    '울산': '울산광역시', '세종': '세종특별자치시', '경기': '경기도',
    '강원': '강원특별자치도', '충북': '충청북도', '충남': '충청남도',
    '전북': '전라북도', '전남': '전라남도', '경북': '경상북도',
    '경남': '경상남도', '제주': '제주특별자치도',
}

def convert_townboard_sheet(excel_file, sheet_name, media_filter, type_name):
    """타운보드 가동리스트 엑셀 시트 → 리스트 변환"""
    print(f"\n=== {type_name} 변환 중: {sheet_name} ===")

    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=5)

    # 매체분류 필터링
    df = df[df['매체분류'] == media_filter].copy()
    df = df.dropna(subset=['아파트명'])
    print(f"  유효 데이터: {len(df)}개")

    data = []
    for idx, row in df.iterrows():
        name = clean_text(row['아파트명'])
        address = clean_text(row.get('주소', ''))
        if not name or not address:
            continue

        region1 = clean_text(row.get('지역1', ''))
        region2 = clean_text(row.get('지역2', ''))
        region3 = clean_text(row.get('지역3(법정)', ''))
        city = CITY_MAP.get(region1, region1)

        item = {
            'name': name,
            'code': '',
            'city': city,
            'gu': region2,
            'dong': region3,
            'address': address,
            'building_type': clean_text(row.get('구분', '아파트')),
            'year': clean_number(row.get('입주년도', 0)) if not pd.isna(row.get('입주년도')) else None,
            'floors': None,
            'area': clean_text(row.get('평형', '')),
            'households': clean_number(row.get('세대수', 0)) if not pd.isna(row.get('세대수')) else None,
            'population': None,
            'grade': None,
            'quantity': clean_number(row.get('가동수량', 0)),
            'unit_price': None,
            'price_4w': None,
            'install_date': '',
            'type': type_name
        }
        data.append(item)

    print(f"  변환 완료: {len(data)}개")
    return data


def main():
    # 1. 기존 data.json에서 좌표 정보 추출
    old_data_file = os.path.join(BASE_DIR, 'data.json')
    with open(old_data_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)

    # 좌표 정보 매핑 (이름 -> 좌표)
    coords_map = {}
    for item in old_data:
        if item.get('lat') and item.get('lng'):
            coords_map[item['name']] = {'lat': item['lat'], 'lng': item['lng']}

    print(f"기존 좌표 정보: {len(coords_map)}개")

    # 기존 데이터 타입 통계
    type_counts = Counter(item.get('type') for item in old_data)
    print(f"\n기존 data.json 타입별:")
    for t, c in type_counts.most_common():
        print(f"  - {t}: {c}개")

    # 2. 새 포커스미디어 데이터 로드
    new_fm_file = os.path.join(BASE_DIR, 'data_focusmedia.json')
    with open(new_fm_file, 'r', encoding='utf-8') as f:
        new_fm_data = json.load(f)
    print(f"\n새 포커스미디어 데이터: {len(new_fm_data)}개")

    # 3. 타운보드 엑셀에서 직접 변환
    townboard_file = os.path.join(BASE_DIR, '타운보드 가동리스트(로컬상품)_260223.xlsx')

    # 타운보드S (가동)
    new_tb_s_data = convert_townboard_sheet(
        townboard_file, '타운보드S(전국 50,000대)', '타운보드', 'townboard_op')

    # 타운보드L (가동)
    new_tb_l_data = convert_townboard_sheet(
        townboard_file, '타운보드L(전국 10,000대)', '타운보드L', 'townboard_l')

    # 4. 기존 townboard (만첨) 데이터 유지
    old_townboard_mancheom = [item for item in old_data if item.get('type') == 'townboard']
    print(f"\n기존 타운보드(만첨) 데이터 유지: {len(old_townboard_mancheom)}개")

    # 5. HTPOST 데이터 로드
    htpost_file = os.path.join(BASE_DIR, 'data_htpost.json')
    with open(htpost_file, 'r', encoding='utf-8') as f:
        htpost_data = json.load(f)
    print(f"HTPOST 데이터: {len(htpost_data)}개")

    # 6. MEDIA MEET 데이터 로드
    mediameet_file = os.path.join(BASE_DIR, 'data_mediameet.json')
    with open(mediameet_file, 'r', encoding='utf-8') as f:
        mediameet_data = json.load(f)
    print(f"MEDIA MEET 데이터: {len(mediameet_data)}개")

    # 7. 모든 데이터에 좌표 적용
    all_items = (new_fm_data + new_tb_s_data + new_tb_l_data +
                 old_townboard_mancheom + htpost_data + mediameet_data)
    coords_applied = 0
    for item in all_items:
        if not item.get('lat') and item['name'] in coords_map:
            item['lat'] = coords_map[item['name']]['lat']
            item['lng'] = coords_map[item['name']]['lng']
            coords_applied += 1

    print(f"\n좌표 새로 적용: {coords_applied}개")

    # 8. 전체 병합
    all_data = all_items
    print(f"\n=== 최종 데이터 ===")
    final_counts = Counter(item.get('type') for item in all_data)
    for t, c in final_counts.most_common():
        print(f"  - {t}: {c}개")
    print(f"  총합: {len(all_data)}개")

    # 9. 저장
    output_file = os.path.join(BASE_DIR, 'data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {output_file}")

    # 10. 영업제한 업종 통계
    with_restriction = [d for d in all_data if d.get('restriction1_type') or d.get('restriction2_type')]
    print(f"영업제한 업종 있는 데이터: {len(with_restriction)}개")

    # 좌표 없는 데이터 확인
    no_coords = [d for d in all_data if not d.get('lat')]
    print(f"좌표 없는 데이터: {len(no_coords)}개")
    if no_coords:
        no_coords_by_type = Counter(d.get('type') for d in no_coords)
        print("좌표 없는 데이터 타입별:")
        for t, c in no_coords_by_type.most_common():
            print(f"  [{t}] {c}개")
        print("좌표 없는 데이터 샘플 (처음 5개):")
        for item in no_coords[:5]:
            print(f"  [{item.get('type')}] {item['name']} - {item.get('address', '')}")

if __name__ == '__main__':
    main()
