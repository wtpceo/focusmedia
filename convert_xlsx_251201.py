#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
엑셀(xlsx)을 JSON으로 변환하는 스크립트
엘리베이터TV 설치리스트 251201 버전
영업제한 업종 정보 포함
"""

import pandas as pd
import json
import os

def clean_number(value):
    """숫자 값 정리"""
    if pd.isna(value):
        return 0
    try:
        return int(float(value))
    except:
        return 0

def clean_text(value):
    """텍스트 값 정리"""
    if pd.isna(value):
        return ''
    return str(value).strip()

def clean_date(value):
    """날짜 값 정리"""
    if pd.isna(value):
        return ''
    try:
        # pandas Timestamp인 경우
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value).strip()
    except:
        return ''

def main():
    input_file = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus/엘리베이터TV 설치리스트(외부용)_251201.xlsx'
    output_file = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus/data_focusmedia.json'

    # 엑셀 파일 읽기 (헤더는 3행, 0-indexed로 3)
    df = pd.read_excel(input_file, header=3)

    print(f"컬럼 목록: {list(df.columns)}")
    print(f"총 행 수: {len(df)}")

    locations = []

    for idx, row in df.iterrows():
        name = clean_text(row.get('단지명', ''))
        if not name:
            continue

        # 주소 가져오기 (도로명 우선, 없으면 지번)
        address = clean_text(row.get(' 주소(도로명)', ''))
        if not address:
            address = clean_text(row.get(' 주소(지번)', ''))

        if not address:
            continue

        # 영업제한 업종 정보
        restriction1_type = clean_text(row.get('구좌1 영업제한 업종', ''))
        restriction1_date = clean_date(row.get('구좌1 영업제한 기한', ''))
        restriction2_type = clean_text(row.get('구좌2 영업제한 업종', ''))
        restriction2_date = clean_date(row.get('구좌2 영업제한기한', ''))

        # 프리미엄 여부 확인
        premium = clean_text(row.get('프리미엄 여부', ''))
        is_premium = premium.upper() == 'Y' or premium == '예' or premium == '프리미엄'

        location = {
            'name': name,
            'city': clean_text(row.get('도시', '')),
            'gu': clean_text(row.get('구', '')),
            'dong': clean_text(row.get('동(법정동)', '')),
            'address': address,
            'building_type': clean_text(row.get('건물유형', '')),
            'year': clean_number(row.get('준공연도', 0)),
            'floors': clean_number(row.get('건물층수', 0)),
            'area': clean_number(row.get('기준평형', 0)),
            'households': clean_number(row.get('총 세대수', 0)),
            'population': clean_number(row.get('총 인구수', 0)),
            'quantity': clean_number(row.get('판매수량', 0)),
            'unit_price': clean_number(row.get('대당단가', 0)),
            'price_4w': clean_number(row.get('4주 금액', 0)),
            'is_premium': is_premium,
            # 영업제한 업종 정보
            'restriction1_type': restriction1_type,
            'restriction1_date': restriction1_date,
            'restriction2_type': restriction2_type,
            'restriction2_date': restriction2_date,
            # 타입 지정
            'type': 'focusmedia'
        }

        locations.append(location)

    # JSON 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(locations)}개 포커스미디어 데이터 변환 완료")
    print(f"저장 위치: {output_file}")

    # 샘플 출력 (영업제한 업종 있는 데이터)
    sample_with_restriction = [loc for loc in locations if loc['restriction1_type']]
    if sample_with_restriction:
        print("\n=== 영업제한 업종 있는 샘플 데이터 ===")
        print(json.dumps(sample_with_restriction[0], ensure_ascii=False, indent=2))

    if locations:
        print("\n=== 첫 번째 데이터 ===")
        print(json.dumps(locations[0], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
