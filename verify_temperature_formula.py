#!/usr/bin/env python3
"""온도 계산 공식 검증 (기준값 테스트)."""

import numpy as np
from solar_system_sim_v2_openai import SimulationEngine, PLANETS

ENGINE = SimulationEngine(PLANETS)

# 기준값 테스트
REFERENCE_VALUES = [
    ("기준 (L=1, A=0.306, d=1, atm=1)", {
        "luminosity_ratio": 1.0,
        "albedo": 0.306,
        "distance_au": 1.0,
        "atmosphere_fraction": 1.0,
    }, (287.5, 288.5)),  # 288.0 ± 0.5

    ("광도 2배", {
        "luminosity_ratio": 2.0,
        "albedo": 0.306,
        "distance_au": 1.0,
        "atmosphere_fraction": 1.0,
    }, (321.5, 322.5)),  # 약 322 K

    ("광도 0.5배", {
        "luminosity_ratio": 0.5,
        "albedo": 0.306,
        "distance_au": 1.0,
        "atmosphere_fraction": 1.0,
    }, (247.5, 248.5)),  # 약 248 K

    ("거리 1.5 AU", {
        "luminosity_ratio": 1.0,
        "albedo": 0.306,
        "distance_au": 1.5,
        "atmosphere_fraction": 1.0,
    }, (240.5, 241.5)),  # 약 241 K

    ("거리 0.7 AU", {
        "luminosity_ratio": 1.0,
        "albedo": 0.306,
        "distance_au": 0.7,
        "atmosphere_fraction": 1.0,
    }, (336.5, 337.5)),  # 약 337 K

    ("알베도 0.8 (눈덩이 지구)", {
        "luminosity_ratio": 1.0,
        "albedo": 0.8,
        "distance_au": 1.0,
        "atmosphere_fraction": 1.0,
    }, (219.5, 220.5)),  # 약 220 K

    ("대기 완전 소실 (atm=0)", {
        "luminosity_ratio": 1.0,
        "albedo": 0.306,
        "distance_au": 1.0,
        "atmosphere_fraction": 0.0,
    }, (253.5, 254.5)),  # 약 254 K
]

print("=" * 70)
print("온도 계산 공식 검증 (기준값 테스트)")
print("=" * 70)

passed = 0
failed = 0

for description, params, expected_range in REFERENCE_VALUES:
    temp_k = ENGINE._calculate_earth_temperature(**params)
    temp_c = temp_k - 273.15

    min_k, max_k = expected_range
    in_range = min_k <= temp_k <= max_k

    status = "✓ PASS" if in_range else "✗ FAIL"
    if in_range:
        passed += 1
    else:
        failed += 1

    print(f"\n{status}: {description}")
    print(f"  기대값: {min_k:.1f}~{max_k:.1f} K")
    print(f"  계산값: {temp_k:.1f} K ({temp_c:.1f}°C)")

print("\n" + "=" * 70)
print(f"결과: {passed}개 통과, {failed}개 실패")
print("=" * 70)

# 모델 B 검산
print("\n모델 B 검산 (태양 질량 변화):")
print("=" * 70)

mu_tests = [
    (0.8, "장반경 비", 1.333, "이심률", 0.250),
    (1.2, "장반경 비", 0.857, "이심률", 0.167),
]

for mu, label1, expected1, label2, expected2 in mu_tests:
    result = ENGINE._earth_orbit_sudden_change(mu)

    if result.get("escape"):
        print(f"\nμ={mu}: 탈출 (E ≥ 0)")
    else:
        a_ratio = result.get("a_ratio", None)
        e = result.get("eccentricity", None)

        if a_ratio is None:
            a_status = "✗ FAIL (None)"
        else:
            a_diff = abs(a_ratio - expected1)
            a_status = "✓" if a_diff < 0.01 else "✗"

        if e is None:
            e_status = "✗ FAIL (None)"
        else:
            e_diff = abs(e - expected2)
            e_status = "✓" if e_diff < 0.01 else "✗"

        print(f"\nμ={mu}:")
        print(f"  {a_status} {label1}: {a_ratio:.3f} (기대: {expected1:.3f})")
        print(f"  {e_status} {label2}: {e:.3f} (기대: {expected2:.3f})")
