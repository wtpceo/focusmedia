# 포커스미디어 지도 프로젝트

## 프로젝트 개요
포커스미디어 엘리베이터TV, 타운보드, CGV/메가박스 스크린 광고 설치 위치를 지도에 표시하는 웹 페이지

## 핵심 파일 구조

### 데이터 파일
| 파일명 | 설명 | 비고 |
|--------|------|------|
| `data.json` | 최종 통합 데이터 (포커스미디어 + 타운보드 + HTPOST + MEDIA MEET) | 메인 데이터, 9,190개 |
| `data_focusmedia.json` | 포커스미디어 전용 데이터 | 중간 변환 파일, 4,840개 |
| `data_mediameet.json` | MEDIA MEET 전용 데이터 | 중간 변환 파일 |
| `cgv_converted.json` | CGV 영화관 데이터 (별도 로드) | 143개 |
| `megabox_converted.json` | 메가박스 영화관 데이터 (별도 로드) | 111개 |

> 이 수치는 회차마다 변함 — 최신값은 `docs/update-history.md` 최상단 참조

### 소스 파일
| 파일명 | 설명 |
|--------|------|
| `index.html` | 메인 지도 페이지 |
| `convert_xlsx_251201.py` | 포커스미디어 엑셀→JSON 변환 스크립트 (→ `data_focusmedia.json`) |
| `convert_mediameet.py` | MEDIA MEET 엑셀→JSON 변환 스크립트 (→ `data_mediameet.json`) |
| `merge_all_data.py` | 전체 병합 스크립트 (타운보드·HTPOST는 이 안에서 엑셀 직접 변환) |
| `fix_geocode_kakao.py` | 카카오 지오코딩 스크립트 (좌표 없는 신규 단지 채움) |

### 원본 엑셀 파일 (YYMMDD = 회차 날짜, 최신 회차 파일명은 `docs/update-history.md` 최상단 참조)
- `엘리베이터TV 설치리스트(외부용)_YYMMDD.xlsx` — 포커스미디어 설치 리스트
- `타운보드 가동리스트(로컬상품)_YYMMDD.xlsx` — 타운보드 가동 (S/L 시트 각각)
- `타운보드S 만첨단지리스트_YYMMDD(공유|_배포용).xlsx` / `타운보드L …` — 타운보드 만첨 (S/L 파일 분리). ⚠️ 파일명 접미사(`(공유)`/`_배포용`)와 **시트명이 회차마다 `만첨리스트` ↔ `S 만첨리스트`/`L 만첨리스트`로 오감** — 매 회차 시트명 확인 필수
- `[현대에이치티] 단지별 로컬광고단가_MM월.xlsx` (09월분은 `_09.xlsx`) — HTPOST 영상+전단지 (`가격정책` 시트). 기본 소스이며, 이 파일이 안 오는 회차에만 영상을 로컬파트너사 파일에서 읽는다
- `MEDIA MEET 설치리스트_YYMMDD.xlsx` — MEDIA MEET 설치 리스트
- `HTPOST 가동리스트_로컬파트너사_YYMMDD.xlsx` — HTPOST **영상 전용** 구형식(`HT_로컬파트너사` 시트). 260720 전까지 쓰다 통합파일로 옮겼으나 **260824 회차에 다시 이 파일만 와서 영상은 여기서 읽음**(`convert_htpost_video_partner`). 전단지 정보는 없음.
  🔒 **git 커밋 금지** — 상호명·연락처·상담내용이 든 시트 5종이 동봉돼 있고 이 저장소는 공개다. `.gitignore`로 차단해 둠

---

## 데이터 업데이트 작업 가이드

한 회차 업데이트는 최대 6개 소스를 다룬다: **포커스미디어 · 타운보드 가동 S/L · 타운보드 만첨 S/L · HTPOST 영상/전단지 · MEDIA MEET**. 회차마다 전부 오는 게 아니라 온 파일만 갱신하고 나머지는 유지한다.

#### Step 1: 새 엑셀 파일 확인
```bash
# 엑셀 파일 컬럼 구조 확인 (포커스미디어 헤더는 4행에 있음, 0-indexed로 3)
python3 -c "
import pandas as pd
df = pd.read_excel('엘리베이터TV 설치리스트(외부용)_YYMMDD.xlsx', header=3)
print('컬럼:', list(df.columns))
print('총 행수:', len(df))
"
```

#### Step 2: 포커스미디어 변환
```bash
# convert_xlsx_251201.py 안의 input_file 경로를 새 회차 파일명으로 수정 후 실행
python3 convert_xlsx_251201.py
# 결과: data_focusmedia.json 생성
```

#### Step 3: MEDIA MEET 변환 (MM 새 파일이 온 회차만)
```bash
# convert_mediameet.py 안의 INPUT_FILE을 새 회차 파일명으로 수정 후 실행
python3 convert_mediameet.py
# 결과: data_mediameet.json 생성
```

#### Step 4: 전체 병합
```bash
# merge_all_data.py 안에 타운보드 가동/만첨/HTPOST 입력 파일명이 하드코딩되어 있음
# → 새 회차 파일명으로 수정 후 실행
python3 merge_all_data.py
# 하는 일: data_focusmedia.json + data_mediameet.json 로드,
#          타운보드 가동 S/L·만첨 S/L·HTPOST 영상/전단지는 엑셀에서 직접 변환,
#          기존 data.json의 좌표를 이름 기준으로 물려받아 data.json 저장
# (CGV/메가박스는 여기 안 들어감 — 별도 파일로 index.html이 직접 로드)
```

#### Step 5: 지오코딩 (매 회차 정규 단계)
```bash
# 신규 단지는 좌표가 없으므로 매 회차 실행 — 카카오 API로 좌표 채움
python3 fix_geocode_kakao.py
# 실행 후 merge_all_data.py 출력의 "좌표 없는 데이터" 개수가 0(또는 기존 예외만)인지 확인
```

#### Step 6: 검증
- 브라우저에서 `index.html` 열어서 지도 확인
- 데이터 개수, 필터링 동작 확인

---

## 업데이트 이력

회차별 기록은 `docs/update-history.md`에 있다(최신이 맨 위).
- 데이터 업데이트 작업 전에 **최근 2~3회차를 먼저 Read** — 헤더 행·시트명·파일명이 회차마다 바뀐 기록과 최신 건수가 거기 있다.
- 새 회차 기록은 그 파일 맨 위(제목·안내 블록 바로 아래)에 추가한다. 이 문서에는 이력을 쌓지 않는다.

---

## 데이터 스키마

### focusmedia 타입
```json
{
  "name": "단지명",
  "city": "도시 (예: 경기도)",
  "gu": "구 (예: 고양시 덕양구)",
  "dong": "동 (법정동)",
  "address": "주소 (도로명 우선)",
  "building_type": "건물유형 (아파트 등)",
  "year": 준공연도,
  "floors": 건물층수,
  "area": 기준평형,
  "households": 총세대수,
  "population": 총인구수,
  "quantity": 판매수량,
  "unit_price": 대당단가,
  "price_4w": 4주금액,
  "is_premium": 프리미엄여부,
  "restriction1_type": "구좌1 영업제한 업종",
  "restriction1_date": "구좌1 영업제한 기한",
  "restriction2_type": "구좌2 영업제한 업종",
  "restriction2_date": "구좌2 영업제한 기한",
  "type": "focusmedia",
  "lat": 위도,
  "lng": 경도
}
```

### townboard / townboard_op 타입
- 타운보드 만첨 단지 / 가동 단지 데이터

### townboard_l 타입
- 타운보드L 가동 단지 데이터 (가동리스트의 타운보드L 시트에서 변환)

### htpost 타입
- HTPOST 영상 광고 데이터 (로컬광고단가 파일의 `동영상광고` 제안가 사용)

### htpost_leaflet 타입
- HTPOST 전단지(게시판) 광고 데이터 (게시판 '가능' 단지만, 주간가×4 = price_4w)

### mediameet_interior 타입
- MEDIA MEET 엘리베이터 내부 광고 데이터

### mediameet_waiting 타입
- MEDIA MEET 엘리베이터 대기공간 광고 데이터 (한 단지가 내부·대기공간 둘 다면 2건으로 들어감)

### cgv / megabox 타입
- 영화관 스크린 광고 데이터
- **data.json에 없음** — `cgv_converted.json`·`megabox_converted.json` 별도 파일로 index.html이 직접 로드

---

## 주의사항

1. **엑셀 헤더 위치**: 헤더는 4행 (0-indexed: 3)에 있음
2. **주소 컬럼**: 공백이 있음 - `' 주소(도로명)'`, `' 주소(지번)'`
3. **좌표 보존**: 기존 data.json의 좌표 정보는 merge 시 자동 적용됨
4. **백업**: 변환 전 기존 data.json 백업 권장

---

## 문제 해결

### 새 컬럼이 추가된 경우
`convert_xlsx_251201.py` 스크립트에 해당 컬럼 처리 코드 추가

### 좌표 없는 데이터
- 새로 추가된 단지는 좌표가 없음
- `fix_geocode_kakao.py` 사용하여 좌표 획득 가능
