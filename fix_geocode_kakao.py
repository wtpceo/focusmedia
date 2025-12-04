#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카카오 API를 사용하여 geocode 없는 항목들의 좌표를 가져오는 스크립트
"""

import json
import urllib.request
import urllib.parse
import time
import ssl
import re

# 카카오 REST API 키
KAKAO_REST_API_KEY = 'd82eba93079458f667f074cb979a694d'

# SSL 인증서 검증 비활성화
ssl._create_default_https_context = ssl._create_unverified_context

def geocode_kakao(address):
    """카카오 API로 주소를 좌표로 변환"""
    url = 'https://dapi.kakao.com/v2/local/search/address.json'
    params = urllib.parse.urlencode({'query': address})
    full_url = f"{url}?{params}"

    req = urllib.request.Request(full_url)
    req.add_header('Authorization', f'KakaoAK {KAKAO_REST_API_KEY}')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data.get('documents') and len(data['documents']) > 0:
                doc = data['documents'][0]
                return float(doc['y']), float(doc['x'])  # lat, lng
    except Exception as e:
        print(f"  API 오류: {e}")

    return None, None

def geocode_kakao_keyword(keyword):
    """카카오 키워드 검색 API로 좌표 변환"""
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json'
    params = urllib.parse.urlencode({'query': keyword})
    full_url = f"{url}?{params}"

    req = urllib.request.Request(full_url)
    req.add_header('Authorization', f'KakaoAK {KAKAO_REST_API_KEY}')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data.get('documents') and len(data['documents']) > 0:
                doc = data['documents'][0]
                return float(doc['y']), float(doc['x'])  # lat, lng
    except Exception as e:
        print(f"  키워드 API 오류: {e}")

    return None, None

def clean_address(address):
    """주소에서 괄호 부분 제거"""
    cleaned = re.sub(r'\s*\([^)]+\)\s*$', '', address)
    return cleaned.strip()

def try_geocode(address, name):
    """여러 방식으로 geocode 시도"""
    # 1. 괄호 제거한 주소로 시도
    cleaned = clean_address(address)
    print(f"  시도 1 (주소): {cleaned[:50]}...")
    lat, lng = geocode_kakao(cleaned)
    if lat and lng:
        print(f"  성공! ({lat}, {lng})")
        return lat, lng
    time.sleep(0.1)

    # 2. 원본 주소로 시도
    if cleaned != address:
        print(f"  시도 2 (원본): {address[:50]}...")
        lat, lng = geocode_kakao(address)
        if lat and lng:
            print(f"  성공! ({lat}, {lng})")
            return lat, lng
        time.sleep(0.1)

    # 3. 키워드 검색으로 시도 (건물명)
    print(f"  시도 3 (키워드): {name}...")
    lat, lng = geocode_kakao_keyword(name)
    if lat and lng:
        print(f"  성공! ({lat}, {lng})")
        return lat, lng
    time.sleep(0.1)

    # 4. 주소 + 건물명으로 키워드 검색
    keyword = f"{cleaned.split()[0]} {cleaned.split()[1] if len(cleaned.split()) > 1 else ''} {name}"
    print(f"  시도 4 (조합): {keyword[:50]}...")
    lat, lng = geocode_kakao_keyword(keyword)
    if lat and lng:
        print(f"  성공! ({lat}, {lng})")
        return lat, lng

    return None, None

def main():
    input_file = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus/data.json'

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # geocode 없는 항목 찾기
    no_geocode = [item for item in data if 'lat' not in item or not item.get('lat')]
    print(f"geocode 없는 항목: {len(no_geocode)}개\n")

    success = 0
    failed = []

    for item in no_geocode:
        print(f"\n처리 중: {item['name']}")
        lat, lng = try_geocode(item['address'], item['name'])

        if lat and lng:
            item['lat'] = lat
            item['lng'] = lng
            success += 1
        else:
            print(f"  실패!")
            failed.append({'name': item['name'], 'address': item['address']})

    # 저장
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n\n=== 결과 ===")
    print(f"성공: {success}개")
    print(f"실패: {len(failed)}개")

    if failed:
        print("\n실패한 항목:")
        for item in failed:
            print(f"  - {item['name']}: {item['address']}")

if __name__ == '__main__':
    main()
