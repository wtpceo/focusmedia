#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geocode 없는 항목들의 좌표를 가져오는 스크립트
주소를 여러 방식으로 시도
"""

import json
import urllib.request
import urllib.parse
import time
import ssl
import re

# 네이버 클라우드 플랫폼 API 키
CLIENT_ID = '1eemrq5iim'
CLIENT_SECRET = 'cS4VXiy0PIzqqBJura7pgRigj2jUO4vF09hfY36n'

# SSL 인증서 검증 비활성화
ssl._create_default_https_context = ssl._create_unverified_context

def geocode(address):
    """주소를 좌표로 변환"""
    url = 'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode'
    params = urllib.parse.urlencode({'query': address})
    full_url = f"{url}?{params}"

    req = urllib.request.Request(full_url)
    req.add_header('X-NCP-APIGW-API-KEY-ID', CLIENT_ID)
    req.add_header('X-NCP-APIGW-API-KEY', CLIENT_SECRET)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data.get('addresses') and len(data['addresses']) > 0:
                addr = data['addresses'][0]
                return float(addr['y']), float(addr['x'])  # lat, lng
    except Exception as e:
        print(f"  API 오류: {e}")

    return None, None

def clean_address(address):
    """주소에서 괄호 부분 제거"""
    # (동명, 건물명) 형태 제거
    cleaned = re.sub(r'\s*\([^)]+\)\s*$', '', address)
    return cleaned.strip()

def try_geocode(address, name):
    """여러 방식으로 geocode 시도"""
    attempts = []

    # 1. 원본 주소
    attempts.append(address)

    # 2. 괄호 제거
    cleaned = clean_address(address)
    if cleaned != address:
        attempts.append(cleaned)

    # 3. 건물명으로 검색
    attempts.append(name)

    # 4. 주소 + 건물명
    attempts.append(f"{cleaned} {name}")

    for i, addr in enumerate(attempts):
        print(f"  시도 {i+1}: {addr[:50]}...")
        lat, lng = geocode(addr)
        if lat and lng:
            print(f"  성공! ({lat}, {lng})")
            return lat, lng
        time.sleep(0.15)

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
            failed.append(item['name'])

    # 저장
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n\n=== 결과 ===")
    print(f"성공: {success}개")
    print(f"실패: {len(failed)}개")

    if failed:
        print("\n실패한 항목:")
        for name in failed:
            print(f"  - {name}")

if __name__ == '__main__':
    main()
