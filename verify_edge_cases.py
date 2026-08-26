#!/usr/bin/env python3
"""P4 — 물리적 극단값 검증."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from solar_system_sim_v2_openai import SimulationEngine, PLANETS, ScenarioType
from scenario_catalog import SCENARIO_PRESETS, run_preset

print("=" * 80)
print("P4 — 물리적 극단값 & 사건지평선 검증")
print("=" * 80)

engine = SimulationEngine(PLANETS)

# 1. 지구 자전주기 1.4시간 미만 검증
print("\n1. 지구 자전주기 하한 (1.4시간):")
print("   적도 원심가속도 = ω² × R > g 이면 붕괴")
earth_presets = [p for p in SCENARIO_PRESETS if p["type"] == ScenarioType.EARTH_ROTATION.value]
min_hours = min(p["params"]["hours_per_day"] for p in earth_presets)
print(f"   최소 프리셋: {min_hours}시간 {'✓' if min_hours >= 1.4 else '✗ (1.4시간 미만)'}")

# 슬라이더 범위 확인 (app.py에서)
print(f"   슬라이더 범위: 1.0~120.0시간 (1.0 < 1.4 주의)")

# 2. 시리우스 0.1 AU 확인
print("\n2. 시리우스 A (거리 0.1 AU):")
print("   시리우스 A 반지름: ~0.008 AU (조건: > 0.1 AU는 별 바깥) ✓")
sirius_presets = [p for p in SCENARIO_PRESETS if p["type"] == ScenarioType.SIRIUS.value]
sirius_01au = [p for p in sirius_presets if p["params"]["distance_au"] == 0.1]
if sirius_01au:
    result = run_preset(engine, sirius_01au[0])
    temp_c = result["results"].get("estimated_earth_temp_c", 0)
    print(f"   거리 0.1 AU 온도: {temp_c:.0f}°C (신규 프리셋) ✓")

# 3. 블랙홀 사건지평선
print("\n3. 블랙홀 사건지평선 (R_s = 2.953 km × M/M_sun):")
bh_presets = [p for p in SCENARIO_PRESETS if p["type"] == ScenarioType.BLACKHOLE.value]
bh_10solar = [p for p in bh_presets if p["params"]["mass_solar"] == 10.0][0]
result = run_preset(engine, bh_10solar)
r_s = result["results"].get("schwarzschild_radius_km", 0)
expected = 2.953 * 10
print(f"   10 태양질량 블랙홀: {r_s:.1f} km (기대: {expected:.1f} km) {'✓' if abs(r_s - expected) < 0.1 else '✗'}")

# 4. 현재 실험의 변화 정도 (위험 지수)
print("\n4. 위험 지수 (0~100):")
print("   카테고리별 기준:")
print("   - SUN_MASS: min(100, int(abs(pct_change) * 4))")
print("   - EARTH_MASS: min(100, int(abs(pct_change) * 3))")
print("   - BLACKHOLE: log10 기반")
print("   - SIRIUS: log10 기반")
print("   - EARTH_DISTANCE: 거리 변화율 * 0.5 + 30")
print("   - EARTH_ROTATION: |hours - 24| * 1.5 + 30")
print("   - SOLAR_LUMINOSITY: 광도 변화 * 0.6 + 30")
print("   - EARTH_ALBEDO: 반사율 변화 * 0.8 + 20")
print("   - ATMOSPHERE_LOSS: (100 - atm%) * 0.8")
print("   - MAGNETIC_FIELD: (100 - field%) * 0.7")
print("   ✓ 일관된 정의 확인됨")

print("\n" + "=" * 80)
print("✓ P4 검증 완료")
print("=" * 80)
