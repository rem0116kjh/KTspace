#!/usr/bin/env python3
"""P3 — 전체 프리셋 스모크 테스트.

pytest 없이도 실행 가능: python tests/test_all_presets.py
"""

# 이 파일은 자체 main()으로 100개를 순회하는 실행 스크립트다.
# pytest에서는 동일 검증을 test_scenario_catalog.py가 담당하므로 중복 수집하지 않는다.
__test__ = False

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from solar_system_sim_v2_openai import SimulationEngine, PLANETS, ScenarioType
from scenario_catalog import SCENARIO_PRESETS, run_preset


def test_preset_runs_without_exception(preset):
    """프리셋이 예외 없이 완료되는가."""
    engine = SimulationEngine(PLANETS)
    try:
        result = run_preset(engine, preset)
        return True, None
    except Exception as e:
        return False, str(e)


def test_no_none_or_nan_in_results(preset, result):
    """결과에 None/NaN/inf가 없는가 (포물선·쌍곡선 제외)."""
    kind = preset["type"]
    results = result.get("results", {})

    # 포물선·쌍곡선 케이스 (장반경이 없거나 음수)
    if kind == ScenarioType.SUN_MASS.value:
        model_b = result.get("orbit_model_b", {})
        if model_b.get("escape"):
            # 탈출 케이스: 장반경 없음이 정상
            return True, None

    # 모든 결과값 검사
    issues = []
    for key, value in results.items():
        if isinstance(value, dict):
            for k, v in value.items():
                if v is None:
                    issues.append(f"  {key}.{k} = None")
                elif isinstance(v, float):
                    if not (-1e10 < v < 1e10):  # inf/nan 감지
                        issues.append(f"  {key}.{k} = {v}")
        else:
            if value is None:
                issues.append(f"  {key} = None")
            elif isinstance(value, float):
                if not (-1e10 < value < 1e10):
                    issues.append(f"  {key} = {value}")

    if issues:
        return False, "Invalid values:\n" + "\n".join(issues)
    return True, None


def test_temperature_values_reasonable(preset, result):
    """온도가 물리적으로 말이 되는 범위인가 (0 < T < 5000 K)."""
    kind = preset["type"]
    results = result.get("results", {})

    # 온도를 표시하는 카테고리
    temp_keys = {
        ScenarioType.SOLAR_LUMINOSITY.value: "estimated_earth_temp_c",
        ScenarioType.EARTH_ALBEDO.value: "estimated_earth_temp_c",
        ScenarioType.EARTH_DISTANCE.value: "estimated_earth_temp_c",
        ScenarioType.ATMOSPHERE_LOSS.value: "estimated_earth_temp_c",
        ScenarioType.SIRIUS.value: "estimated_earth_temp_c",
    }

    if kind in temp_keys:
        temp_c = results.get(temp_keys[kind])
        if temp_c is not None:
            temp_k = temp_c + 273.15
            if not (0 < temp_k < 5000):
                return False, f"Temperature out of range: {temp_k:.1f} K"

    return True, None


def test_eccentricity_non_negative(preset, result):
    """이심률이 음수가 아닌가."""
    kind = preset["type"]

    if kind == ScenarioType.SUN_MASS.value:
        model_b = result.get("orbit_model_b", {})
        if not model_b.get("escape"):
            e = model_b.get("eccentricity")
            if e is not None and e < 0:
                return False, f"Eccentricity negative: {e}"

    return True, None


def test_a_ratio_non_negative(preset, result):
    """장반경 배율이 음수가 아닌가 (탈출 케이스 제외)."""
    kind = preset["type"]

    if kind == ScenarioType.SUN_MASS.value:
        model_b = result.get("orbit_model_b", {})
        if not model_b.get("escape"):
            a_ratio = model_b.get("a_ratio")
            if a_ratio is not None and a_ratio < 0:
                return False, f"a_ratio negative: {a_ratio}"

    return True, None


def test_temperature_variety(all_results):
    """온도 표시 프리셋들이 전부 288로 동일하지 않은가."""
    temp_presets = {
        ScenarioType.SOLAR_LUMINOSITY.value: [],
        ScenarioType.EARTH_ALBEDO.value: [],
        ScenarioType.EARTH_DISTANCE.value: [],
        ScenarioType.ATMOSPHERE_LOSS.value: [],
        ScenarioType.SIRIUS.value: [],
    }

    for preset, result in all_results:
        kind = preset["type"]
        if kind in temp_presets:
            temp_c = result.get("results", {}).get("estimated_earth_temp_c")
            if temp_c is not None:
                temp_presets[kind].append(temp_c)

    issues = []
    for kind, temps in temp_presets.items():
        if not temps:
            continue
        # 기준값 288K (즉 15°C)
        count_at_15 = sum(1 for t in temps if 14.9 <= t <= 15.1)
        if count_at_15 == len(temps):
            issues.append(f"{kind}: 모든 값이 288K(15°C)로 동일")

    if issues:
        return False, "\n".join(issues)
    return True, None


# =============================================================================
# 메인 테스트 실행
# =============================================================================

def main():
    print("=" * 80)
    print("P3 — 전체 프리셋 스모크 테스트")
    print("=" * 80)

    if len(SCENARIO_PRESETS) != 100:
        print(f"✗ FATAL: 프리셋 개수 오류 (기대: 100, 실제: {len(SCENARIO_PRESETS)})")
        return 1

    print(f"\n✓ 프리셋 개수: {len(SCENARIO_PRESETS)}")

    all_results = []
    failed_presets = []

    for i, preset in enumerate(SCENARIO_PRESETS, 1):
        title = preset.get("title", "?")

        # 테스트 1: 예외 없이 실행
        runs, exc = test_preset_runs_without_exception(preset)
        if not runs:
            failed_presets.append((preset["id"], f"Exception: {exc}"))
            continue

        result = None
        engine = SimulationEngine(PLANETS)
        result = run_preset(engine, preset)
        all_results.append((preset, result))

        # 테스트 2-5: 결과 검증
        checks = [
            (test_no_none_or_nan_in_results, "NaN/None check"),
            (test_temperature_values_reasonable, "Temperature range"),
            (test_eccentricity_non_negative, "Eccentricity >= 0"),
            (test_a_ratio_non_negative, "a_ratio >= 0"),
        ]

        for test_func, test_name in checks:
            success, msg = test_func(preset, result)
            if not success:
                failed_presets.append((preset["id"], f"{test_name}: {msg}"))

    print(f"\n프리셋 실행: {len(SCENARIO_PRESETS) - len(failed_presets)}/{len(SCENARIO_PRESETS)} 성공")

    # 테스트 6: 온도 다양성
    success, msg = test_temperature_variety(all_results)
    if not success:
        print(f"\n✗ 온도 다양성 검사 실패:")
        print(msg)
        failed_presets.append(("temperature_variety", msg))
    else:
        print(f"✓ 온도 다양성 검사: 통과")

    # 결과 출력
    if failed_presets:
        print("\n" + "=" * 80)
        print(f"✗ 실패한 항목 ({len(failed_presets)}개):")
        print("=" * 80)
        for preset_id, reason in failed_presets:
            print(f"\n{preset_id}:")
            print(f"  {reason}")
        return 1
    else:
        print("\n" + "=" * 80)
        print("✓ 모든 테스트 통과!")
        print("=" * 80)
        return 0


if __name__ == "__main__":
    sys.exit(main())
