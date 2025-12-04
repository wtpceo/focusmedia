#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주소를 좌표로 변환하는 스크립트 (네이버 Geocoding API 사용)
한 번만 실행하면 됩니다!
"""

import json
import urllib.request
import urllib.parse
import time
import ssl

# 네이버 클라우드 플랫폼 API 키
CLIENT_ID = '1eemrq5iim'
CLIENT_SECRET = 'cS4VXiy0PIzqqBJura7pgRigj2jUO4vF09hfY36n'

# SSL 인증서 검증 비활성화 (필요시)
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
        pass

    return None, None

def main():
    # 데이터 로드
    input_file = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus/data.json'
    output_file = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus/data.json'

    with open(input_file, 'r', encoding='utf-8') as f:
        locations = json.load(f)

    total = len(locations)
    success = 0
    already = 0

    print(f"총 {total}개 데이터 처리 시작...")

    for i, loc in enumerate(locations):
        # 이미 좌표가 있으면 스킵
        if loc.get('lat') and loc.get('lng'):
            already += 1
            success += 1
            continue

        address = loc.get('address', '')
        if not address:
            continue

        lat, lng = geocode(address)

        if lat and lng:
            loc['lat'] = lat
            loc['lng'] = lng
            success += 1

        # 진행률 출력
        if (i + 1) % 100 == 0:
            print(f"진행: {i + 1}/{total} (성공: {success}, 기존: {already})")

        # API 제한 방지 (초당 10회 제한)
        time.sleep(0.12)

    # 결과 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(locations, f, ensure_ascii=False, indent=2)

    print(f"\n완료!")
    print(f"- 기존 좌표: {already}개")
    print(f"- 새로 변환: {success - already}개")
    print(f"- 총 성공: {success}/{total}개")
    print(f"저장 위치: {output_file}")

if __name__ == '__main__':
    main()
