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

def get_col(row, *keywords):
    """컬럼명에서 공백·줄바꿈 제거 후 모든 keyword를 포함하는 컬럼 값 반환.
    엑셀 회차마다 컬럼명 공백/줄바꿈 위치가 바뀌어도 안정적으로 매칭."""
    for col in row.index:
        norm = str(col).replace(' ', '').replace('\n', '')
        if all(k in norm for k in keywords):
            return row[col]
    return ''

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, '엘리베이터TV 설치리스트(외부용)_260907.xlsx')
    output_file = os.path.join(base_dir, 'data_focusmedia.json')

    # 엑셀 파일 읽기 (헤더는 3행, 0-indexed로 3)
    # 회차에 따라 시트가 여러 개 오므로(260907: '서울생활권 동네상권정보'+'신규아파트')
    # 첫 시트에 의존하지 않고 '단지명' 컬럼이 있는 시트를 고른다
    xls = pd.ExcelFile(input_file)
    candidates = []
    for name in xls.sheet_names:
        d = pd.read_excel(input_file, sheet_name=name, header=3)
        if '단지명' in d.columns:
            candidates.append((name, d))
    if not candidates:
        raise SystemExit(f"'단지명' 컬럼이 있는 시트를 찾지 못함: {xls.sheet_names}")
    # 후보가 여럿이면 행이 가장 많은 시트를 쓴다 (일부만 담긴 시트를 조용히 집는 사고 방지)
    candidates.sort(key=lambda t: len(t[1]), reverse=True)
    sheet, df = candidates[0]
    if len(candidates) > 1:
        print(f"⚠️ '단지명' 시트가 여러 개: {[(n, len(d)) for n, d in candidates]} → 최다 행 시트 '{sheet}' 사용")
    print(f"사용 시트: {sheet} (전체 {xls.sheet_names})")

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

        # 영업제한 업종 정보 (컬럼명 공백·줄바꿈 위치가 회차마다 바뀌어 정규화 매칭)
        restriction1_type = clean_text(get_col(row, '구좌1', '영업제한업종'))
        restriction1_date = clean_date(get_col(row, '구좌1', '영업제한기한'))
        restriction2_type = clean_text(get_col(row, '구좌2', '영업제한업종'))
        restriction2_date = clean_date(get_col(row, '구좌2', '영업제한기한'))

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
