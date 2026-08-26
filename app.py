"""직접 조작하는 태양계 WHAT IF Streamlit 앱."""

import time
import numpy as np
import streamlit as st

from solar_system_sim_v2_openai import (
    AIInterpreter,
    PLANETS,
    ScenarioType,
    SimulationEngine,
    fallback_interpretation,
)
from scenario_catalog import CATEGORY_LABELS, SCENARIO_PRESETS, presets_for, run_preset


st.set_page_config(
    page_title="태양계 WHAT IF 실험실",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #0a0e27 0%, #1a1a3e 50%, #0d1a2d 100%); color: #e0f2fe; }
    [data-testid="stHeader"] { background: rgba(10, 14, 39, 0.95); border-bottom: 1px solid #00d9ff; box-shadow: 0 0 10px rgba(0, 217, 255, 0.3); }
    [data-testid="stSidebar"] { background: rgba(15, 20, 40, 0.9); border-right: 2px solid #7c3aed; }
    [data-testid="stSidebar"] * { color: #ffffff; }
    [data-baseweb="select"] { background: rgba(30, 45, 80, 0.9) !important; }
    [data-baseweb="select"] input { color: #ffffff !important; font-weight: 500; }
    [data-baseweb="select"] div { color: #ffffff !important; }
    [data-testid="stMetric"] {
        background: rgba(20, 30, 60, 0.8); border: 1px solid #7c3aed;
        border-radius: 10px; padding: 13px 15px; box-shadow: 0 0 15px rgba(124, 58, 237, 0.2);
    }
    [data-testid="stMetricLabel"] { color: #a0d9ff; }
    [data-testid="stMetricValue"] { color: #00ffff; font-family: Georgia, "AppleMyungjo", serif; }
    .hero-kicker {
        display: inline-block; color: #00ffff; background: rgba(0, 255, 255, 0.1);
        border: 1px solid #00ffff; border-radius: 999px; padding: 5px 10px;
        font-size: .78rem; font-weight: 700; letter-spacing: .01em; box-shadow: 0 0 8px rgba(0, 255, 255, 0.5);
    }
    .hero-title {
        color: #00ffff; font-family: Georgia, "AppleMyungjo", serif;
        font-size: 2.6rem; font-weight: 700; margin: .55rem 0 .35rem; letter-spacing: -.025em;
        text-shadow: 0 0 20px rgba(0, 255, 255, 0.4);
    }
    .hero-copy { color: #a0d9ff; font-size: 1rem; margin-bottom: 1.6rem; }
    .result-card {
        background: rgba(25, 35, 75, 0.8); border: 1px solid #7c3aed;
        border-radius: 10px; padding: 16px 18px; margin: 8px 0; box-shadow: 0 0 12px rgba(124, 58, 237, 0.3);
    }
    .danger-card { border-left: 4px solid #ff006e; }
    .eyebrow { color: #64b5f6; font-size: .8rem; margin-bottom: 4px; }
    .big-result { color: #ff006e; font-family: Georgia, "AppleMyungjo", serif; font-size: 1.45rem; font-weight: 700; }
    .safe-note { color: #81d4fa; font-size: .82rem; }
    div.stButton > button { border-radius: 6px; min-height: 44px; font-weight: 700; background: linear-gradient(135deg, #7c3aed 0%, #00ffff 100%); color: white; border: 1px solid #00ffff; }
    h1, h2, h3 { color: #00ffff !important; letter-spacing: -.015em; text-shadow: 0 0 10px rgba(0, 255, 255, 0.3); }
    hr { border-color: #7c3aed !important; }
    [data-baseweb="tab-list"] { border-bottom: 1px solid #7c3aed; }
    [data-baseweb="tab"] { color: #7c7c9e !important; min-width: 120px; }
    [data-baseweb="tab"][aria-selected="true"] { color: #00ffff !important; border-bottom: 2px solid #00ffff !important; }
    [data-testid="stSelectbox"] { color: #e0f2fe; }
    [data-baseweb="select"] { background: rgba(20, 30, 60, 0.8) !important; }
    [data-baseweb="select"] input { color: #e0f2fe !important; }
    [data-baseweb="select"] input::selection { color: #000000 !important; background: rgba(0, 255, 255, 0.5) !important; }
    [data-baseweb="select"] input::-webkit-selection { color: #000000 !important; background: rgba(0, 255, 255, 0.5) !important; }
    [data-baseweb="select"] svg { fill: #00ffff !important; }
    [data-baseweb="menu"] { background: rgba(15, 20, 40, 0.95) !important; border: 1px solid #7c3aed !important; }
    [data-baseweb="menu"] li { color: #e0f2fe !important; }
    [data-baseweb="menu"] li::selection { color: #000000 !important; background: rgba(0, 255, 255, 0.5) !important; }
    [data-baseweb="menu"] li::-webkit-selection { color: #000000 !important; background: rgba(0, 255, 255, 0.5) !important; }
    [data-baseweb="menu"] li:hover { background: rgba(124, 58, 237, 0.3) !important; }
    [data-baseweb="segmented-control"] { background: rgba(20, 30, 60, 0.6) !important; border: 1px solid #7c3aed !important; border-radius: 8px; }
    [data-baseweb="segmented-control"] button { color: #a0d9ff !important; }
    [data-baseweb="segmented-control"] button[aria-selected="true"] { background: rgba(124, 58, 237, 0.6) !important; color: #00ffff !important; box-shadow: 0 0 10px rgba(124, 58, 237, 0.4); }
    [data-testid="stToggle"] label { color: #ffffff !important; }
    [data-testid="stSelectbox"] label { color: #ffffff !important; font-weight: 600; }
    [data-baseweb="select"] label { color: #ffffff !important; font-weight: 600; }
    [data-baseweb="segmented-control-label"] { color: #ffffff !important; font-weight: 600; }
    div[data-testid="stSegmentedControlLabel"] { color: #ffffff !important; font-weight: 600; }
    .stSegmentedControl { color: #ffffff !important; }
    .stSegmentedControl label { color: #ffffff !important; font-weight: 600; }
    [data-baseweb="toggle"] { background: rgba(20, 30, 60, 0.8) !important; }
    [data-baseweb="toggle"][aria-checked="true"] { background: rgba(0, 255, 255, 0.3) !important; }
    [data-baseweb="toggle"] span { background: #7c3aed !important; box-shadow: 0 0 8px rgba(124, 58, 237, 0.5); }
    [data-baseweb="slider"] { background: rgba(20, 30, 60, 0.8) !important; }
    [data-baseweb="slider"] input { color: #e0f2fe !important; }
    .stCaption { color: #a0d9ff !important; }
    .stDivider { border-color: #7c3aed !important; }
    .stSubheader { color: #00ffff !important; text-shadow: 0 0 10px rgba(0, 255, 255, 0.3); }
    </style>
    """,
    unsafe_allow_html=True,
)


ENGINE = SimulationEngine(PLANETS)


def customize_scenario(preset):
    """프리셋을 시작점으로 사용자가 값을 더 조정할 수 있게 한다."""
    kind, params, suffix = preset["type"], preset["params"], preset["id"]
    if kind == ScenarioType.SUN_MASS.value:
        change = st.sidebar.slider("태양 질량 변화율", -90.0, 100.0,
                                   float(params["percent_change"]), 0.5,
                                   format="%+.1f%%", key=f"sun-{suffix}")
        return ENGINE.scenario_sun_mass_change(change)
    if kind == ScenarioType.EARTH_MASS.value:
        change = st.sidebar.slider("지구 질량 변화율", -90.0, 100.0,
                                   float(params["percent_change"]), 0.5,
                                   format="%+.1f%%", key=f"earth-{suffix}")
        return ENGINE.scenario_earth_mass_change(change)
    if kind == ScenarioType.BLACKHOLE.value:
        mass = st.sidebar.slider("블랙홀 질량 (태양 = 1)", 1.0, 100.0,
                                 float(params["mass_solar"]), 1.0, key=f"bh-m-{suffix}")
        distance = st.sidebar.slider("지구와의 거리 (AU)", 0.1, 10.0,
                                     float(params["distance_au"]), 0.1, key=f"bh-d-{suffix}")
        return ENGINE.scenario_blackhole_nearby(mass, distance)
    if kind == ScenarioType.SIRIUS.value:
        distance = st.sidebar.slider("지구와의 거리 (AU)", 0.2, 20.0,
                                     float(params["distance_au"]), 0.1, key=f"sirius-{suffix}")
        # NASA 값: 시리우스 A 질량 2.063 태양질량, 광도 24.7 태양광도
        return ENGINE.scenario_sirius_nearby(distance_au=distance, mass_solar=2.063, luminosity_solar=24.7)
    if kind == ScenarioType.EARTH_DISTANCE.value:
        change = st.sidebar.slider("궤도 반지름 변화율", -80.0, 100.0,
                                   float(params["distance_change_pct"]), 0.5,
                                   format="%+.1f%%", key=f"dist-{suffix}")
        return ENGINE.scenario_earth_distance(change)
    if kind == ScenarioType.EARTH_ROTATION.value:
        hours = st.sidebar.slider("하루 길이 (시간)", 1.0, 120.0,
                                  float(params["hours_per_day"]), 0.5, key=f"rot-{suffix}")
        return ENGINE.scenario_earth_rotation(hours)
    if kind == ScenarioType.SOLAR_LUMINOSITY.value:
        change = st.sidebar.slider("태양 광도 변화율", -90.0, 100.0,
                                   float(params["luminosity_change_pct"]), 0.5,
                                   format="%+.1f%%", key=f"lum-{suffix}")
        return ENGINE.scenario_solar_luminosity(change)
    if kind == ScenarioType.EARTH_ALBEDO.value:
        change = st.sidebar.slider("반사율 변화율", -90.0, 100.0,
                                   float(params["albedo_change_pct"]), 0.5,
                                   format="%+.1f%%", key=f"alb-{suffix}")
        return ENGINE.scenario_earth_albedo(change)
    if kind == ScenarioType.ATMOSPHERE_LOSS.value:
        pct = st.sidebar.slider("대기 잔존율", 0.0, 100.0,
                                float(params["atmosphere_remaining_pct"]), 1.0,
                                format="%.0f%%", key=f"atm-{suffix}")
        return ENGINE.scenario_atmosphere_loss(pct)
    if kind == ScenarioType.MAGNETIC_FIELD.value:
        pct = st.sidebar.slider("자기장 강도", 0.0, 100.0,
                                float(params["field_strength_pct"]), 1.0,
                                format="%.0f%%", key=f"mag-{suffix}")
        return ENGINE.scenario_magnetic_field(pct)


def risk_score(scenario) -> int:
    """화면 비교를 위한 교육용 상대 위험 지수."""
    kind = scenario["type"]
    if kind == ScenarioType.SUN_MASS.value:
        return min(100, int(abs(scenario["percent_change"]) * 4))
    if kind == ScenarioType.EARTH_MASS.value:
        return min(100, int(abs(scenario["percent_change"]) * 3))
    if kind == ScenarioType.BLACKHOLE.value:
        gravity = scenario["results"]["gravity_ratio_to_sun_at_1au"]
        return min(100, max(5, int(35 + 25 * np.log10(max(gravity, 0.1)))))
    if kind == ScenarioType.SIRIUS.value:
        radiation = scenario["results"]["radiation_ratio_to_earth"]
        return min(100, max(5, int(30 + 30 * np.log10(max(radiation, 0.1)))))
    if kind == ScenarioType.EARTH_DISTANCE.value:
        change = abs(scenario["percent_change"])
        return min(100, int(30 + change * 0.5))
    if kind == ScenarioType.EARTH_ROTATION.value:
        hours = scenario["hours_per_day"]
        return min(100, int(30 + abs(hours - 24) * 1.5))
    if kind == ScenarioType.SOLAR_LUMINOSITY.value:
        change = abs(scenario["percent_change"])
        return min(100, int(30 + change * 0.6))
    if kind == ScenarioType.EARTH_ALBEDO.value:
        change = abs(scenario["albedo_change_pct"])
        return min(100, int(20 + change * 0.8))
    if kind == ScenarioType.ATMOSPHERE_LOSS.value:
        loss = 100 - scenario["atmosphere_remaining_pct"]
        return min(100, int(loss * 0.8))
    if kind == ScenarioType.MAGNETIC_FIELD.value:
        loss = 100 - scenario["field_strength_pct"]
        return min(100, int(loss * 0.7))
    return 50


def scenario_metrics(scenario):
    kind, results = scenario["type"], scenario["results"]
    if kind == ScenarioType.SUN_MASS.value:
        earth = results["Earth"]
        # 모델 A: 태양이 원래부터 그 질량 (케플러 3법칙, 원궤도 유지)
        model_a = scenario.get("orbit_model_a", {})
        period_ratio_a = model_a.get("period_ratio", 1.0)

        # 모델 B: 태양이 갑자기 질량 변화 (지구 속도 고정, 궤도 변형)
        model_b = scenario.get("orbit_model_b", {})

        if model_b.get("escape"):
            return [
                ("⚠️ 궤도 이탈 (모델 B)", "태양 질량 급감 시: 지구 탈출 속도 도달"),
                ("이심률", "1.0 (포물선)"),
                ("원일점", "∞ (무한원점)"),
                ("참고", f"모델 A: 원궤도 유지 시 주기 {period_ratio_a*100-100:+.2f}% (μ > 0이면 항상 계산 가능)"),
            ]
        else:
            a_ratio = model_b.get("a_ratio")
            eccentricity = model_b.get("eccentricity")
            period_ratio_b = model_b.get("period_ratio")

            # 음수 방지 (a_ratio가 음수면 탈출로 분류되어야 함)
            a_ratio_str = f"{a_ratio:.3f}배" if a_ratio is not None and a_ratio > 0 else "정의 불가"

            return [
                ("모델 A (원궤도 유지)", f'새 주기: {period_ratio_a:.3f}배'),
                ("모델 B (속도 고정)", f'새 장반경: {a_ratio_str}, 이심률: {eccentricity:.3f}'),
                ("모델 B 새 주기", f'{period_ratio_b:.3f}배'),
            ]
    if kind == ScenarioType.EARTH_MASS.value:
        return [
            ("표면 중력 변화", f'{results["surface_gravity_change_pct"]:+.2f}%'),
            ("새 상대 중력", f'{results["surface_gravity_new"]:.3f} g'),
            ("지구 질량", f'{scenario["percent_change"]:+.1f}%'),
        ]
    if kind == ScenarioType.BLACKHOLE.value:
        return [
            ("상대 중력", f'{results["gravity_ratio_to_sun_at_1au"]:.2f}배'),
            ("상대 조석력", f'{results["tidal_ratio_to_sun_at_1au"]:.2f}배'),
            ("사건지평선 반지름", f'{results["schwarzschild_radius_km"]:.1f} km'),
        ]
    if kind == ScenarioType.SIRIUS.value:
        return [
            ("상대 중력", f'{results["gravity_ratio_to_sun_at_1au"]:.2f}배'),
            ("복사 에너지", f'{results["radiation_ratio_to_earth"]:.1f}배'),
            ("단순 추정 온도", f'{results["estimated_earth_temp_c"]:.0f}°C'),
        ]
    if kind == ScenarioType.EARTH_DISTANCE.value:
        return [
            ("복사 에너지 비율", f'{results["radiation_ratio_to_earth"]:.4f}배'),
            ("추정 온도", f'{results["estimated_earth_temp_c"]:.0f}°C'),
            ("궤도 변화", f'{scenario["percent_change"]:+.1f}%'),
        ]
    if kind == ScenarioType.EARTH_ROTATION.value:
        # 유효중력이 음수인 붕괴 조건 확인
        if results.get("is_collapse_condition"):
            hours = scenario["hours_per_day"]
            g_eff = results["effective_gravity_ms2"]
            # 임계값: T_crit = 2π√(R/g) ≈ 1.40652시간
            t_crit = 2.0 * np.pi * np.sqrt(6.371e6 / 9.81) / 3600.0
            return [
                ("⚠️ 붕괴 조건", "지구가 형태를 유지할 수 없습니다"),
                ("하루 길이", f'{hours:.1f}시간 (< {t_crit:.3f}시간)'),
                ("유효중력", f'{g_eff:.2f} m/s² (음수)'),
            ]
        else:
            return [
                ("하루 길이", f'{scenario["hours_per_day"]:.1f}시간'),
                ("변화율", f'{results["rotation_change_pct"]:+.1f}%'),
                ("시간 변화", f'{results["day_length_change_hours"]:+.1f}시간'),
            ]
    if kind == ScenarioType.SOLAR_LUMINOSITY.value:
        return [
            ("광도 변화", f'{scenario["percent_change"]:+.1f}%'),
            ("광도 비율", f'{results["luminosity_ratio"]:.3f}배'),
            ("추정 온도", f'{results["estimated_earth_temp_c"]:.0f}°C'),
        ]
    if kind == ScenarioType.EARTH_ALBEDO.value:
        return [
            ("반사율 변화", f'{scenario["albedo_change_pct"]:+.1f}%'),
            ("새 반사율", f'{results["albedo_value"]:.3f}'),
            ("추정 온도", f'{results["estimated_earth_temp_c"]:.0f}°C'),
        ]
    if kind == ScenarioType.ATMOSPHERE_LOSS.value:
        return [
            ("대기 잔존율", f'{scenario["atmosphere_remaining_pct"]:.0f}%'),
            ("온도 감소", f'{results["temp_reduction_k"]:.1f}K'),
            ("추정 온도", f'{results["estimated_earth_temp_c"]:.0f}°C'),
        ]
    if kind == ScenarioType.MAGNETIC_FIELD.value:
        return [
            ("자기장 강도", f'{scenario["field_strength_pct"]:.0f}%'),
            ("태양풍 증가", f'{results["solar_wind_increase"]:+.1f}배'),
            ("상태", results["primary_risk"]),
        ]
    return [("시나리오 타입", kind)]


def animated_scene(scenario, speed_label: str, paused: bool):
    """행성 공전과 외부 천체 영향을 CSS 애니메이션으로 보여준다."""
    kind = scenario["type"]
    speed_scale = {"느리게": 1.6, "보통": 1.0, "빠르게": 0.55}[speed_label]
    sun_scale, earth_scale = 1.0, 1.0
    # 태양 질량 변화 시 케플러 3법칙에 따른 주기 배율 적용
    period_ratio = scenario.get("period_ratio", 1.0)

    # 기본 공전주기 (초)
    base_durations = [4.0, 6.5, 9.0, 13.0, 18.0, 23.0, 29.0, 36.0]
    # 현재 조건에서의 실제 주기 계산
    durations = [b * period_ratio * speed_scale for b in base_durations]
    # 시간 기반 delay: 각 궤도가 이미 진행 중인 상태에서 시작 (rerun해도 위상이 연속)
    now = time.time()
    delays = [-(now % d) for d in durations]

    system_class, intruder_html, callout = "", "", "행성들이 태양 주위를 공전합니다."

    if kind == ScenarioType.SUN_MASS.value:
        sun_scale = max(0.65, min(1.55, 1 + scenario["percent_change"] / 150))
        callout = f'태양 질량 {scenario["percent_change"]:+.1f}% · 공전 속도와 1년의 길이가 달라집니다.'
    elif kind == ScenarioType.EARTH_MASS.value:
        earth_scale = max(0.65, min(1.55, 1 + scenario["percent_change"] / 120))
        callout = f'지구 질량 {scenario["percent_change"]:+.1f}% · 지구의 크기 변화는 이해를 돕기 위한 표현입니다.'
    elif kind == ScenarioType.BLACKHOLE.value:
        system_class = "disturbed"
        mass = scenario["assumptions"]["mass_solar"]
        distance = scenario["assumptions"]["distance_au"]
        intruder_html = (
            '<div class="pull-line"></div><div class="intruder blackhole"><span>블랙홀</span></div>'
        )
        callout = f'{mass:g} 태양질량 블랙홀 · 거리 {distance:g} AU · 태양계 전체가 강하게 끌립니다.'
    elif kind == ScenarioType.SIRIUS.value:
        system_class = "heated"
        distance = scenario["assumptions"]["distance_au"]
        intruder_html = (
            '<div class="heat-wave wave-one"></div><div class="heat-wave wave-two"></div>'
            '<div class="intruder sirius"><span>시리우스 A</span></div>'
        )
        callout = f'시리우스 A · 거리 {distance:g} AU · 지구가 받는 빛과 열이 강해집니다.'
    elif kind == ScenarioType.EARTH_DISTANCE.value:
        system_class = "heated"
        change = scenario["percent_change"]
        if change > 0:
            callout = f'궤도 {change:+.1f}% · 태양에서 멀어져 추워집니다.'
        else:
            callout = f'궤도 {change:+.1f}% · 태양에 가까워져 더워집니다.'
    elif kind == ScenarioType.EARTH_ROTATION.value:
        hours = scenario.get("hours_per_day", 24)
        callout = f'하루 길이 {hours:.1f}시간 · 낮과 밤의 길이가 변합니다.'
    elif kind == ScenarioType.SOLAR_LUMINOSITY.value:
        system_class = "heated" if scenario["percent_change"] > 0 else ""
        change = scenario["percent_change"]
        callout = f'태양 광도 {change:+.1f}% · 지구가 받는 복사 에너지가 변합니다.'
    elif kind == ScenarioType.EARTH_ALBEDO.value:
        change = scenario["albedo_change_pct"]
        if change > 0:
            callout = f'반사율 {change:+.1f}% · 지표가 더 밝아져 추워집니다.'
        else:
            callout = f'반사율 {change:+.1f}% · 지표가 어두워져 더워집니다.'
    elif kind == ScenarioType.ATMOSPHERE_LOSS.value:
        pct = scenario["atmosphere_remaining_pct"]
        callout = f'대기 {pct:.0f}% 잔존 · 대기 감소로 온도와 보호력이 변합니다.'
    else:  # MAGNETIC_FIELD
        pct = scenario["field_strength_pct"]
        if pct >= 90:
            callout = f'자기장 {pct:.0f}% · 정상적인 자기장이 태양풍을 차단합니다.'
        elif pct >= 50:
            callout = f'자기장 {pct:.0f}% · 약화된 자기장이 부분적으로만 보호합니다.'
        else:
            callout = f'자기장 {pct:.0f}% · 거의 없는 자기장은 태양풍을 막지 못합니다.'

    pause_class = "paused" if paused else ""
    # 각 궤도의 duration과 delay를 시간 기반으로 동적 계산
    orbit_html_lines = []
    planet_names = ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"]
    planet_display_names = ["수성", "금성", "지구", "화성", "목성", "토성", "천왕성", "해왕성"]

    for i, (planet, display_name) in enumerate(zip(planet_names, planet_display_names)):
        is_earth = (i == 2)
        earth_scale_css = f"--earth-scale:{earth_scale:.2f}" if is_earth else ""
        planet_css = f'style="{earth_scale_css}"' if is_earth else ""

        orbit_html_lines.append(
            f'        <div class="orbit orbit-{i+1}" style="--duration:{durations[i]:.2f}s;--delay:{delays[i]:.2f}s" data-base-duration="{base_durations[i]}">'
            f'\n          <div class="planet {planet}" {planet_css}><span style="animation-duration:{durations[i]:.2f}s;animation-delay:{delays[i]:.2f}s">{display_name}</span></div>'
            f'\n        </div>'
        )

    orbit_html = '\n'.join(orbit_html_lines)

    html = f"""
    <div class="space {pause_class}">
      <div class="guide">{callout}</div>
      <div class="system {system_class}">
        <div class="sun" style="--sun-scale:{sun_scale:.2f}"><span>태양</span></div>
{orbit_html}
      </div>
      {intruder_html}
      <div class="scale-note">움직임과 행성 크기는 이해를 돕기 위한 표현이며 실제 비율과 다릅니다.</div>
    </div>
    <style>
      * {{ box-sizing: border-box; }}
      .space {{
        position: relative; height: 520px; overflow: hidden; border-radius: 8px;
        background-color: #111b25; border: 5px solid #fffdf8; outline: 1px solid #cfc5b6; color: #f5f1e8;
        background-image: radial-gradient(circle at 12% 18%, #8090a8 1px, transparent 1.5px),
                          radial-gradient(circle at 72% 31%, #8090a8 1px, transparent 1.5px),
                          radial-gradient(circle at 42% 77%, #8090a8 1px, transparent 1.5px);
        background-size: 95px 85px, 135px 110px, 165px 130px;
      }}
      .guide {{ position:absolute; left:20px; top:18px; z-index:20; color:#e8e1d4; font-size:14px; }}
      .system {{ position:absolute; width:430px; height:430px; left:50%; top:52%; transform:translate(-50%,-50%); }}
      .system.disturbed {{ left:36%; animation: tug 2.8s ease-in-out infinite alternate; }}
      .system.heated {{ left:39%; }}
      .sun {{
        position:absolute; width:48px; height:48px; left:50%; top:50%; border-radius:50%;
        background:#ffd166; border:3px solid rgba(255,236,170,.6);
        transform:translate(-50%,-50%) scale(var(--sun-scale)); box-shadow:0 0 24px rgba(255,209,102,.55); z-index:8;
      }}
      .sun span {{ position:absolute; width:70px; left:-11px; top:54px; text-align:center; color:#ffd166; font-size:12px; }}
      .orbit {{
        position:absolute; left:50%; top:50%; border:1px solid #405266; border-radius:50%;
        transform:translate(-50%,-50%); animation: spin var(--duration) linear infinite; animation-delay: var(--delay, 0s);
      }}
      .orbit-1 {{ width:78px; height:78px; }}
      .orbit-2 {{ width:116px; height:116px; }}
      .orbit-3 {{ width:158px; height:158px; }}
      .orbit-4 {{ width:200px; height:200px; }}
      .orbit-5 {{ width:246px; height:246px; }}
      .orbit-6 {{ width:288px; height:288px; }}
      .orbit-7 {{ width:334px; height:334px; }}
      .orbit-8 {{ width:382px; height:382px; }}
      .planet {{ position:absolute; left:50%; top:-7px; border-radius:50%; transform:translateX(-50%); }}
      .planet span {{
        position:absolute; top:-21px; left:50%; transform:translateX(-50%); color:#e2ddd2;
        font-size:11px; white-space:nowrap; animation: counter-spin var(--duration) linear infinite;
      }}
      .mercury {{ width:9px; height:9px; background:#b6a48b; }}
      .venus {{ width:13px; height:13px; background:#e9c46a; }}
      .earth {{ width:16px; height:16px; background:#4f93e8; border:2px solid #b9dcff; transform:translateX(-50%) scale(var(--earth-scale)); }}
      .mars {{ width:12px; height:12px; background:#f07b62; }}
      .jupiter {{ width:24px; height:24px; top:-12px; background:#d6a979; border:2px solid #efcda8; }}
      .saturn {{ width:21px; height:21px; top:-11px; background:#e1c48c; border:1px solid #f6dda8; }}
      .saturn::after {{ content:""; position:absolute; width:35px; height:10px; left:50%; top:50%; transform:translate(-50%,-50%) rotate(-12deg); border:2px solid #e1c48c; border-radius:50%; }}
      .uranus {{ width:17px; height:17px; top:-9px; background:#75c6d9; border:1px solid #c0eff7; }}
      .neptune {{ width:17px; height:17px; top:-9px; background:#6687e8; border:1px solid #b6c7ff; }}
      .intruder {{ position:absolute; right:9%; top:49%; transform:translateY(-50%); z-index:12; }}
      .intruder span {{ position:absolute; top:70px; left:50%; transform:translateX(-50%); white-space:nowrap; font-size:12px; }}
      .blackhole {{ width:70px; height:70px; border-radius:50%; background:#010205; border:3px solid #ff6678; box-shadow:0 0 0 12px rgba(255,102,120,.12); animation:pulse 1.8s ease-in-out infinite; }}
      .blackhole span {{ color:#ff8290; }}
      .sirius {{ width:68px; height:68px; border-radius:50%; background:#fff0a6; border:3px solid #ffb45e; box-shadow:0 0 28px rgba(255,180,94,.75); animation:pulse 1.5s ease-in-out infinite; }}
      .sirius span {{ color:#ffcb8d; }}
      .pull-line {{ position:absolute; left:51%; right:15%; top:50%; height:2px; background:#ff6678; opacity:.55; animation:pull 1.3s ease-in-out infinite; }}
      .heat-wave {{ position:absolute; right:5%; top:50%; width:120px; height:120px; border:2px solid #ffb45e; border-radius:50%; transform:translateY(-50%); opacity:.35; animation:wave 2s ease-out infinite; }}
      .wave-two {{ animation-delay:1s; }}
      .scale-note {{ position:absolute; left:20px; bottom:14px; z-index:20; color:#aeb6bd; font-size:11px; }}
      .paused *, .paused *::before, .paused *::after {{ animation-play-state: paused !important; }}
      @keyframes spin {{ to {{ transform:translate(-50%,-50%) rotate(360deg); }} }}
      @keyframes counter-spin {{ to {{ transform:translateX(-50%) rotate(-360deg); }} }}
      @keyframes tug {{ from {{ transform:translate(-54%,-50%) rotate(-1deg); }} to {{ transform:translate(-46%,-50%) rotate(2deg); }} }}
      @keyframes pulse {{ 50% {{ transform:translateY(-50%) scale(1.08); }} }}
      @keyframes pull {{ 50% {{ opacity:.95; transform:scaleX(1.05); transform-origin:right; }} }}
      @keyframes wave {{ from {{ transform:translateY(-50%) scale(.5); opacity:.45; }} to {{ transform:translateY(-50%) scale(2.5); opacity:0; }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation-duration: .001ms !important; animation-iteration-count: 1 !important; }} }}
    </style>
    <script>
      (function() {{
        const orbits = document.querySelectorAll('.orbit[data-base-duration]');
        const t = (Date.now() / 1000) % 3600; // 시간 기반 위상 (3600초 주기)
        orbits.forEach(orbit => {{
          const duration = parseFloat(getComputedStyle(orbit).getPropertyValue('--duration').match(/[0-9.]+/)[0]);
          if (duration > 0) {{
            const delay = -((t % duration) - duration);
            orbit.style.setProperty('--delay', delay.toFixed(2) + 's');
          }}
        }});
      }})();
    </script>
    """
    st.html(html)


st.markdown('<div class="hero-kicker">중학생 과학 시뮬레이션</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">태양계, 만약에?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-copy">행성과 별의 조건을 바꾸며 결과를 관찰하는 가상 우주 실험입니다.</div>',
    unsafe_allow_html=True,
)

st.sidebar.header("실험 설정")
st.sidebar.markdown(
    "**사용 순서**  \n"
    "1. 실험 유형을 고릅니다.  \n"
    "2. 원하는 상황을 고릅니다.  \n"
    "3. 움직임을 보고 쉬운 해설을 읽습니다."
)
category = st.sidebar.selectbox(
    "시나리오 유형",
    list(CATEGORY_LABELS),
    index=2,
    format_func=lambda value: CATEGORY_LABELS[value],
)
custom_mode = st.sidebar.toggle("조건 직접 조정", value=False)
available_presets = presets_for(category)
default_index = 8 if category == ScenarioType.BLACKHOLE.value else 0
preset = st.sidebar.selectbox(
    "시나리오 프리셋",
    available_presets,
    index=min(default_index, len(available_presets) - 1),
    format_func=lambda item: item["title"],
    disabled=custom_mode,
)
if custom_mode:
    st.sidebar.caption("👆 직접 조정 중")
else:
    st.sidebar.caption(f"전체 {len(SCENARIO_PRESETS)}개 중 {len(available_presets)}개 표시")
scenario = customize_scenario(preset) if custom_mode else run_preset(ENGINE, preset)
selected_type = ScenarioType(category)
st.sidebar.divider()
st.sidebar.subheader("애니메이션")
animation_speed = st.sidebar.segmented_control(
    "움직임 속도", ["느리게", "보통", "빠르게"], default="보통"
)
pause_animation = st.sidebar.toggle("움직임 멈추기", value=False)
st.sidebar.divider()
st.sidebar.markdown("<span class='safe-note'>가상 실험이며 실제 발생 가능성을 예측하지 않습니다.</span>",
                    unsafe_allow_html=True)

left, right = st.columns([1.55, 1], gap="large")
with left:
    st.subheader(scenario["scenario"])
    animated_scene(scenario, animation_speed or "보통", pause_animation)

with right:
    score = risk_score(scenario)
    st.subheader("실험 결과")
    st.markdown(
        f'<div class="result-card danger-card"><div class="eyebrow">현재 실험의 변화 정도</div>'
        f'<div class="big-result">{score} / 100</div></div>',
        unsafe_allow_html=True,
    )
    st.progress(score / 100)
    for label, value in scenario_metrics(scenario):
        st.metric(label, value)

st.divider()
explain_tab, note_tab = st.tabs(["쉬운 해설", "과학적 가정"])
with explain_tab:
    if "explanations" not in st.session_state:
        st.session_state.explanations = {}
    scenario_key = repr(scenario)
    explanation = st.session_state.explanations.get(scenario_key, fallback_interpretation(scenario))
    st.markdown(f'<div class="result-card">{explanation}</div>', unsafe_allow_html=True)
    ai = AIInterpreter()
    if ai.client:
        if st.button("설명을 더 쉽게 바꾸기", type="primary"):
            with st.spinner("계산 결과를 쉬운 말로 정리하고 있어요..."):
                ai_text = ai.interpret_scenario(scenario)
            if ai_text:
                st.session_state.explanations[scenario_key] = ai_text
                st.rerun()
            st.warning("AI 연결에 실패해 기본 해설을 유지합니다.")

with note_tab:
    limitations = scenario.get("limitations")
    if limitations:
        st.info(limitations)
    elif selected_type == ScenarioType.SUN_MASS:
        st.info("행성의 현재 거리와 궤도 모양은 고정하고 태양 질량만 바꾼 단순 모델입니다.")
    else:
        st.info("지구의 반지름은 고정하고 질량만 바꾼 단순 모델입니다.")
    st.caption("위험 지수는 과학 단위가 아니라 여러 시나리오를 쉽게 비교하기 위한 교육용 값입니다.")
