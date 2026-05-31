# 성북구 토지이용 분석 시스템

가천대학교 스마트시티학과 | 국토데이터분석실습 과제

## 개요

성북구 전체 필지(52,970개)의 **용도지역·이용상황·건축물 주용도**를 지도에 시각화하고, 읍면동 단위 인구 분포를 코로플레스(단계구분도)로 표출하는 웹 GIS 시스템입니다.

**라이브 데모:** https://yoojunseo-ops.github.io/Smartcity_homework_1/

---

## 주요 기능

| 뷰 | 설명 |
|----|------|
| **용도지역** | 제1종전용주거~개발제한구역 등 용도지역별 색상 표출 |
| **이용상황** | 단독·아파트·상업용·임야 등 토지 이용 현황 |
| **주용도** | 건축물대장 937건 조인 → 건축물 용도 시각화 |
| **인구** | 읍면동 20개 인구 코로플레스 (2024년 기준) |

- 마우스 호버 시 필지 정보 즉시 표시
- 필지 클릭 시 상세 정보 카드 (PNU, 면적, 공시지가, 건축물 주용도 등)
- 도넛 차트 + 비율 테이블 (건수·% 동시 표시)
- Vworld WMTS 베이스맵

---

## 사용 데이터

| 데이터 | 출처 | 비고 |
|--------|------|------|
| 연속지적도 (용도지역 포함) | [Vworld 국토공간정보](https://www.vworld.kr) | 성북구, EPSG:5186 |
| 건축물대장 총괄표제부 | [건축데이터 민간개방](https://www.hub.go.kr) | 성북구 2026.05 |
| 읍면동 경계 + 인구 통계 | [SGIS 소지역통계](https://sgis.mods.go.kr) | 2025년 2분기 경계, 2024년 인구 |

---

## 파일 구성

```
smartcity_homework1/
├── index.html                  # 메인 웹 지도 (Leaflet + Chart.js)
├── seongbuk_land.geojson       # 필지 52,970개 (좌표계 변환 완료, WGS84)
├── seongbuk_dong.geojson       # 읍면동 20개 + 인구 수치
├── preprocess.py               # SHP → GeoJSON 변환 + 건축물대장 조인
├── preprocess_dong.py          # 읍면동 경계 + 인구 CSV 처리
└── 02. 총괄표제부_20260531175655.csv  # 건축물대장 원본
```

---

## 실행 방법

```bash
# 로컬 서버 실행 (Python 3)
cd smartcity_homework1
python -m http.server 8080

# 브라우저에서 열기
http://localhost:8080
```

> GeoJSON 파일(~29MB)을 로드하므로 처음 열릴 때 3~5초 소요됩니다.

---

## 데이터 재생성

원본 데이터를 다시 받아 GeoJSON을 새로 만들 때:

```bash
# 1. 필지 GeoJSON 생성 (연속지적도 SHP + 건축물대장 CSV)
python preprocess.py

# 2. 읍면동 인구 GeoJSON 생성 (전국 읍면동 SHP + 인구 CSV)
python preprocess_dong.py
```

**필요 패키지:**
```bash
pip install pyshp pyproj
```

---

## 기술 스택

- **Frontend:** HTML5, Leaflet.js 1.9.4, Chart.js 4.4
- **베이스맵:** Vworld WMTS
- **데이터 처리:** Python (pyshp, pyproj)
- **좌표계:** EPSG:5186 / EPSG:5179 → WGS84 변환
