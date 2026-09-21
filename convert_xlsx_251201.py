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
    input_file = os.path.join(base_dir, '엘리베이터TV 설치리스트(외부용)_260921.xlsx')
    output_file = os.path.join(base_dir, 'data_focusmedia.json')

    # 엑셀 파일 읽기
    # 회차에 따라 시트가 여러 개 오고(260907: '서울생활권 동네상권정보'+'신규아파트')
    # 헤더 행 위치도 오간다(260907: 4행=header 3 / 260921: 3행=header 2)
    # → 시트·헤더행을 모두 탐색해 '단지명' 컬럼이 잡히는 조합을 고른다
    # '단지명' 하나만 보면, 병합된 타이틀 띠에 그 글자가 남아 있을 때 한 행 위를 헤더로
    # 잘못 잡아 전 컬럼이 밀린 채 조용히 통과한다 → 필수 컬럼 3종 동시 충족으로 조인다
    REQUIRED = {'단지명', ' 주소(도로명)', '4주 금액'}
    xls = pd.ExcelFile(input_file)
    candidates = []
    for name in xls.sheet_names:
        for hdr in (2, 3, 4):
            d = pd.read_excel(input_file, sheet_name=name, header=hdr)
            if REQUIRED.issubset(set(d.columns)):
                candidates.append((name, hdr, d))
                break
    if not candidates:
        raise SystemExit(f"필수 컬럼 {REQUIRED}이 모두 있는 시트를 찾지 못함: {xls.sheet_names}")
    # 후보가 여럿이면 실데이터('단지명'이 채워진) 행이 가장 많은 시트를 쓴다.
    # 헤더행이 시트마다 다를 수 있어 len(df)로는 비교가 안 된다(헤더가 위면 그만큼 행이 늘어남)
    def real_rows(d):
        return int(d['단지명'].notna().sum())
    candidates.sort(key=lambda t: real_rows(t[2]), reverse=True)
    sheet, header_row, df = candidates[0]
    if len(candidates) > 1:
        print(f"⚠️ 후보 시트가 여러 개: {[(n, h, real_rows(d)) for n, h, d in candidates]} → 최다 실데이터 시트 '{sheet}' 사용")
        # 행수가 같으면 정렬 안정성에 기대 첫 시트가 뽑힌다 — 내용까지 같은지 확인하고,
        # 다르면 어느 쪽을 써야 할지 사람이 판단해야 하므로 크게 경고한다
        base = set(df['단지명'].dropna())
        for n, h, d in candidates[1:]:
            if real_rows(d) != real_rows(df):
                continue
            other = set(d['단지명'].dropna())
            if base != other:
                print(f"🚨 행수가 같은 시트 '{n}'의 단지명 집합이 '{sheet}'와 다름 "
                      f"(only-{sheet} {len(base - other)}건 / only-{n} {len(other - base)}건) "
                      f"— 어느 시트가 맞는지 확인 필요")
            else:
                print(f"   (참고) '{n}'은 '{sheet}'와 단지명 집합 동일 = 정렬만 다른 같은 데이터")
    print(f"사용 시트: {sheet} (헤더행 {header_row}, 실데이터 {real_rows(df)}행, 전체 {xls.sheet_names})")

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
