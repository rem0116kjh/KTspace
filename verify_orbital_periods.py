#!/usr/bin/env python3
"""
8개 행성의 공전주기 검증: 케플러 3법칙 모델 vs NASA 관측값
T = a^1.5 (a: AU, T: 년)
"""

# NASA NSSDCA Planetary Fact Sheet 데이터
PLANETS = [
    {"name": "수성", "a_au": 0.387, "t_days_observed": 88.0},
    {"name": "금성", "a_au": 0.723, "t_days_observed": 224.7},
    {"name": "지구", "a_au": 1.000, "t_days_observed": 365.2},
    {"name": "화성", "a_au": 1.523, "t_days_observed": 687.0},
    {"name": "목성", "a_au": 5.205, "t_days_observed": 4331.0},
    {"name": "토성", "a_au": 9.582, "t_days_observed": 10747.0},
    {"name": "천왕성", "a_au": 19.201, "t_days_observed": 30589.0},
    {"name": "해왕성", "a_au": 30.047, "t_days_observed": 59800.0},
]

def kepler_period_years(a_au):
    """케플러 3법칙: T = a^1.5 (a: AU, T: 년)"""
    return a_au ** 1.5

# 검증 계산
results = []
for planet in PLANETS:
    a = planet["a_au"]
    t_years_calc = kepler_period_years(a)
    t_days_calc = t_years_calc * 365.25
    t_days_obs = planet["t_days_observed"]
    error_pct = ((t_days_calc - t_days_obs) / t_days_obs) * 100

    results.append({
        "name": planet["name"],
        "a_au": a,
        "t_calc_days": t_days_calc,
        "t_obs_days": t_days_obs,
        "error_pct": error_pct,
    })

# 표 출력
print("\n" + "=" * 90)
print("케플러 3법칙 검증: 8개 행성 공전주기")
print("=" * 90)
print(f"{'행성':<8} {'장반경 a (AU)':<18} {'모델 계산 (일)':<18} {'실제 관측 (일)':<18} {'오차':<10}")
print("-" * 90)
for r in results:
    print(f"{r['name']:<8} {r['a_au']:<18.3f} {r['t_calc_days']:<18.1f} {r['t_obs_days']:<18.1f} {r['error_pct']:+.2f}%")
print("-" * 90)
print("출처: NASA NSSDCA Planetary Fact Sheet")

# 통계
errors_float = [r["error_pct"] for r in results]
print(f"\n오차 통계:")
print(f"  평균: {sum(errors_float)/len(errors_float):+.2f}%")
print(f"  최대: {max(errors_float):+.2f}% ({results[errors_float.index(max(errors_float))]['name']})")
print(f"  최소: {min(errors_float):+.2f}% ({results[errors_float.index(min(errors_float))]['name']})")
print(f"\n💡 결론: 단순 2체 모델이 행성 간 상호 중력(섭동)을 무시하므로")
print(f"   바깥 행성으로 갈수록 오차가 커집니다.")
