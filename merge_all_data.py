#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
모든 데이터를 병합하는 스크립트
- 새로운 포커스미디어 데이터 (251201)
- 기존 타운보드 데이터 (만첨/가동)
- 기존 좌표 정보 유지
"""

import json
import os

BASE_DIR = '/Users/wtpceo/Desktop/01.위플 프로젝트/01.개발/08.homepages_1/03.focus'

def main():
    # 1. 기존 data.json에서 타운보드 데이터와 좌표 정보 추출
    old_data_file = os.path.join(BASE_DIR, 'data.json')
    with open(old_data_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)

    # 좌표 정보 매핑 (이름 -> 좌표)
    coords_map = {}
    for item in old_data:
        if item.get('lat') and item.get('lng'):
            coords_map[item['name']] = {'lat': item['lat'], 'lng': item['lng']}

    # 타운보드 데이터만 추출
    townboard_data = [item for item in old_data if item.get('type') in ['townboard', 'townboard_op']]
    print(f"기존 타운보드 데이터: {len(townboard_data)}개")
    print(f"  - 타운보드 만첨: {len([d for d in townboard_data if d.get('type') == 'townboard'])}개")
    print(f"  - 타운보드 가동: {len([d for d in townboard_data if d.get('type') == 'townboard_op'])}개")

    # 2. 새 포커스미디어 데이터 로드
    new_fm_file = os.path.join(BASE_DIR, 'data_focusmedia.json')
    with open(new_fm_file, 'r', encoding='utf-8') as f:
        new_fm_data = json.load(f)

    print(f"새 포커스미디어 데이터: {len(new_fm_data)}개")

    # 3. 새 포커스미디어 데이터에 기존 좌표 정보 적용
    coords_applied = 0
    for item in new_fm_data:
        if item['name'] in coords_map:
            item['lat'] = coords_map[item['name']]['lat']
            item['lng'] = coords_map[item['name']]['lng']
            coords_applied += 1

    print(f"좌표 정보 적용: {coords_applied}개")

    # 4. 모든 데이터 병합
    all_data = new_fm_data + townboard_data
    print(f"\n최종 데이터: {len(all_data)}개")

    # 5. 저장
    output_file = os.path.join(BASE_DIR, 'data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {output_file}")

    # 6. 영업제한 업종 통계
    with_restriction = [d for d in all_data if d.get('restriction1_type') or d.get('restriction2_type')]
    print(f"\n영업제한 업종 있는 데이터: {len(with_restriction)}개")

    # 샘플 출력
    if with_restriction:
        print("\n=== 영업제한 업종 샘플 ===")
        sample = with_restriction[0]
        print(f"단지명: {sample['name']}")
        print(f"구좌1: {sample.get('restriction1_type', '')} ({sample.get('restriction1_date', '')})")
        print(f"구좌2: {sample.get('restriction2_type', '')} ({sample.get('restriction2_date', '')})")

if __name__ == '__main__':
    main()
