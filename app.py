"""직접 조작하는 태양계 WHAT IF Streamlit 앱."""

from io import BytesIO
from pathlib import Path
import time

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
import streamlit as st

from solar_system_sim_v2_openai import (
    AIInterpreter,
    PLANETS,
    ScenarioType,
    SimulationEngine,
    fallback_interpretation,
)
from scenario_catalog import CATEGORY_LABELS, SCENARIO_PRESETS, presets_for, run_preset


def configure_korean_matplotlib_font() -> str | None:
    """AppleGothic을 우선 적용하고 NanumGothic으로 폴백한다."""
    font_candidates = [
        ("AppleGothic", Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")),
        ("NanumGothic", Path("/Library/Fonts/NanumGothic.ttf")),
    ]
    for family, font_path in font_candidates:
        try:
            if font_path.exists():
                font_manager.fontManager.addfont(str(font_path))
            font_manager.findfont(family, fallback_to_default=False)
            matplotlib.rcParams["font.family"] = family
            matplotlib.rcParams["axes.unicode_minus"] = False
            return None
        except (FileNotFoundError, ValueError, RuntimeError):
            continue
    matplotlib.rcParams["axes.unicode_minus"] = False
    return "AppleGothic과 NanumGothic을 찾지 못해 그래프 한글 폰트를 적용하지 못했습니다."


MATPLOTLIB_FONT_WARNING = configure_korean_matplotlib_font()


st.set_page_config(
    page_title="태양계 WHAT IF 실험실",
    layout="wide",
    initial_sidebar_state="expanded",
)

if MATPLOTLIB_FONT_WARNING:
    st.warning(MATPLOTLIB_FONT_WARNING)

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
    .validation-table { width:100%; table-layout:fixed; border-collapse:collapse; background:rgba(20,30,60,.72); font-size:.86rem; }
    .validation-table th, .validation-table td { border:1px solid #52617a; padding:9px 8px; color:#e0f2fe; white-space:normal; overflow-wrap:anywhere; vertical-align:top; }
    .validation-table th { color:#00ffff; background:rgba(124,58,237,.28); }
    .validation-table th:nth-child(1) { width:17%; } .validation-table th:nth-child(2) { width:12%; }
    .validation-table th:nth-child(3) { width:12%; } .validation-table th:nth-child(4) { width:15%; }
    .validation-table th:nth-child(5) { width:44%; }
    </style>
    """,
    unsafe_allow_html=True,
)


ENGINE = SimulationEngine(PLANETS)


ASSUMPTIONS = {
    ScenarioType.SUN_MASS.value: (
        "**사용 공식:** $e=|\\mu-1|/\\mu$, $\\mu=M'/M$  \n"
        "**고정/변경:** 지구의 순간 위치(1 AU)와 속도는 고정하고 태양 질량만 바꿉니다.  \n"
        "**무시:** 행성 간 상호 중력, 태양 질량 변화 과정, 장기 섭동은 무시합니다."
    ),
    ScenarioType.EARTH_MASS.value: (
        "**사용 공식:** $g'/g=(M'/M)(R/R')^2$  \n"
        "**고정/변경:** 지구 반지름은 고정하고 지구 질량만 바꿉니다.  \n"
        "**무시:** 질량 변화에 따른 반지름·밀도·내부 구조 변화는 무시합니다."
    ),
    ScenarioType.BLACKHOLE.value: (
        "**사용 공식:** $F/F_\\odot=(M/M_\\odot)/(r/\\mathrm{AU})^2$, $F_t/F_{t,\\odot}=(M/M_\\odot)/(r/\\mathrm{AU})^3$, $R_s=2GM/c^2$  \n"
        "**고정/변경:** 비교 기준은 1 AU의 태양이며 블랙홀 질량과 거리만 바꿉니다.  \n"
        "**무시:** 접근 방향·속도, 강착원반, 다체 운동은 무시합니다."
    ),
    ScenarioType.SIRIUS.value: (
        "**사용 공식:** $F/F_\\odot=(M/M_\\odot)/r^2$, $S_*/S_\\odot=(L_*/L_\\odot)/r^2$, $T=288(1+S_*/S_\\odot)^{1/4}$  \n"
        "**고정/변경:** 시리우스 A의 질량·광도는 고정하고 지구와의 거리만 바꿉니다.  \n"
        "**무시:** 대기·해양 순환, 스펙트럼 차이, 다체 궤도는 무시합니다."
    ),
    ScenarioType.EARTH_DISTANCE.value: (
        "**사용 공식:** $S/S_0=(r_0/r)^2$, $T_s=278.5(1-A)^{1/4}/\\sqrt d+33.9$  \n"
        "**고정/변경:** 태양 광도·지구 반사율·대기는 고정하고 공전 거리만 바꿉니다.  \n"
        "**무시:** 궤도 이심률, 계절, 기후 되먹임과 해양 순환은 무시합니다."
    ),
    ScenarioType.EARTH_ROTATION.value: (
        "**사용 공식:** $\\omega=2\\pi/T$, $g_{eff}=g-\\omega^2R_E$  \n"
        "**고정/변경:** 지구 반지름과 표면중력은 고정하고 하루 길이만 바꿉니다.  \n"
        "**무시:** 지구의 변형, 대기 순환, 조석과 자전축 변화는 무시합니다."
    ),
    ScenarioType.SOLAR_LUMINOSITY.value: (
        "**사용 공식:** $T_s=278.5L^{1/4}(1-A)^{1/4}/\\sqrt d+33.9$  \n"
        "**고정/변경:** 지구 거리·반사율·대기는 고정하고 태양 광도만 바꿉니다.  \n"
        "**무시:** 구름·빙하·수증기 되먹임과 대기 순환은 무시합니다."
    ),
    ScenarioType.EARTH_ALBEDO.value: (
        "**사용 공식:** $T_s=278.5(1-A)^{1/4}+33.9$  \n"
        "**고정/변경:** 태양 광도·지구 거리·대기는 고정하고 반사율 $A$만 바꿉니다.  \n"
        "**온실효과:** 지표 온도는 유효 복사 온도에 온실효과 +33.9 K를 상수로 더해 구합니다(현재 지구의 288 K - 254 K에서 얻은 값).  \n"
        "**무시:** 반사율 변화에 따른 온실효과의 되먹임, 구름과 얼음의 공간 분포, 대기 순환은 무시합니다."
    ),
    ScenarioType.ATMOSPHERE_LOSS.value: (
        "**사용 공식:** $T_s=T_e+33.9f_{atm}$  \n"
        "**고정/변경:** 복사평형 조건은 고정하고 대기 잔존 비율만 바꿉니다.  \n"
        "**무시:** 기체 조성·기압 변화, 구름, 비선형 온실효과는 무시합니다."
    ),
    ScenarioType.MAGNETIC_FIELD.value: (
        "**사용 공식:** $W/W_0=1+2(1-B/B_0)$  \n"
        "**고정/변경:** 태양풍 세기는 고정하고 지구 자기장 강도만 바꿉니다.  \n"
        "**무시:** 자기권 형상, 태양폭풍, 대기와 자기장의 장기 상호작용은 무시합니다."
    ),
}


def format_number(value: float, kind: str) -> str:
    """대회 화면 전체에서 사용하는 유효숫자 규칙."""
    if kind == "multiple":
        return f"{value:.2f}배"
    if kind == "percent":
        return f"{value:+.1f}%"
    if kind == "temperature":
        return f"{value:.0f}°C"
    if kind == "length":
        return f"{value:.3g} km"
    raise ValueError(f"지원하지 않는 표시 형식: {kind}")


def _bounded_impact(magnitude: float) -> float:
    """0 이상의 영향 크기를 포화형 공통 척도 0~100으로 바꾼다."""
    return 100 * (1 - np.exp(-max(0.0, float(magnitude))))


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
    """지구 거주 가능성에 대한 물리적 영향을 공통 0~100 척도로 환산한다."""
    kind, results = scenario["type"], scenario["results"]
    baseline_temp_c = ENGINE._calculate_earth_temperature() - 273.15

    def temperature_impact(temp_c: float) -> float:
        return _bounded_impact(abs(temp_c - baseline_temp_c) / 20)

    if kind == ScenarioType.SUN_MASS.value:
        orbit = scenario["orbit_model_b"]
        if orbit.get("escape"):
            return 100
        return round(_bounded_impact(3 * orbit["eccentricity"]))
    if kind == ScenarioType.EARTH_MASS.value:
        gravity_ratio = results["surface_gravity_new"]
        return round(_bounded_impact(abs(np.log(gravity_ratio)) / np.log(2)))
    if kind == ScenarioType.BLACKHOLE.value:
        perturbation = max(results["gravity_ratio_to_sun_at_1au"], results["tidal_ratio_to_sun_at_1au"])
        return round(_bounded_impact(perturbation))
    if kind == ScenarioType.SIRIUS.value:
        return round(max(
            temperature_impact(results["estimated_earth_temp_c"]),
            _bounded_impact(results["gravity_ratio_to_sun_at_1au"]),
        ))
    if kind == ScenarioType.EARTH_DISTANCE.value:
        return round(temperature_impact(results["estimated_earth_temp_c"]))
    if kind == ScenarioType.EARTH_ROTATION.value:
        baseline_gravity = ENGINE.scenario_earth_rotation(24)["results"]["effective_gravity_ms2"]
        day_impact = abs(np.log(scenario["hours_per_day"] / 24)) / np.log(2)
        gravity_impact = abs(results["effective_gravity_ms2"] - baseline_gravity) / baseline_gravity
        return round(_bounded_impact(max(day_impact, gravity_impact)))
    if kind == ScenarioType.SOLAR_LUMINOSITY.value:
        return round(temperature_impact(results["estimated_earth_temp_c"]))
    if kind == ScenarioType.EARTH_ALBEDO.value:
        return round(temperature_impact(results["estimated_earth_temp_c"]))
    if kind == ScenarioType.ATMOSPHERE_LOSS.value:
        return round(temperature_impact(results["estimated_earth_temp_c"]))
    if kind == ScenarioType.MAGNETIC_FIELD.value:
        wind_ratio_increase = results["solar_wind_increase"]
        return round(_bounded_impact(wind_ratio_increase))
    raise ValueError(f"지원하지 않는 시나리오 유형: {kind}")


def representative_score_table() -> pd.DataFrame:
    """유형별 대표 조건의 거주 가능성 영향 점수를 보여준다."""
    examples = [
        ("태양 질량", "-50%", ENGINE.scenario_sun_mass_change(-50)),
        ("지구 질량", "-50%", ENGINE.scenario_earth_mass_change(-50)),
        ("블랙홀", "10 M☉ · 1 AU", ENGINE.scenario_blackhole_nearby(10, 1)),
        ("시리우스 A", "1 AU", ENGINE.scenario_sirius_nearby(1, 2.063, 24.7)),
        ("지구 궤도", "-50%", ENGINE.scenario_earth_distance(-50)),
        ("자전", "하루 6시간", ENGINE.scenario_earth_rotation(6)),
        ("태양 광도", "-50%", ENGINE.scenario_solar_luminosity(-50)),
        ("지표 반사율", "-50%", ENGINE.scenario_earth_albedo(-50)),
        ("대기", "0% 잔존", ENGINE.scenario_atmosphere_loss(0)),
        ("자기장", "0%", ENGINE.scenario_magnetic_field(0)),
    ]
    return pd.DataFrame(
        [{"시나리오": name, "대표 조건": condition, "영향 점수": risk_score(value)} for name, condition, value in examples]
    )


def scenario_metrics(scenario):
    kind, results = scenario["type"], scenario["results"]
    if kind == ScenarioType.SUN_MASS.value:
        # 모델 B: 태양이 갑자기 질량 변화 (지구 속도 고정, 궤도 변형)
        model_b = scenario.get("orbit_model_b", {})

        if model_b.get("escape"):
            return [
                ("궤도 상태", "탈출", "급격한 질량 변화 모델"),
                ("이심률", "1.00" if np.isclose(1 + scenario["percent_change"] / 100, .5) else ">1.00", "포물선" if np.isclose(1 + scenario["percent_change"] / 100, .5) else "쌍곡선"),
                ("원일점", "∞", "무한원점"),
            ]
        else:
            a_ratio = model_b.get("a_ratio")
            eccentricity = model_b.get("eccentricity")
            period_ratio_b = model_b.get("period_ratio")

            # 음수 방지 (a_ratio가 음수면 탈출로 분류되어야 함)
            a_ratio_str = f"{a_ratio:.3f}배" if a_ratio is not None and a_ratio > 0 else "정의 불가"

            return [
                ("궤도 상태", "결합", "급격한 질량 변화 모델"),
                ("장반경", a_ratio_str, "현재 궤도 대비"),
                ("이심률", f'{eccentricity:.3f}', "타원 궤도"),
                ("공전 주기", format_number(period_ratio_b, "multiple"), "현재 1년 대비"),
            ]
    if kind == ScenarioType.EARTH_MASS.value:
        return [
            ("중력 변화", format_number(results["surface_gravity_change_pct"], "percent"), None),
            ("상대 중력", f'{results["surface_gravity_new"]:.3f} g', None),
            ("질량 변화", format_number(scenario["percent_change"], "percent"), None),
        ]
    if kind == ScenarioType.BLACKHOLE.value:
        return [
            ("상대 중력", format_number(results["gravity_ratio_to_sun_at_1au"], "multiple"), None),
            ("상대 조석력", format_number(results["tidal_ratio_to_sun_at_1au"], "multiple"), None),
            ("사건지평선", format_number(results["schwarzschild_radius_km"], "length"), "반지름"),
        ]
    if kind == ScenarioType.SIRIUS.value:
        return [
            ("상대 중력", format_number(results["gravity_ratio_to_sun_at_1au"], "multiple"), None),
            ("복사 에너지", format_number(results["radiation_ratio_to_earth"], "multiple"), None),
            ("추정 온도", format_number(results["estimated_earth_temp_c"], "temperature"), None),
        ]
    if kind == ScenarioType.EARTH_DISTANCE.value:
        return [
            ("복사 비율", format_number(results["radiation_ratio_to_earth"], "multiple"), None),
            ("추정 온도", format_number(results["estimated_earth_temp_c"], "temperature"), None),
            ("궤도 변화", format_number(scenario["percent_change"], "percent"), None),
        ]
    if kind == ScenarioType.EARTH_ROTATION.value:
        # 유효중력이 음수인 붕괴 조건 확인
        if results.get("is_collapse_condition"):
            hours = scenario["hours_per_day"]
            g_eff = results["effective_gravity_ms2"]
            # 임계값: T_crit = 2π√(R/g) ≈ 1.40652시간
            t_crit = 2.0 * np.pi * np.sqrt(6.371e6 / 9.81) / 3600.0
            return [
                ("자전 상태", "붕괴", "형태 유지 불가"),
                ("하루 길이", f'{hours:.1f}시간', f'임계 {t_crit:.3f}시간 미만'),
                ("유효중력", f'{g_eff:.2f} m/s²', "음수"),
            ]
        else:
            return [
                ("하루 길이", f'{scenario["hours_per_day"]:.1f}시간', None),
                ("변화율", format_number(results["rotation_change_pct"], "percent"), None),
                ("시간 변화", f'{results["day_length_change_hours"]:+.1f}시간', None),
            ]
    if kind == ScenarioType.SOLAR_LUMINOSITY.value:
        return [
            ("광도 변화", format_number(scenario["percent_change"], "percent"), None),
            ("광도 비율", format_number(results["luminosity_ratio"], "multiple"), None),
            ("추정 온도", format_number(results["estimated_earth_temp_c"], "temperature"), None),
        ]
    if kind == ScenarioType.EARTH_ALBEDO.value:
        return [
            ("반사율 변화", format_number(scenario["albedo_change_pct"], "percent"), None),
            ("새 반사율", f'{results["albedo_value"]:.3f}', None),
            ("추정 온도", format_number(results["estimated_earth_temp_c"], "temperature"), None),
        ]
    if kind == ScenarioType.ATMOSPHERE_LOSS.value:
        return [
            ("대기 잔존율", f'{scenario["atmosphere_remaining_pct"]:.1f}%', None),
            ("온도 감소", f'{results["temp_reduction_k"]:.1f} K', None),
            ("추정 온도", format_number(results["estimated_earth_temp_c"], "temperature"), None),
        ]
    if kind == ScenarioType.MAGNETIC_FIELD.value:
        return [
            ("자기장 강도", f'{scenario["field_strength_pct"]:.1f}%', None),
            ("태양풍 증가", format_number(results["solar_wind_increase"], "multiple"), None),
            ("상태", "위험" if scenario["field_strength_pct"] < 50 else "정상", results["primary_risk"]),
        ]
    return [("시나리오", kind, None)]


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
            f'\n          <div class="planet {planet}" {planet_css} aria-label="{display_name}"></div>'
            f'\n        </div>'
        )

    orbit_html = '\n'.join(orbit_html_lines)
    label_html = "\n".join(
        f'      <div class="planet-label" data-planet="{planet}">{name}</div>'
        for planet, name in zip(planet_names, planet_display_names)
    )

    html = f"""
    <div class="space {pause_class}">
      <div class="guide">{callout}</div>
      <div class="system {system_class}">
        <div class="sun" style="--sun-scale:{sun_scale:.2f}"><span>태양</span></div>
{orbit_html}
      </div>
{label_html}
      {intruder_html}
      <div class="scale-note">궤도 간격은 외행성까지 보이도록 압축한 비선형 표현입니다. 행성 크기도 실제 비율과 다릅니다.</div>
    </div>
    <style>
      * {{ box-sizing: border-box; }}
      .space {{
        position: relative; height: 540px; overflow: hidden; border-radius: 8px;
        background-color: #111b25; border: 5px solid #fffdf8; outline: 1px solid #cfc5b6; color: #f5f1e8;
        background-image: radial-gradient(circle at 12% 18%, #8090a8 1px, transparent 1.5px),
                          radial-gradient(circle at 72% 31%, #8090a8 1px, transparent 1.5px),
                          radial-gradient(circle at 42% 77%, #8090a8 1px, transparent 1.5px);
        background-size: 95px 85px, 135px 110px, 165px 130px;
        min-width: 900px;
      }}
      .guide {{ position:absolute; left:20px; top:18px; z-index:20; color:#e8e1d4; font-size:14px; }}
      .system {{ position:absolute; width:min(700px, 95%); aspect-ratio:1; left:50%; top:48%; transform:translate(-50%,-50%); }}
      .system.disturbed {{ left:38%; animation: tug 2.8s ease-in-out infinite alternate; }}
      .system.heated {{ left:40%; }}
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
      .orbit-1 {{ width:16.7%; height:16.7%; }}
      .orbit-2 {{ width:24.6%; height:24.6%; }}
      .orbit-3 {{ width:32.9%; height:32.9%; }}
      .orbit-4 {{ width:41.7%; height:41.7%; }}
      .orbit-5 {{ width:51.8%; height:51.8%; }}
      .orbit-6 {{ width:62.7%; height:62.7%; }}
      .orbit-7 {{ width:74.6%; height:74.6%; }}
      .orbit-8 {{ width:86.4%; height:86.4%; }}
      .planet {{ position:absolute; left:50%; top:-7px; border-radius:50%; transform:translateX(-50%); }}
      .planet-label {{ position:absolute; z-index:25; color:#e2ddd2; font-size:11px; line-height:15px; white-space:nowrap; pointer-events:none; }}
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
      .scale-note {{ position:absolute; left:14px; right:14px; bottom:10px; z-index:20; color:#aeb6bd; font-size:11px; line-height:1.35; padding:5px 7px; background:rgba(17,27,37,.9); border-radius:4px; }}
      .paused *, .paused *::before, .paused *::after {{ animation-play-state: paused !important; }}
      @keyframes spin {{ to {{ transform:translate(-50%,-50%) rotate(360deg); }} }}
      @keyframes tug {{ from {{ transform:translate(-54%,-50%) rotate(-1deg); }} to {{ transform:translate(-46%,-50%) rotate(2deg); }} }}
      @keyframes pulse {{ 50% {{ transform:translateY(-50%) scale(1.08); }} }}
      @keyframes pull {{ 50% {{ opacity:.95; transform:scaleX(1.05); transform-origin:right; }} }}
      @keyframes wave {{ from {{ transform:translateY(-50%) scale(.5); opacity:.45; }} to {{ transform:translateY(-50%) scale(2.5); opacity:0; }} }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation-duration: .001ms !important; animation-iteration-count: 1 !important; }} }}
    </style>
    <script>
      (function() {{
        const orbits = document.querySelectorAll('.orbit[data-base-duration]');
        const labels = [...document.querySelectorAll('.planet-label')];
        const planets = labels.map(label => document.querySelector(`.planet.${{label.dataset.planet}}`));
        const space = document.querySelector('.space');
        const caption = document.querySelector('.scale-note');
        const t = (Date.now() / 1000) % 3600; // 시간 기반 위상 (3600초 주기)
        orbits.forEach(orbit => {{
          const duration = parseFloat(getComputedStyle(orbit).getPropertyValue('--duration').match(/[0-9.]+/)[0]);
          if (duration > 0) {{
            const delay = -((t % duration) - duration);
            orbit.style.setProperty('--delay', delay.toFixed(2) + 's');
          }}
        }});

        function overlaps(a, b, gap = 6) {{
          return a.left < b.right + gap && a.right + gap > b.left &&
                 a.top < b.bottom + gap && a.bottom + gap > b.top;
        }}

        function resolveLabelCollisions() {{
          const spaceBox = space.getBoundingClientRect();
          const captionTop = caption.getBoundingClientRect().top - 12;
          const placed = [];
          // 우선순위: 오른쪽/왼쪽(±28), 위/아래(±42), 대각선, 미세 조정
          const candidates = [
            [32,-28],[32,28],[-32,-28],[-32,28],
            [0,-42],[0,42],
            [48,-14],[48,14],[-48,-14],[-48,14],
            [22,-35],[22,35],[-22,-35],[-22,35],
            [0,-55],[0,55],
            [12,-20],[12,20],[-12,-20],[-12,20]
          ];
          let collisions = 0;
          labels.forEach((label, index) => {{
            const planetBox = planets[index].getBoundingClientRect();
            const centerX = (planetBox.left + planetBox.right) / 2 - spaceBox.left;
            const centerY = (planetBox.top + planetBox.bottom) / 2 - spaceBox.top;
            let accepted = false;
            for (const [dx, dy] of candidates) {{
              label.style.left = `${{centerX + dx}}px`;
              label.style.top = `${{centerY + dy}}px`;
              label.style.transform = 'translateX(-50%)';
              const box = label.getBoundingClientRect();
              const inside = box.left >= spaceBox.left + 10 && box.right <= spaceBox.right - 10 &&
                             box.top >= spaceBox.top + 10 && box.bottom <= captionTop;
              if (inside && placed.every(other => !overlaps(box, other, 8))) {{
                placed.push(box); accepted = true; break;
              }}
            }}
            if (!accepted) {{
              collisions++;
              const vertOffset = (index % 2 === 0) ? -25 - Math.floor(index / 2) * 12 : 25 + Math.floor(index / 2) * 12;
              label.style.left = `${{Math.max(spaceBox.left + 15, Math.min(spaceBox.left + spaceBox.width - 45, centerX + (index % 2 === 0 ? -35 : 35))}}px`;
              label.style.top = `${{Math.max(spaceBox.top + 15, Math.min(captionTop - 20, centerY + vertOffset))}}px`;
              placed.push(label.getBoundingClientRect());
            }}
          }});
          return collisions;
        }}
        window.__solarResolveLabels = resolveLabelCollisions;
        let collisionCount = resolveLabelCollisions();
        console.log(`[Solar System] 라벨 충돌: ${{collisionCount}}건 (전체 1주기 통과 중 ${{collisionCount === 0 ? '안전' : '경고'}})`);
        window.setInterval(() => {{
          resolveLabelCollisions();
        }}, 100);
      }})();
    </script>
    """
    st.iframe(html, width="stretch", height=550, tab_index=-1)


def show_calculation(scenario) -> None:
    """선택한 시나리오의 공식, 실제 대입식, 결과를 같은 엔진 값으로 표시한다."""
    kind, r = scenario["type"], scenario["results"]
    if kind == ScenarioType.SUN_MASS.value:
        mu = 1 + scenario["percent_change"] / 100
        e = abs(mu - 1) / mu
        st.latex(r"e=\frac{|\mu-1|}{\mu},\qquad \mu=\frac{M'}{M}")
        st.latex(fr"e=\frac{{|{mu:.3f}-1|}}{{{mu:.3f}}}={e:.3f}")
        st.success(f"결과: 이심률 {e:.3f} → " + ("탈출 궤도" if e >= 1 else "타원 궤도"))
    elif kind == ScenarioType.EARTH_MASS.value:
        factor = 1 + scenario["percent_change"] / 100
        value = r["surface_gravity_new"]
        st.latex(r"\frac{g'}{g}=\frac{M'}{M}\left(\frac{R}{R'}\right)^2")
        st.latex(fr"\frac{{g'}}{{g}}={factor:.3f}\times 1^2={value:.3f}")
        st.success(f"결과: 현재 지구 중력의 {value:.3f}배")
    elif kind == ScenarioType.BLACKHOLE.value:
        mass = scenario["assumptions"]["mass_solar"]
        distance = scenario["assumptions"]["distance_au"]
        rs = r["schwarzschild_radius_km"]
        st.latex(r"R_s=\frac{2GM}{c^2},\quad F/F_\odot=\frac{M/M_\odot}{(r/\mathrm{AU})^2},\quad F_t/F_{t,\odot}=\frac{M/M_\odot}{(r/\mathrm{AU})^3}")
        st.latex(fr"R_s=\frac{{2(6.674\times10^{{-11}})({mass:g}\times1.989\times10^{{30}})}}{{(2.998\times10^8)^2}}={rs:.3g}\ \mathrm{{km}}")
        st.success(f"결과: 사건지평선 반지름 {format_number(rs, 'length')}, 상대 중력 {format_number(r['gravity_ratio_to_sun_at_1au'], 'multiple')} (거리 {distance:g} AU)")
    elif kind == ScenarioType.SIRIUS.value:
        a = scenario["assumptions"]
        flux = r["radiation_ratio_to_earth"]
        st.latex(r"S_*/S_\odot=(L_*/L_\odot)/(r/\mathrm{AU})^2,\quad T=288(1+S_*/S_\odot)^{1/4}")
        st.latex(fr"S_*/S_\odot={a['luminosity_solar']:.1f}/{a['distance_au']:.2f}^2={flux:.3f}")
        st.success(f"결과: 시리우스 복사 {format_number(flux, 'multiple')}, 추정 온도 {format_number(r['estimated_earth_temp_c'], 'temperature')}")
    elif kind == ScenarioType.EARTH_DISTANCE.value:
        distance = 1 + scenario["percent_change"] / 100
        flux = r["radiation_ratio_to_earth"]
        temp_k = r["estimated_earth_temp_c"] + 273.15
        st.latex(r"S/S_0=(r_0/r)^2,\qquad T_s=278.5(1-A)^{1/4}/\sqrt d+33.9")
        st.latex(fr"S/S_0=1/{distance:.3f}^2={flux:.4f}")
        st.latex(fr"T_s=278.5(1-0.306)^{{1/4}}/\sqrt{{{distance:.3f}}}+33.9={temp_k:.2f}\ \mathrm{{K}}")
        st.success(f"결과: 복사 에너지 {format_number(flux, 'multiple')}, 추정 온도 {format_number(r['estimated_earth_temp_c'], 'temperature')}")
    elif kind == ScenarioType.EARTH_ROTATION.value:
        hours = scenario["hours_per_day"]
        omega = 2 * np.pi / (hours * 3600)
        st.latex(r"\omega=2\pi/T,\qquad g_{eff}=g-\omega^2R_E")
        st.latex(fr"g_{{eff}}=9.81-({omega:.3e})^2(6.371\times10^6)={r['effective_gravity_ms2']:.3f}\ \mathrm{{m/s^2}}")
        st.success(f"결과: 유효중력 {r['effective_gravity_ms2']:.3f} m/s²")
    elif kind == ScenarioType.SOLAR_LUMINOSITY.value:
        factor = r["luminosity_ratio"]
        st.latex(r"T_s=278.5L^{1/4}(1-A)^{1/4}/\sqrt d+33.9")
        st.latex(fr"T_s=278.5({factor:.3f})^{{1/4}}(1-0.306)^{{1/4}}+33.9={r['estimated_earth_temp_c'] + 273.15:.2f}\ \mathrm{{K}}")
        st.success(f"결과: 추정 온도 {format_number(r['estimated_earth_temp_c'], 'temperature')}")
    elif kind == ScenarioType.EARTH_ALBEDO.value:
        albedo = r["albedo_value"]
        st.latex(r"T_s=278.5(1-A)^{1/4}+33.9")
        st.latex(fr"T_s=278.5(1-{albedo:.3f})^{{1/4}}+33.9={r['estimated_earth_temp_c'] + 273.15:.2f}\ \mathrm{{K}}")
        st.success(f"결과: 반사율 {albedo:.3f}, 추정 온도 {format_number(r['estimated_earth_temp_c'], 'temperature')}")
    elif kind == ScenarioType.ATMOSPHERE_LOSS.value:
        fraction = r["atmosphere_factor"]
        st.latex(r"T_s=T_e+33.9f_{atm}")
        st.latex(fr"T_s=254.1+33.9({fraction:.2f})={r['estimated_earth_temp_c'] + 273.15:.2f}\ \mathrm{{K}}")
        st.success(f"결과: 온실효과 감소 {r['temp_reduction_k']:.1f} K, 추정 온도 {format_number(r['estimated_earth_temp_c'], 'temperature')}")
    elif kind == ScenarioType.MAGNETIC_FIELD.value:
        factor = r["field_factor"]
        wind = 1 + r["solar_wind_increase"]
        st.latex(r"W/W_0=1+2(1-B/B_0)")
        st.latex(fr"W/W_0=1+2(1-{factor:.2f})={wind:.2f}")
        st.success(f"결과: 태양풍 영향은 기준의 {format_number(wind, 'multiple')}")
    else:
        st.error(f"계산 과정이 등록되지 않은 시나리오입니다: {kind}")


def validation_table() -> pd.DataFrame:
    """현재 조건을 엔진에 넣어 기준 관측값과 비교한다."""
    period_days = 365.0 * ENGINE.scenario_sun_mass_change(0)["period_ratio"]
    model_eccentricity = ENGINE.scenario_sun_mass_change(0)["orbit_model_b"]["eccentricity"]
    surface_k = ENGINE._calculate_earth_temperature()
    effective_k = surface_k - 33.9
    blackhole_km = ENGINE.scenario_blackhole_nearby(1, 1)["results"]["schwarzschild_radius_km"]
    rows = [
        ("지구 공전 주기", period_days, 365.26, "일"),
        ("지구 궤도 이심률", model_eccentricity, 0.0167, ""),
        ("유효 복사 온도", effective_k, 254.0, "K"),
        ("평균 지표 온도", surface_k, 288.0, "K"),
        ("1 M☉ 사건지평선", blackhole_km, 2.95, "km"),
    ]
    data = []
    for name, model, observed, unit in rows:
        if name == "지구 궤도 이심률":
            data.append({
                "항목": name,
                "우리 모델": f"{model:.4f}",
                "관측값": f"{observed:.4f}",
                "오차/절대차": f"{abs(model - observed):.4f} (절대차)",
                "판정": "원궤도 가정에 따른 설계값. 실제 지구는 e=0.0167로 거의 원궤도이므로 이 가정은 타당함",
            })
            continue
        error = abs(model - observed) / abs(observed) * 100
        data.append({
            "항목": name,
            "우리 모델": f"{model:.3g} {unit}".strip(),
            "관측값": f"{observed:.3g} {unit}".strip(),
            "오차/절대차": f"{error:.2f}%",
            "판정": "기준값 재현" if error <= 5 else "오차 5% 초과",
        })
    return pd.DataFrame(data)


def threshold_figure(selected_change: float):
    """태양 질량 급변 모델의 이심률 임계값 그림을 만든다."""
    changes = np.linspace(-90, 100, 381)
    mu = 1 + changes / 100
    eccentricity = np.abs(mu - 1) / mu
    fig, ax = plt.subplots(figsize=(12, 7), dpi=150)
    ax.plot(changes, eccentricity, color="#28c7fa", linewidth=3, label="지구 궤도 이심률")
    ax.axvspan(-90, -50, color="#ff4b5c", alpha=.18, label="탈출 영역 (e ≥ 1)")
    ax.axvline(-50, color="#ff4b5c", linestyle="--", linewidth=2)
    ax.axhline(1, color="#ffb45e", linestyle=":", linewidth=1.5)
    ax.annotate("임계점: -50%", (-50, 1), xytext=(-22, 1.7), arrowprops={"arrowstyle": "->", "color": "#ff4b5c"}, color="#ff4b5c", fontsize=14)
    selected_mu = 1 + selected_change / 100
    selected_e = abs(selected_mu - 1) / selected_mu
    ax.scatter([selected_change], [selected_e], s=100, color="#7c3aed", zorder=5, label="현재 선택값")
    ax.set_xlabel("태양 질량 변화율 (%)", fontsize=13)
    ax.set_ylabel("지구 궤도 이심률", fontsize=13)
    ax.set_xlim(-90, 100)
    ax.set_ylim(0, min(9.5, max(2.2, selected_e + .5)))
    ax.set_title("태양 질량 급변에 따른 지구 궤도 임계값", fontsize=18, pad=16, fontweight="bold")
    ax.tick_params(labelsize=12)
    ax.grid(alpha=.2)
    ax.legend(loc="upper right", fontsize=11)
    fig.tight_layout()
    return fig


def orbit_shape_figure(selected_change: float):
    """급격한 질량 변화 뒤 지구의 원뿔곡선 궤도를 정적으로 그린다."""
    mu = 1 + selected_change / 100
    eccentricity = abs(mu - 1) / mu
    if eccentricity < 1:
        theta = np.linspace(0, 2 * np.pi, 800)
        if mu <= 1:  # 현재 지점이 근일점
            semi_latus_rectum = 1 + eccentricity
            start = (1, 0)
        else:  # 현재 지점이 원일점
            semi_latus_rectum = 1 - eccentricity
            start = (-1, 0)
    else:
        limit = np.pi - .12 if np.isclose(eccentricity, 1) else np.arccos(-1 / eccentricity) - .05
        theta = np.linspace(-limit, limit, 800)
        semi_latus_rectum = 1 + eccentricity
        start = (1, 0)
    radius = semi_latus_rectum / (1 + eccentricity * np.cos(theta))
    valid = np.isfinite(radius) & (radius > 0) & (radius < 8)
    x = radius[valid] * np.cos(theta[valid])
    y = radius[valid] * np.sin(theta[valid])

    fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
    ax.plot(x, y, color="#28c7fa", linewidth=3)
    ax.scatter([0], [0], s=250, color="#ffd166", edgecolor="#ffb45e", label="태양", zorder=4)
    ax.scatter([start[0]], [start[1]], s=100, color="#4f93e8", label="질량 변화 시점의 지구", zorder=5)
    shape = "타원" if eccentricity < 1 else ("포물선" if np.isclose(eccentricity, 1) else "쌍곡선")
    ax.set_title(f"계산된 궤도: {shape} (e={eccentricity:.3f})", fontsize=18, pad=16, fontweight="bold")
    ax.set_xlabel("거리 (AU, 모델 축척)", fontsize=13)
    ax.set_ylabel("거리 (AU, 모델 축척)", fontsize=13)
    ax.tick_params(labelsize=12)
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(alpha=.2)
    ax.legend(loc="best", fontsize=11)
    fig.tight_layout()
    return fig


def figure_png(fig) -> bytes:
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    return buffer.getvalue()


st.markdown('<div class="hero-kicker">중학생 과학 시뮬레이션</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">태양계, 만약에?</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-copy">행성과 별의 조건을 바꾸며 결과를 관찰하는 가상 우주 실험입니다.</div>',
    unsafe_allow_html=True,
)

st.divider()

with st.expander("시작하기 전에", expanded=False):
    st.markdown("""
### 개요

태양 질량이 달라진다면? 지구가 블랙홀에 빨려간다면?
시리우스 A가 1 AU 거리에 나타난다면?

이 시뮬레이션은 태양계의 조건을 변화시켜 **행성의 공전 주기, 지구의 중력,
지구가 받는 빛과 열이 어떻게 달라지는지** 계산하고 보여줍니다.

### 배울 내용

- **케플러 제3법칙**: 태양 질량이 커지면 행성의 공전 주기는 짧아집니다
- **중력의 거리 의존성**: 질량이 클수록, 거리가 가까울수록 중력이 커집니다
- **복사 에너지**: 별의 밝기와 거리는 지구가 받는 에너지와 온도를 결정합니다
- **극한 상황 분석**: 블랙홀과 시리우스 같은 가상 상황에서 물리 법칙을 확인합니다

### 교과 연계

**중학교**: 천재교과서 중학교 과학 「태양계」 단원 — 태양계 구성, 행성의 공전, 별빛과 열의 복사 에너지

**고등학교**: 천재교과서 고등학교 「통합과학」 또는 「행성우주과학」 — 행성 공전의 물리, 케플러 법칙, 복사 에너지

### 사용 방법

1. **실험 유형 선택**: 왼쪽 메뉴에서 "시나리오 유형"을 고릅니다
2. **조건 설정**: 프리셋을 고르거나 "조건 직접 조정"으로 값을 바꿉니다
3. **결과 관찰**: 중앙의 애니메이션과 표를 보며 변화를 분석합니다
4. **해설 읽기**: 오른쪽 패널의 AI 해설(또는 기본 설명)로 결과를 이해합니다

**주의**: 이것은 교육용 단순 모델입니다. 실제 천체 운동과 지구 기후는 훨씬 복잡하며, 블랙홀과 시리우스 시나리오는 물리적으로 불가능한 가상 상황입니다.
    """)

st.divider()

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
    if scenario["type"] in {
        ScenarioType.EARTH_ROTATION.value,
        ScenarioType.EARTH_ALBEDO.value,
        ScenarioType.ATMOSPHERE_LOSS.value,
        ScenarioType.MAGNETIC_FIELD.value,
    }:
        st.caption("이 시나리오는 공전 궤도와 직접 관련이 없으며, 위 태양계 그림은 위치 참고용입니다.")

with right:
    score = risk_score(scenario)
    st.subheader("실험 결과")
    st.markdown(
        f'<div class="result-card danger-card"><div class="eyebrow">지구 거주 가능성 영향 지수</div>'
        f'<div class="big-result">{score} / 100</div></div>',
        unsafe_allow_html=True,
    )
    st.progress(score / 100)
    st.caption("지구에서 살 수 있는 조건이 얼마나 크게 달라지는지를 0~100으로 나타냈습니다. 100에 가까울수록 큰 변화입니다.")
    with st.expander("점수는 어떻게 계산하나요?"):
        st.latex(r"H(x)=100(1-e^{-x})")
        st.caption(
            "공통 환산 규칙: 온도는 |ΔT|/20 K, 지구 중력은 |ln(g/g₀)|/ln2, 외부 천체는 상대 중력·조석력, "
            "자전은 하루 길이·유효중력 변화, 자기장은 태양풍 증가량을 x로 사용합니다. 궤도 이탈은 100점이며 여러 영향 중 최댓값을 표시합니다."
        )
    for label, value, detail in scenario_metrics(scenario):
        st.metric(label, value, delta=detail, delta_color="off")
        caption_map = {
            "이심률": "궤도가 얼마나 찌그러졌는지. 0이면 동그라미, 1이면 탈출",
            "사건지평선": "이 안으로 들어가면 빛도 빠져나오지 못하는 경계",
            "상대 조석력": "물체를 양쪽으로 잡아 늘이는 힘",
            "원일점": "태양에서 가장 멀어지는 지점",
            "궤도 상태": "지구가 태양 주위를 계속 도는지, 벗어나는지",
        }
        if label in caption_map:
            st.caption(caption_map[label])
    if scenario["type"] == ScenarioType.SUN_MASS.value:
        with st.expander("비교 모델 A: 질량이 천천히 변한다면"):
            ratio = scenario["orbit_model_a"]["period_ratio"]
            st.metric("원궤도 주기", format_number(ratio, "multiple"), delta=format_number((ratio - 1) * 100, "percent"), delta_color="off")
            st.caption("질량이 갑자기 변하면 속도가 남아 궤도가 찌그러지고, 천천히 변하면 원궤도를 유지합니다.")

st.divider()
st.subheader("모델 검증")
validation = validation_table()
st.markdown(validation.to_html(index=False, classes="validation-table", border=0), unsafe_allow_html=True)
st.success("5개 기준을 모두 재현하며, 이심률은 원궤도 가정에 따른 의도된 차이입니다.")

st.subheader("10개 시나리오 대표 조건 점수")
st.dataframe(representative_score_table(), hide_index=True, use_container_width=True)

st.divider()
explain_tab, note_tab, calculation_tab = st.tabs(["쉬운 해설", "과학적 가정", "계산 과정"])
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
    assumption = ASSUMPTIONS.get(scenario["type"])
    if assumption:
        st.info(assumption)
    else:
        st.error(f"과학적 가정이 등록되지 않았습니다: {scenario['type']}")
    if scenario.get("limitations"):
        st.warning(f"추가 한계: {scenario['limitations']}")

with calculation_tab:
    show_calculation(scenario)

if scenario["type"] == ScenarioType.SUN_MASS.value:
    st.divider()
    st.subheader("태양 질량 임계값: −50%")
    graph_col, orbit_col = st.columns(2)
    with graph_col:
        threshold = threshold_figure(scenario["percent_change"])
        st.pyplot(threshold, width="stretch")
        st.download_button(
            "임계값 그래프 PNG 저장",
            data=figure_png(threshold),
            file_name="solar_mass_escape_threshold.png",
            mime="image/png",
        )
        plt.close(threshold)
    with orbit_col:
        orbit_shape = orbit_shape_figure(scenario["percent_change"])
        st.pyplot(orbit_shape, width="stretch")
        st.caption("선택한 이심률과 근일점/원일점을 사용한 계산 궤도입니다. e ≥ 1이면 바깥으로 열린 탈출 궤도입니다.")
        plt.close(orbit_shape)
    st.success("우리 모델은 태양 질량이 절반 이하로 급격히 줄면 지구가 태양계를 탈출한다고 예측합니다.")
