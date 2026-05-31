import sys, os, json, csv
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import shapefile
from pyproj import Transformer

# ── 경로 설정 ──────────────────────────────────────────────
BASE = r'C:\smartcity\smartcity_homework1'
SHP_PATH = os.path.join(BASE, '토지이용', 'AL_D194_11290_20260520.shp')
CSV_PATH = os.path.join(BASE, '02. 총괄표제부_20260531175655.csv')
OUT_PATH = os.path.join(BASE, 'seongbuk_land.geojson')

# ── 좌표 변환기: EPSG:5186 → WGS84 ──────────────────────────
transformer = Transformer.from_crs("EPSG:5186", "EPSG:4326", always_xy=True)

def transform_ring(ring):
    return [[round(lng, 5), round(lat, 5)] for x, y in ring
            for lng, lat in [transformer.transform(x, y)]]

def transform_geometry(shape):
    stype = shape.shapeType
    if stype == 5:  # Polygon
        parts = list(shape.parts) + [len(shape.points)]
        rings = [transform_ring(shape.points[parts[i]:parts[i+1]])
                 for i in range(len(parts) - 1)]
        if len(rings) == 1:
            return {"type": "Polygon", "coordinates": rings}
        return {"type": "MultiPolygon", "coordinates": [[rings[0]], *[[r] for r in rings[1:]]]}
    return None

# ── 건축물대장 CSV → PNU : 주용도 매핑 ──────────────────────
print("건축물대장 로드 중...")
building_map = {}  # pnu -> {주용도코드명, 연면적, 세대수}

with open(CSV_PATH, encoding='utf-8-sig', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            sigungu  = row['시군구코드'].zfill(5)
            bdong    = row['법정동코드'].zfill(5)
            # 건축물대장 대지구분코드: 0=일반→SHP에서는 1, 1=산→SHP에서는 2
            dg_raw   = row['대지구분코드'].strip()
            daejigub = str(int(dg_raw) + 1) if dg_raw.isdigit() else '1'
            bun      = row['번'].zfill(4)
            ji       = row['지'].zfill(4)
            pnu = sigungu + bdong + daejigub + bun + ji

            yonedo   = row.get('주용도코드명', '').strip()
            yeonmyeon = row.get('연면적(㎡)', '0').strip() or '0'
            sedaesu  = row.get('세대수(세대)', '0').strip() or '0'

            building_map[pnu] = {
                'yonedo': yonedo,
                'yeonmyeon': float(yonedo and yeonmyeon or 0),
                'sedaesu': int(sedaesu) if sedaesu.isdigit() else 0
            }
        except Exception:
            pass

print(f"  → {len(building_map)}개 건물 로드 완료")

# ── SHP → GeoJSON 변환 ──────────────────────────────────────
print("SHP 변환 중... (52,970 필지)")

sf = shapefile.Reader(SHP_PATH, encoding='euc-kr')
field_names = [f[0] for f in sf.fields[1:]]

features = []
skip = 0
matched = 0

for i, (rec, shape) in enumerate(zip(sf.iterRecords(), sf.iterShapes())):
    if i % 5000 == 0:
        print(f"  {i:,} / 52,970 처리 중...")

    if shape.shapeType == 0:
        skip += 1
        continue

    geom = transform_geometry(shape)
    if geom is None:
        skip += 1
        continue

    d = dict(zip(field_names, rec))
    pnu = str(d.get('A1', '')).strip()

    # SHP 필드 매핑
    props = {
        'pnu':         pnu,
        'address':     str(d.get('A3', '')).strip(),
        'jibun':       str(d.get('A6', '')).strip(),
        'jimok':       str(d.get('A11', '')).strip(),   # 지목
        'area':        float(d.get('A12', 0) or 0),     # 면적(㎡)
        'yodojiyeok':  str(d.get('A14', '')).strip(),   # 용도지역
        'jigudan':     str(d.get('A16', '')).strip(),   # 지구단위계획
        'iyongsang':   str(d.get('A18', '')).strip(),   # 이용상황
        'gongsi':      int(d.get('A25', 0) or 0),       # 개별공시지가(원/㎡)
    }

    # 건축물대장 조인
    bldg = building_map.get(pnu)
    if bldg:
        props['juyongdo'] = bldg['yonedo']
        props['yeonmyeon'] = bldg['yeonmyeon']
        props['sedaesu'] = bldg['sedaesu']
        matched += 1
    else:
        props['juyongdo'] = ''
        props['yeonmyeon'] = 0
        props['sedaesu'] = 0

    features.append({"type": "Feature", "geometry": geom, "properties": props})

print(f"  → 변환 완료: {len(features):,}개, 건축물 조인: {matched}개, 스킵: {skip}개")

# ── GeoJSON 저장 ─────────────────────────────────────────────
print("GeoJSON 저장 중...")
geojson = {"type": "FeatureCollection", "features": features}

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, separators=(',', ':'))

size_mb = os.path.getsize(OUT_PATH) / 1024 / 1024
print(f"  → 저장 완료: {OUT_PATH}")
print(f"  → 파일 크기: {size_mb:.1f} MB")
print("완료!")
