#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 데이터를 병합하는 스크립트 (260309 버전)
- 포커스미디어 (data_focusmedia.json)
- 타운보드S 가동 (엑셀 직접 변환)
- 타운보드L 가동 (엑셀 직접 변환)
- 타운보드 만첨 (엑셀 직접 변환)
- HTPOST 영상 + 전단지 (엑셀 직접 변환, 두 타입으로 분리)
- MEDIA MEET (data_mediameet.json)
- 기존 좌표 정보 유지
"""

import json
import os
import pandas as pd
import re
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

    # 매체분류 필터링 (문자열 또는 리스트)
    if isinstance(media_filter, list):
        df = df[df['매체분류'].isin(media_filter)].copy()
    else:
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


def convert_townboard_mancheom(excel_file, sheet_name='만첨리스트'):
    """타운보드 만첨 엑셀 → 리스트 변환"""
    print(f"\n=== 타운보드(만첨) 변환 중: {sheet_name} ===")
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=6)
    df = df.dropna(subset=['단지명'])
    # 문자열인 단지명만 유지 (총합계 등 제거)
    df = df[df['단지명'].apply(lambda x: isinstance(x, str) and len(str(x).strip()) > 0)]
    print(f"  유효 데이터: {len(df)}개")

    data = []
    for idx, row in df.iterrows():
        name = clean_text(row['단지명'])
        if not name:
            continue

        region1 = clean_text(row.get('지역1', ''))
        region2 = clean_text(row.get('지역2', ''))
        region3 = clean_text(row.get('지역3(법정)', ''))
        city = CITY_MAP.get(region1, region1)

        address_parts = [p for p in [city, region2, region3] if p]
        address = ' '.join(address_parts)

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
            'type': 'townboard'
        }
        data.append(item)

    print(f"  변환 완료: {len(data)}개")
    return data


SIDO_PREFIX = re.compile(
    r'^(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)_')


def strip_sido_prefix(name):
    """HTPOST 현장명에 붙는 공급사 내부 시/도 접두사 제거.
    ('경기_평촌센텀퍼스트' → '평촌센텀퍼스트')
    로컬파트너사 파일뿐 아니라 로컬광고단가 통합파일에도 섞여 들어오므로
    HTPOST 3경로(영상 통합·영상 파트너사·전단지) 전부에 적용한다.
    표기를 맞춰야 좌표 승계와 영상↔전단지 매칭이 어긋나지 않는다."""
    return SIDO_PREFIX.sub('', name)


# HTPOST 주소에서 구·동을 뽑는다 — 원본 단가표엔 지역 컬럼이 시/도밖에 없어
# gu가 비면 index.html의 지역 필터(gu 기준)에서 HTPOST 전건이 탈락한다.
# 표기는 MEDIA MEET 계열에 맞춘다(도 = 시 단위 '고양시', 광역시 = 구 단위 '노원구').
# 포커스미디어·타운보드처럼 '고양시 일산동구'로 쪼개지 않는 이유는
# HTPOST의 city가 '경기'·'서울' 짧은 표기여서 MM과 같은 칩에 붙어야 하기 때문이다.
# 광역시·특별시·특별자치시는 '서울시'처럼 '시'를 붙인 약칭이 쓰인다.
_METRO = ('서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종')
# 도(道)는 '경기도'처럼 '도'를 붙인다. '경기 …'처럼 접미 없이 오는 표기도 있다.
_PROVINCE = ('경기', '강원', '충북', '충청북도', '충남', '충청남도',
             '전북', '전북특별자치도', '전남', '전라남도',
             '경북', '경상북도', '경남', '경상남도', '제주')
_SIDO_HEAD = _METRO + _PROVINCE
_ADMIN_TAIL = ('특별시', '광역시', '특별자치시', '특별자치도')


def _is_sido_token(tok, next_tok=''):
    """주소 첫 토큰이 시/도 표기인가.

    '광주시'·'제주시'는 광역시 약칭일 수도, 기초 지자체(경기 광주시·제주시)일 수도 있다.
    뒤 토큰이 '구'로 끝나면 광역시 약칭으로, 그렇지 않으면 기초 시로 본다
    ('광주시 북구 …' = 광주광역시 / '광주시 태전동 …' = 경기 광주시).
    이 구분이 없으면 후자에서 시 이름이 버려지고 동 이름이 gu로 올라간다."""
    if tok in _SIDO_HEAD:
        return True
    for h in _SIDO_HEAD:
        if tok.startswith(h) and tok.endswith(_ADMIN_TAIL):
            return True
    for h in _PROVINCE:
        if tok == h + '도':
            return True
    for h in _METRO:
        if tok == h + '시':
            return bool(next_tok) and next_tok.endswith('구')
    return False


def _strip_sido_prefix_token(tok):
    """'경기도고양시'처럼 시/도를 붙여 쓴 토큰에서 시/도 부분을 떼어낸다.

    남는 조각이 두 글자 이상이고 행정구역 접미로 끝날 때만 떼어낸다 —
    그러지 않으면 '광주시'에서 '광주'를 떼어 '시' 한 글자가 gu로 올라간다."""
    for h in sorted(_SIDO_HEAD, key=len, reverse=True):
        for pre in (h + '특별자치도', h + '특별자치시', h + '특별시', h + '광역시', h + '도', h):
            if not tok.startswith(pre):
                continue
            tail = tok[len(pre):]
            if len(tail) >= 2 and tail.endswith(('시', '군', '구')):
                return tail
    return tok


def split_address_gu_dong(address, city=''):
    """주소 문자열 → (gu, dong). 못 뽑으면 빈 문자열.
    세종은 구가 없어 동을 gu로 쓰고(MM 관행: gu='나성동'),
    동까지 없는 도로명 주소면 '세종시'로 떨어뜨린다(타운보드가 쓰는 표기).

    '시'로 끝나는 토큰을 처음 만나면 채택하므로 도(道)의 자치구
    (수원 영통구·성남 분당구 등)는 'gu=수원시'가 되고 세분 표기는 하지 않는다 —
    타운보드·MM이 모두 시 단위 단일 토큰을 쓰기 때문에 맞춘 설계상 한계다."""
    address = (address or '').strip()
    toks = address.split()
    if toks:
        skip_first = _is_sido_token(toks[0], toks[1] if len(toks) > 1 else '')
        rest = toks[1:] if skip_first else toks
        # 붙여 쓴 시/도 접두사 제거 ('경기도고양시' → '고양시')
        rest = [_strip_sido_prefix_token(t) for t in rest]
        rest = [t for t in rest if t]
    else:
        rest = []
    gu = ''
    for t in rest:
        if t.endswith(('시', '군', '구')):
            gu = t
            break
    dong = ''
    for t in rest:
        if t.endswith(('동', '읍', '면', '리')) and t != gu:
            dong = t
            break
    if not gu and dong:
        gu = dong          # 세종처럼 시/군/구가 없는 경우
    if not gu and (city or '').startswith('세종'):
        gu = '세종시'       # 동 정보도 없는(또는 주소가 빈) 세종 행
    return gu, dong


def convert_htpost_video_partner(excel_file):
    """HTPOST 가동리스트_로컬파트너사 → 영상(htpost)
    260824 회차: 이번 회차엔 로컬광고단가 통합파일이 오지 않아 영상만 구형식 파일에서 읽음.
    (통합파일이 다시 오면 convert_htpost_new 사용)"""
    print(f"\n=== HTPOST 영상 변환 중 (로컬파트너사 형식) ===")
    df = pd.read_excel(excel_file, sheet_name='HT_로컬파트너사', header=2)
    df = df.dropna(subset=['현장명'])
    df = df[df['지역'] != '구분']  # 반복 헤더 행 제거
    print(f"  유효 데이터: {len(df)}개")

    video_data = []

    for idx, row in df.iterrows():
        name = strip_sido_prefix(clean_text(row['현장명']))
        if not name:
            continue

        price = clean_number(row.get('Unnamed: 7', 0))
        if not price:
            continue  # '불가'·패키지 안내문 등 숫자 아닌 값은 영상 미판매 단지로 간주
                      # (convert_htpost_new와 동일한 정책)

        city = clean_text(row.get('지역', ''))
        address = clean_text(row.get('주소', ''))
        gu, dong = split_address_gu_dong(address, city)

        video_data.append({
            'name': name,
            'city': city,
            'gu': gu,
            'dong': dong,
            'address': address,
            'building_type': '',
            'households': clean_number(row.get('세대수', 0)),
            'quantity': clean_number(row.get('실제수량', 0)),
            'lat': None,
            'lng': None,
            'price_4w': price,
            'type': 'htpost'
        })

    print(f"  영상: {len(video_data)}개")
    return video_data


def convert_htpost_new(excel_file):
    """[현대에이치티] 단지별 로컬광고단가_07월 → 영상(htpost)
    260720 회차부터 영상도 로컬광고단가 통합 파일에서 읽음 ('동영상광고' 제안가(월) 컬럼)"""
    print(f"\n=== HTPOST 영상 변환 중 ===")
    df = pd.read_excel(excel_file, sheet_name='가격정책', header=2)
    df = df.dropna(subset=['현장명'])
    df = df[df['지역'] != '구분']  # 반복 헤더 행 제거
    print(f"  유효 데이터: {len(df)}개")

    video_data = []

    for idx, row in df.iterrows():
        name = strip_sido_prefix(clean_text(row['현장명']))
        if not name:
            continue

        price = clean_number(row.get('동영상광고', 0))
        if not price:
            continue  # '불가' 등 숫자 아닌 값은 영상 미판매 단지로 간주

        city = clean_text(row.get('지역', ''))
        address = clean_text(row.get('주소', ''))
        gu, dong = split_address_gu_dong(address, city)

        video_data.append({
            'name': name,
            'city': city,
            'gu': gu,
            'dong': dong,
            'address': address,
            'building_type': '',
            'households': clean_number(row.get('세대수', 0)),
            'quantity': clean_number(row.get('설치대수', 0)),
            'lat': None,
            'lng': None,
            'price_4w': price,
            'type': 'htpost'
        })

    print(f"  영상: {len(video_data)}개")
    return video_data


def convert_htpost_leaflet(excel_file):
    """[현대에이치티] 단지별 로컬광고단가.xlsx → 전단지(htpost_leaflet)"""
    print(f"\n=== HTPOST 전단지 변환 중 ===")
    df = pd.read_excel(excel_file, sheet_name='가격정책', header=2)
    df = df.dropna(subset=['현장명'])
    df = df[df['지역'] != '구분']  # 반복 헤더 행 제거

    leaflet_data = []

    for idx, row in df.iterrows():
        name = strip_sido_prefix(clean_text(row['현장명']))
        if not name:
            continue

        # 전단지 (게시판 가능 단지만 - '가능', '가능 (보장)' 포함)
        # 07월 파일부터 '동영상광고' 컬럼 신설로 가격 컬럼이 한 칸 밀림 (Unnamed: 11 → 12)
        leaflet_yn = clean_text(row.get('게시판전단광고', ''))
        if leaflet_yn.startswith('가능'):
            price_per_week = clean_number(row.get('Unnamed: 12', 0))
            city = clean_text(row.get('지역', ''))
            address = clean_text(row.get('주소', ''))
            gu, dong = split_address_gu_dong(address, city)

            leaflet_data.append({
                'name': name,
                'city': city,
                'gu': gu,
                'dong': dong,
                'address': address,
                'building_type': '',
                'households': clean_number(row.get('세대수', 0)),
                'quantity': clean_number(row.get('설치대수', 0)),
                'lat': None,
                'lng': None,
                'price_4w': price_per_week * 4,
                'type': 'htpost_leaflet'
            })

    print(f"  전단지: {len(leaflet_data)}개")
    return leaflet_data


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
    townboard_file = os.path.join(BASE_DIR, '타운보드 가동리스트(로컬상품)_261006.xlsx')

    # 타운보드S (가동)
    new_tb_s_data = convert_townboard_sheet(
        townboard_file, '타운보드S(전국 50,000대)', '타운보드', 'townboard_op')

    # 타운보드L (가동) - 시트 내 모든 데이터를 townboard_l로 처리 (리모델링 추가 단지 제외)
    new_tb_l_data = convert_townboard_sheet(
        townboard_file, '타운보드L(전국 10,000대)', ['타운보드', '타운보드L'], 'townboard_l')

    # 4. 타운보드 만첨: S + L 엑셀 직접 변환 (둘 다 'townboard' 타입으로 통합)
    mancheom_s_file = os.path.join(BASE_DIR, '타운보드S 만첨단지리스트_261006(공유).xlsx')
    mancheom_l_file = os.path.join(BASE_DIR, '타운보드L 만첨단지리스트_260928(공유).xlsx')
    new_tb_mancheom_data = (convert_townboard_mancheom(mancheom_s_file, '만첨리스트') +
                            convert_townboard_mancheom(mancheom_l_file, '만첨리스트'))

    # 5. HTPOST 데이터
    #    260901 회차: 로컬광고단가 통합파일(09월)이 다시 와서 영상·전단지 모두 이 파일에서 읽는다.
    #    (통합파일이 안 오는 회차엔 영상만 convert_htpost_video_partner로 로컬파트너사 파일에서 읽음)
    #    261006 회차: 통합파일은 안 오고 로컬파트너사 260930만 와서 영상은 그 파일에서,
    #    전단지는 파트너사 파일에 정보가 없어 09월 통합파일 값 유지.
    htpost_file = os.path.join(BASE_DIR, '[현대에이치티] 단지별 로컬광고단가_09.xlsx')
    htpost_partner_file = os.path.join(BASE_DIR, 'HTPOST 가동리스트_로컬파트너사_260930.xlsx')
    htpost_video_data = convert_htpost_video_partner(htpost_partner_file)
    htpost_leaflet_data = convert_htpost_leaflet(htpost_file)

    # 6. MEDIA MEET 데이터 로드 → 내부/대기공간 분리
    mediameet_file = os.path.join(BASE_DIR, 'data_mediameet.json')
    with open(mediameet_file, 'r', encoding='utf-8') as f:
        mediameet_raw = json.load(f)
    print(f"MEDIA MEET 원본 데이터: {len(mediameet_raw)}개")

    mediameet_data = []
    for item in mediameet_raw:
        qi = item.get('quantity_interior') or 0
        qw = item.get('quantity_waiting') or 0

        if qi > 0:
            interior = {**item, 'type': 'mediameet_interior', 'quantity': qi}
            mediameet_data.append(interior)
        if qw > 0:
            waiting = {**item, 'type': 'mediameet_waiting', 'quantity': qw}
            mediameet_data.append(waiting)
        if qi == 0 and qw == 0:
            # 둘 다 0이면 내부로 처리
            mediameet_data.append({**item, 'type': 'mediameet_interior'})

    mm_interior = sum(1 for d in mediameet_data if d['type'] == 'mediameet_interior')
    mm_waiting = sum(1 for d in mediameet_data if d['type'] == 'mediameet_waiting')
    print(f"MEDIA MEET 분리: 내부 {mm_interior}개, 대기공간 {mm_waiting}개 (합계 {len(mediameet_data)}개)")

    # 7. 모든 데이터에 좌표 적용
    all_items = (new_fm_data + new_tb_s_data + new_tb_l_data +
                 new_tb_mancheom_data + htpost_video_data + htpost_leaflet_data + mediameet_data)
    coords_applied = 0
    for item in all_items:
        if not item.get('lat') and item['name'] in coords_map:
            item['lat'] = coords_map[item['name']]['lat']
            item['lng'] = coords_map[item['name']]['lng']
            coords_applied += 1

    print(f"\n좌표 새로 적용: {coords_applied}개")

    # 9. 전체 병합
    all_data = all_items
    print(f"\n=== 최종 데이터 ===")
    final_counts = Counter(item.get('type') for item in all_data)
    for t, c in final_counts.most_common():
        print(f"  - {t}: {c}개")
    print(f"  총합: {len(all_data)}개")

    # 10. 저장
    output_file = os.path.join(BASE_DIR, 'data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {output_file}")

    # 11. 영업제한 업종 통계
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
