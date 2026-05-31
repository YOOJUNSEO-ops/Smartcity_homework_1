import sys, json, csv, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import shapefile
from pyproj import Transformer

BASE = r'C:\smartcity\smartcity_homework1\dong_shp'
SHP = BASE + r'\bnd_dong_00_2025_2Q.shp'
CSV = BASE + r'\pop_total.csv'
OUT = r'C:\smartcity\smartcity_homework1\seongbuk_dong.geojson'

# EPSG:5179 → WGS84
transformer = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)

def transform_ring(ring):
    return [[round(lng,7), round(lat,7)]
            for x, y in ring
            for lng, lat in [transformer.transform(x, y)]]

def transform_geometry(shape):
    if shape.shapeType == 0: return None
    parts = list(shape.parts) + [len(shape.points)]
    rings = [transform_ring(shape.points[parts[i]:parts[i+1]])
             for i in range(len(parts)-1)]
    if len(rings) == 1:
        return {"type": "Polygon", "coordinates": rings}
    return {"type": "MultiPolygon", "coordinates": [[rings[0]], *[[r] for r in rings[1:]]]}

# ── 인구 CSV 로드 (to_in_001 = 총인구) ──────────────────────
print("인구 CSV 로드 중...")
pop_map = {}  # adm_cd -> 총인구
with open(CSV, encoding='euc-kr', errors='replace') as f:
    reader = csv.reader(f)
    next(reader)  # header
    for row in reader:
        if len(row) < 4: continue
        code = row[1].strip().strip('"')
        item = row[2].strip().strip('"')
        val  = row[3].strip().strip('"')
        if item == 'to_in_001' and code.startswith('11080') and len(code) == 8:
            try:
                pop_map[code] = int(val)
            except ValueError:
                pass

print(f"  → 성북구 읍면동 {len(pop_map)}개 인구 로드")
for k, v in sorted(pop_map.items()):
    print(f"     {k}: {v:,}명")

# ── DBF에서 성북구 행정동 코드 확인 ────────────────────────
print("\n읍면동 SHP 로드 중 (전국 → 성북구 필터)...")
sf = shapefile.Reader(SHP, encoding='utf-8')
fields = [f[0] for f in sf.fields[1:]]
print(f"  DBF 필드: {fields}")

# 샘플 레코드 확인
for i in range(3):
    d = dict(zip(fields, sf.record(i)))
    print(f"  sample {i}: {d}")

# ── 성북구(11080) 필터링 + GeoJSON 생성 ────────────────────
features = []
total = len(sf)
matched_pop = 0

for i, (rec, shape) in enumerate(zip(sf.iterRecords(), sf.iterShapes())):
    d = dict(zip(fields, rec))
    # ADM_CD 필드 찾기
    adm_cd = str(d.get('ADM_CD', d.get('adm_cd', ''))).strip()

    if not adm_cd.startswith('11080'):
        continue

    geom = transform_geometry(shape)
    if geom is None:
        continue

    pop = pop_map.get(adm_cd, 0)
    if pop > 0:
        matched_pop += 1

    props = {
        'adm_cd':  adm_cd,
        'adm_nm':  str(d.get('ADM_NM', d.get('adm_nm', ''))).strip(),
        'tot_pop': pop,
    }
    features.append({"type": "Feature", "geometry": geom, "properties": props})

print(f"\n  → 성북구 읍면동 {len(features)}개 추출, 인구 매핑 {matched_pop}개")

# ── 저장 ────────────────────────────────────────────────────
geojson = {"type": "FeatureCollection", "features": features}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False, separators=(',',':'))

import os
print(f"  → 저장: {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")
print("완료!")
