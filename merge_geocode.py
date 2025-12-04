#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기존 data.json의 geocode 정보를 새 데이터에 매핑하는 스크립트
"""

import json
import subprocess

def main():
    # git에서 기존 data.json 가져오기
    result = subprocess.run(
        ['git', 'show', 'HEAD:data.json'],
        capture_output=True,
        text=True,
        cwd='/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus'
    )

    old_data = json.loads(result.stdout)
    print(f"기존 데이터: {len(old_data)}개")

    # 기존 데이터에서 code -> geocode 매핑 생성
    geocode_map = {}
    for item in old_data:
        if 'lat' in item and 'lng' in item and item.get('lat') and item.get('lng'):
            geocode_map[item['code']] = {
                'lat': item['lat'],
                'lng': item['lng']
            }

    print(f"geocode 정보가 있는 항목: {len(geocode_map)}개")

    # 새 data.json 로드
    with open('/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus/data.json', 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    print(f"새 데이터: {len(new_data)}개")

    # geocode 정보 매핑
    matched = 0
    for item in new_data:
        code = item.get('code')
        if code in geocode_map:
            item['lat'] = geocode_map[code]['lat']
            item['lng'] = geocode_map[code]['lng']
            matched += 1

    print(f"geocode 매핑 완료: {matched}개")

    # 저장
    with open('/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus/data.json', 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    print("data.json 업데이트 완료")

    # geocode 없는 항목 수 확인
    no_geocode = sum(1 for item in new_data if 'lat' not in item or not item.get('lat'))
    print(f"geocode 없는 항목: {no_geocode}개")

if __name__ == '__main__':
    main()
