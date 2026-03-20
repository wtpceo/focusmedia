#!/usr/bin/env python3
"""
MEDIA MEET 설치리스트 엑셀 → JSON 변환 스크립트
- 입력: MEDIA MEET 설치리스트_251121.xlsx (두 번째 탭: 설치 리스트)
- 출력: data_mediameet.json
- 단가: 15초 단가만 사용 (나머지 광고료 단가 제외)
"""

import pandas as pd
import json

# 설정
INPUT_FILE = 'MEDIA MEET 설치리스트_260317.xlsx'
OUTPUT_FILE = 'data_mediameet.json'
SHEET_NAME = '설치 리스트'
HEADER_ROW = 4  # 0-indexed (5행)

def convert_value(val, dtype='str'):
    """값 변환 헬퍼"""
    if pd.isna(val):
        return None if dtype != 'str' else ''
    if dtype == 'int':
        try:
            return int(float(val))
        except:
            return None
    if dtype == 'float':
        try:
            return float(val)
        except:
            return None
    return str(val).strip()

def main():
    print(f"입력 파일: {INPUT_FILE}")
    print(f"시트: {SHEET_NAME}")

    # 엑셀 읽기
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=HEADER_ROW)
    print(f"총 행 수: {len(df)}")

    # 아파트명이 있는 행만 필터링
    df = df.dropna(subset=['아파트명'])
    print(f"유효 데이터: {len(df)}개")

    # JSON 데이터 생성
    data = []
    for idx, row in df.iterrows():
        item = {
            'name': convert_value(row['아파트명']),
            'city': convert_value(row['지역1']),
            'gu': convert_value(row['지역2']),
            'dong': convert_value(row.get('지역3', '')),
            'address': convert_value(row['주 소']),
            'building_type': convert_value(row['구분']),
            'year': convert_value(row.get('준공년도'), 'int'),
            'area_min': convert_value(row.get('최소평형'), 'int'),
            'area_max': convert_value(row.get('최대평형'), 'int'),
            'households': convert_value(row.get('세대수'), 'int'),
            'quantity_interior': convert_value(row.get('엘리베이터 내부'), 'int'),
            'quantity_waiting': convert_value(row.get('엘리베이터 대기공간'), 'int'),
            'quantity': convert_value(row.get('합계(내부+대기공간)'), 'int'),
            'unit_price': convert_value(row.get('15초 단가'), 'int'),  # 15초 단가만!
            'type': 'mediameet',
            'lat': None,
            'lng': None
        }

        # 이름이 비어있으면 스킵
        if not item['name']:
            continue

        data.append(item)

    print(f"변환 완료: {len(data)}개")

    # JSON 저장
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {OUTPUT_FILE}")

    # 샘플 출력
    print("\n=== 샘플 데이터 (처음 3개) ===")
    for item in data[:3]:
        print(f"  {item['name']} ({item['city']} {item['gu']}) - {item['quantity']}대, 15초단가: {item['unit_price']}원")

if __name__ == '__main__':
    main()
