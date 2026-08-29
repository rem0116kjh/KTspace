"""태양계 WHAT IF 앱에서 사용하는 100개 검증 가능한 시나리오 프리셋."""

from typing import Any, Dict, List

from solar_system_sim_v2_openai import ScenarioType, SimulationEngine


CATEGORY_LABELS = {
    ScenarioType.SUN_MASS.value: "태양 질량 변화",
    ScenarioType.EARTH_MASS.value: "지구 질량 변화",
    ScenarioType.BLACKHOLE.value: "블랙홀 출현",
    ScenarioType.SIRIUS.value: "시리우스 A 출현",
    ScenarioType.EARTH_DISTANCE.value: "지구 궤도 변화",
    ScenarioType.EARTH_ROTATION.value: "자전 속도 변화",
    ScenarioType.SOLAR_LUMINOSITY.value: "태양 광도 변화",
    ScenarioType.EARTH_ALBEDO.value: "지표 반사율 변화",
    ScenarioType.ATMOSPHERE_LOSS.value: "대기 손실",
    ScenarioType.MAGNETIC_FIELD.value: "자기장 변화",
}


def _mass_presets(kind: ScenarioType, values: List[float]) -> List[Dict[str, Any]]:
    target = "태양" if kind == ScenarioType.SUN_MASS else "지구"
    presets = []
    for index, value in enumerate(values, 1):
        direction = "증가" if value > 0 else "감소"
        presets.append({
            "id": f"{kind.value}-{index:02d}",
            "type": kind.value,
            "title": f"{target} 질량 {abs(value):g}% {direction}",
            "params": {"percent_change": value},
        })
    return presets


SCENARIO_PRESETS: List[Dict[str, Any]] = []
SCENARIO_PRESETS += _mass_presets(
    ScenarioType.SUN_MASS,
    [-50, -20, -10, -5, -2, -1, 1, 2, 5, 10, 20, 50],
)
SCENARIO_PRESETS += _mass_presets(
    ScenarioType.EARTH_MASS,
    [-50, -20, -10, -5, -2, -1, 1, 2, 5, 10, 20, 50],
)

for index, (mass, distance) in enumerate([
    (1, 0.1), (1, 0.5), (1, 1.0),
    (5, 0.1), (5, 0.5), (5, 1.0),
    (10, 0.1), (10, 0.5), (10, 1.0),
    (20, 0.2), (20, 1.0), (50, 0.5), (50, 2.0),
], 1):
    SCENARIO_PRESETS.append({
        "id": f"blackhole-{index:02d}",
        "type": ScenarioType.BLACKHOLE.value,
        "title": f"{mass:g} 태양질량 블랙홀 · 거리 {distance:g} AU",
        "params": {"mass_solar": mass, "distance_au": distance},
    })

for index, distance in enumerate(
    [0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0], 1
):
    SCENARIO_PRESETS.append({
        "id": f"sirius-{index:02d}",
        "type": ScenarioType.SIRIUS.value,
        "title": f"시리우스 A · 거리 {distance:g} AU",
        "params": {"distance_au": distance},
    })

# 지구 궤도 변화
for index, value in enumerate([-50, -20, -10, -5, 5, 10, 20, 50], 1):
    direction = "증가" if value > 0 else "감소"
    SCENARIO_PRESETS.append({
        "id": f"earth-distance-{index:02d}",
        "type": ScenarioType.EARTH_DISTANCE.value,
        "title": f"궤도 반지름 {abs(value):g}% {direction}",
        "params": {"distance_change_pct": value},
    })

# 자전 속도 변화
for index, hours in enumerate([6, 12, 18, 24, 30, 36, 48, 72], 1):
    SCENARIO_PRESETS.append({
        "id": f"earth-rotation-{index:02d}",
        "type": ScenarioType.EARTH_ROTATION.value,
        "title": f"하루 길이 {hours}시간",
        "params": {"hours_per_day": hours},
    })

# 태양 광도 변화
for index, value in enumerate([-50, -20, -10, -5, 5, 10, 20, 50], 1):
    direction = "증가" if value > 0 else "감소"
    SCENARIO_PRESETS.append({
        "id": f"solar-lum-{index:02d}",
        "type": ScenarioType.SOLAR_LUMINOSITY.value,
        "title": f"광도 {abs(value):g}% {direction}",
        "params": {"luminosity_change_pct": value},
    })

# 지표 반사율 변화
for index, value in enumerate([-50, -30, -15, -5, 5, 15, 30, 50], 1):
    direction = "증가" if value > 0 else "감소"
    SCENARIO_PRESETS.append({
        "id": f"earth-albedo-{index:02d}",
        "type": ScenarioType.EARTH_ALBEDO.value,
        "title": f"반사율 {abs(value):g}% {direction}",
        "params": {"albedo_change_pct": value},
    })

# 대기 손실
for index, pct in enumerate([100, 80, 50, 30, 10, 5, 1, 0], 1):
    SCENARIO_PRESETS.append({
        "id": f"atmosphere-{index:02d}",
        "type": ScenarioType.ATMOSPHERE_LOSS.value,
        "title": f"대기 {pct}% 잔존",
        "params": {"atmosphere_remaining_pct": pct},
    })

# 자기장 변화
for index, pct in enumerate([100, 80, 60, 40, 20, 10, 5, 0], 1):
    SCENARIO_PRESETS.append({
        "id": f"magnetic-{index:02d}",
        "type": ScenarioType.MAGNETIC_FIELD.value,
        "title": f"자기장 {pct}% 강도",
        "params": {"field_strength_pct": pct},
    })

if len(SCENARIO_PRESETS) != 100:
    raise RuntimeError(f"시나리오 프리셋은 정확히 100개여야 합니다: {len(SCENARIO_PRESETS)}")


def presets_for(category: str) -> List[Dict[str, Any]]:
    """선택한 유형의 프리셋만 반환한다."""
    return [preset for preset in SCENARIO_PRESETS if preset["type"] == category]


def run_preset(engine: SimulationEngine, preset: Dict[str, Any]) -> Dict[str, Any]:
    """프리셋을 기존 계산 엔진으로 실행한다."""
    kind, params = preset["type"], preset["params"]
    if kind == ScenarioType.SUN_MASS.value:
        return engine.scenario_sun_mass_change(params["percent_change"])
    if kind == ScenarioType.EARTH_MASS.value:
        return engine.scenario_earth_mass_change(params["percent_change"])
    if kind == ScenarioType.BLACKHOLE.value:
        return engine.scenario_blackhole_nearby(**params)
    if kind == ScenarioType.SIRIUS.value:
        # NASA 값: 시리우스 A 질량 2.063, 광도 24.7
        return engine.scenario_sirius_nearby(
            distance_au=params.get("distance_au", 1.0),
            mass_solar=2.063,
            luminosity_solar=24.7
        )
    if kind == ScenarioType.EARTH_DISTANCE.value:
        return engine.scenario_earth_distance(**params)
    if kind == ScenarioType.EARTH_ROTATION.value:
        return engine.scenario_earth_rotation(**params)
    if kind == ScenarioType.SOLAR_LUMINOSITY.value:
        return engine.scenario_solar_luminosity(**params)
    if kind == ScenarioType.EARTH_ALBEDO.value:
        return engine.scenario_earth_albedo(**params)
    if kind == ScenarioType.ATMOSPHERE_LOSS.value:
        return engine.scenario_atmosphere_loss(**params)
    if kind == ScenarioType.MAGNETIC_FIELD.value:
        return engine.scenario_magnetic_field(**params)
    raise ValueError(f"지원하지 않는 시나리오 유형: {kind}")

