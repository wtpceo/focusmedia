# 미디어지도 최신화 계획 — 260615

## 🎯 목표 4요소

| 요소 | 내용 |
|---|---|
| **목표** | 포커스미디어 + 타운보드 가동(S/L) 260615 데이터를 지도에 반영 |
| **범위** | `convert_xlsx_251201.py`, `merge_all_data.py`, `data.json`, `data_focusmedia.json`, `CLAUDE.md`만 수정. 만첨·HTPOST·MM 스크립트 로직은 손대지 않음 |
| **종료 조건** | data.json 재생성 + 좌표 없는 데이터 0개 + 영업제한 정상 반영 + 검수 봇 Critical/High 0건 |
| **검증 명령** | `python3 convert → merge → fix_geocode` 실행 후 타입별 개수·좌표·영업제한 검증 스크립트 PASS |

## 📦 이번에 받은 파일 (2개만)

| 파일 | 매체 | 비고 |
|---|---|---|
| `엘리베이터TV 설치리스트(외부용)_260615.xlsx` | 포커스미디어 | 4,674행 |
| `타운보드 가동리스트(로컬상품)_260615.xlsx` | 타운보드S/L 가동 | S 2,834 / L 323 |

→ **만첨(260608) · HTPOST 영상(260602) · HTPOST 전단지 · MEDIA MEET는 직전 그대로 유지.**

## ⚠️ 핵심 이슈: 영업제한 컬럼명 형식 회귀

엑셀 만드는 쪽이 컬럼명 공백을 매 회차 다르게 넣음 — 이번에 **다시 공백 형식으로 되돌아옴**:

| 회차 | 구좌1 업종 컬럼명 |
|---|---|
| 260427 이전 | `구좌1 \n영업제한 업종` (공백 O) |
| 260608 | `구좌1\n영업제한 업종` (공백 X) ← 현재 스크립트 |
| **260615** | `구좌1 \n영업제한 업종` (공백 O) ← **또 바뀜** |

**현재 스크립트(공백 X 기준)로 그대로 돌리면 영업제한 438개 → 0개로 사라짐 (production 회귀).**

### 해결안: 컬럼명 정규화 매칭 (한 번 고치면 다신 안 깨짐)

`convert_xlsx_251201.py`의 영업제한 4줄을, 공백·줄바꿈을 무시하고 찾는 헬퍼로 교체:

```python
def get_col(row, *keywords):
    """컬럼명에서 공백·줄바꿈 제거 후 모든 keyword를 포함하는 컬럼 값 반환"""
    for col in row.index:
        norm = str(col).replace(' ', '').replace('\n', '')
        if all(k in norm for k in keywords):
            return row[col]
    return ''

restriction1_type = clean_text(get_col(row, '구좌1', '영업제한업종'))
restriction1_date = clean_date(get_col(row, '구좌1', '영업제한기한'))
restriction2_type = clean_text(get_col(row, '구좌2', '영업제한업종'))
restriction2_date = clean_date(get_col(row, '구좌2', '영업제한기한'))
```

→ 공백이 있든 없든, 줄바꿈 위치가 어디든 항상 매칭. 향후 회차에서 또 바뀌어도 안전.

## 📝 수정 파일 목록

| 파일 | 변경 |
|---|---|
| `convert_xlsx_251201.py` | ① 입력파일 → `_260615.xlsx` ② 영업제한 4줄 → 정규화 헬퍼로 교체 |
| `merge_all_data.py` | 타운보드 파일 → `_260615.xlsx` (만첨·HTPOST 파일명 유지) |
| `data_focusmedia.json` / `data.json` | 재생성됨 |
| `CLAUDE.md` | 260615 이력 추가 |

## ✅ 작업 체크리스트

- [x] 1. 새 엑셀 2개를 프로젝트 폴더로 복사
- [x] 2. `data.json` → `data.json.bak_260617` 백업
- [x] 3. `convert_xlsx_251201.py` 입력파일명 260615로 변경
- [x] 4. `convert_xlsx_251201.py` 영업제한 4줄 → 정규화 헬퍼로 교체
- [x] 5. `merge_all_data.py` 타운보드 파일명 260615로 변경
- [x] 6. `python3 convert_xlsx_251201.py` 실행 → 포커스미디어 JSON 생성 (영업제한 0 아닌지 확인)
- [x] 7. `python3 merge_all_data.py` 실행 → data.json 병합
- [x] 8. `python3 fix_geocode_kakao.py` 실행 → 좌표 없는 신규 단지 지오코딩
- [x] 9. 지오코딩 실패분 동일 단지 좌표 수동 적용
- [x] 10. 정합성 검증: 타입별 개수 / 좌표 0개 / 한국 범위 / 영업제한 ~438개 / 이름 누락 0
- [x] 11. `CLAUDE.md` 260615 이력 추가
- [x] 12. 검수 봇 호출 → Critical/High 0건까지 수정 루프
- [ ] 13. 커밋 (명시 파일만) → 사용자 "푸시" 신호 대기

## 📊 예상 결과 수치

| 타입 | 260608(현재) | 260615(예상) |
|---|---|---|
| focusmedia | 4,659 | **4,674** (+15) |
| townboard_op (타운보드S 가동) | 2,834 | 2,834 (유지) |
| townboard_l | 322 | **323** (+1) |
| townboard (만첨) | 92 | 92 (유지) |
| htpost (영상) | 116 | 116 (유지) |
| htpost_leaflet (전단지) | 97 | 97 (유지) |
| mediameet_interior | 817 | 817 (유지) |
| mediameet_waiting | 108 | 108 (유지) |
| **총합** | 9,045 | **약 9,061 (+16)** |

> 실제 개수는 구현 시 변환·병합 출력으로 확정. 좌표 없는 신규 단지는 카카오 지오코딩으로 0개까지 해소.

## 🚫 명확한 금지

- 만첨·HTPOST·MEDIA MEET 변환 함수 로직 수정 금지 (파일명도 그대로)
- `index.html`, 마커 색상, 필터 UI 손대지 않음
- `git add` 와일드카드 금지 — 명시 파일만
- 사용자 "푸시" 신호 전까지 push 금지
