#!/usr/bin/env python3
"""
HTPOST 가동리스트 엑셀 → JSON 변환 스크립트
- 입력: HTPOST 가동리스트_로컬파트너사_260121.xlsx (HT_로컬파트너사 시트)
- 출력: data_htpost.json
"""

import pandas as pd
import json

INPUT_FILE = '[현대에이치티] 단지별 로컬광고단가.xlsx'
OUTPUT_FILE = 'data_htpost.json'
SHEET_NAME = '가격정책'
HEADER_ROW = 2  # 0-indexed (3행)

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

def main():
    print(f"입력 파일: {INPUT_FILE}")
    print(f"시트: {SHEET_NAME}")

    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME, header=HEADER_ROW)
    print(f"총 행 수: {len(df)}")

    # 현장명이 있는 행만 필터링, 헤더 반복행 제거
    df = df.dropna(subset=['현장명'])
    df = df[df['지역'] != '구분']  # 머지 헤더 반복행 스킵
    print(f"유효 데이터: {len(df)}개")

    data = []
    for idx, row in df.iterrows():
        name = clean_text(row['현장명'])
        if not name:
            continue

        item = {
            'name': name,
            'city': clean_text(row.get('지역', '')),
            'gu': '',
            'dong': '',
            'address': clean_text(row.get('주소', '')),
            'building_type': '',
            'households': clean_number(row.get('세대수', 0)),
            'quantity': clean_number(row.get('실제수량', 0)),
            'price_4w': clean_number(row.get('Unnamed: 9', 0)),  # 제안가(월) - 머지 헤더
            'type': 'htpost',
            'lat': None,
            'lng': None
        }
        data.append(item)

    print(f"변환 완료: {len(data)}개")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {OUTPUT_FILE}")

    print("\n=== 샘플 데이터 (처음 3개) ===")
    for item in data[:3]:
        print(f"  {item['name']} ({item['city']}) - {item['quantity']}대, 월금액: {item['price_4w']}원")

if __name__ == '__main__':
    main()
