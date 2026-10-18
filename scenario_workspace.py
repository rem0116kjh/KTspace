"""Selectable WHAT IF experiments; calculations shared with the classic lab.

The extra experiments compare physical quantities, not integrated N-body orbits.
Climate values are educational equilibrium estimates, not weather forecasts.
"""
import math
from orbital_dynamics import LESSONS, build_experiment, validate_settings
from simulation_engine import PLANETS, SimulationEngine
from solar_scene import build_solar_scene

ENGINE = SimulationEngine(PLANETS)


def control(key, label, unit, low, high, step, default, help_text):
    return dict(key=key, label=label, unit=unit, min=low, max=high,
                step=step, default=default, help=help_text)


CATALOG = [
    dict(id="sun_mass", title="태양의 질량", subtitle="지구의 궤도", icon="orbit", question="태양이 가벼워지면 지구는 어떤 길로 움직일까요?", controls=[]),
    dict(id="blackhole", title="블랙홀", subtitle="질량과 거리", icon="blackhole", question="블랙홀이 더 가까워지면 지구를 끄는 힘은 얼마나 달라질까요?", controls=[
        control("mass", "블랙홀의 질량 (태양 기준)", "배", 1, 50, 1, 10, "태양 10개를 합친 질량이라면 10배예요."),
        control("distance", "블랙홀과 지구 사이 거리", "AU", .1, 10, .1, 1, "1 AU는 현재 태양과 지구 사이의 평균 거리예요.")]),
    dict(id="earth_mass", title="지구의 질량", subtitle="표면 중력", icon="globe", question="지구의 크기는 그대로 두고 질량이 두 배가 되면 몸을 끄는 힘은 어떨까요?", controls=[
        control("mass", "지구의 질량", "%", 20, 300, 5, 200, "현재 지구를 100%로 놓아요. 크기는 그대로예요.")]),
    dict(id="sirius", title="시리우스 A", subtitle="또 다른 별", icon="spark", question="밝은 별 시리우스 A가 가까이 생긴다면 지구에 빛이 얼마나 더 올까요?", controls=[
        control("distance", "시리우스 A와 지구 사이 거리", "AU", .5, 20, .5, 5, "태양은 그대로 있고, 별 하나가 더 있다고 가정해요.")]),
    dict(id="earth_distance", title="태양과의 거리", subtitle="햇빛과 공전", icon="compare", question="지구가 태양에서 더 멀어지면 받는 햇빛과 공전 주기는 어떻게 될까요?", controls=[
        control("distance", "태양과 지구 사이 거리", "AU", .5, 2, .05, 1.5, "태양의 질량과 밝기는 지금과 같아요.")]),
    dict(id="earth_rotation", title="지구의 자전", subtitle="하루의 길이", icon="clock", question="지구가 더 빨리 돌면 하루는 얼마나 짧아지고 적도의 유효중력은 어떨까요?", controls=[
        control("hours", "한 바퀴 자전하는 시간", "시간", 2, 72, 1, 12, "숫자가 작을수록 빨리 돌아요. 현재는 약 24시간이에요.")]),
    dict(id="solar_luminosity", title="태양의 밝기", subtitle="받는 에너지", icon="sun", question="태양의 밝기만 바뀌면 지구의 모형 온도는 어떻게 될까요?", controls=[
        control("brightness", "태양의 밝기", "%", 20, 200, 5, 120, "현재 밝기를 100%로 놓아요. 태양의 질량은 바꾸지 않아요.")]),
    dict(id="earth_albedo", title="지구의 반사율", subtitle="빛을 돌려보내기", icon="globe", question="지구가 햇빛을 더 많이 반사하면 흡수하는 에너지는 어떻게 될까요?", controls=[
        control("albedo", "들어온 햇빛을 반사하는 비율", "%", 0, 90, .1, 50, "현재 지구의 평균 반사율은 약 30.6%예요.")]),
    dict(id="atmosphere_loss", title="지구의 대기", subtitle="온실효과 모형", icon="layers", question="대기가 줄어들면 열을 붙잡는 효과는 어떻게 바뀔까요?", controls=[
        control("atmosphere", "현재와 비교한 대기의 양", "%", 0, 100, 5, 50, "이 모형에서는 대기의 양에 비례해 온실효과를 줄여요.")]),
    dict(id="magnetic_field", title="지구의 자기장", subtitle="자기권 비교", icon="shield", question="지구의 자기장이 약해지면 태양 쪽 자기권의 경계는 어떻게 달라질까요?", controls=[
        control("field", "현재와 비교한 자기장 세기", "%", 0, 200, 5, 50, "태양풍의 압력과 지구의 크기는 같다고 놓아요.")]),
]
BY_ID = {item["id"]: item for item in CATALOG}


def validate_workspace(values=None):
    values = {} if values is None else values
    if not isinstance(values, dict):
        raise ValueError("설정은 객체여야 합니다.")
    kind = values.get("scenario", "sun_mass")
    if not isinstance(kind, str) or kind not in BY_ID:
        raise ValueError("목록에서 실험 종류를 선택해주세요.")
    if kind == "sun_mass":
        return validate_settings(values)
    result = {"scenario": kind}
    for spec in BY_ID[kind]["controls"]:
        value = values.get(spec["key"], spec["default"])
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not spec["min"] <= value <= spec["max"]:
            raise ValueError(f"{spec['label']}: {spec['min']}~{spec['max']} 사이의 수를 넣어주세요.")
        result[spec["key"]] = float(value)
    return result


def metric(label, value, unit, baseline, detail):
    return dict(label=label, value=float(value), unit=unit, baseline=float(baseline), detail=detail)


CLIMATE_LIMIT = "평균적인 에너지 균형을 보는 단순 모형이에요. 구름·해류·계절과 실제 기후의 반응 시간은 계산하지 않아요."
BASE_TEMP = ENGINE._calculate_earth_temperature() - 273.15
SOURCES = {
    "blackhole": ("NASA · 블랙홀 알아보기", "https://www.nasa.gov/learning-resources/for-kids-and-students/what-is-a-black-hole-grades-5-8/"),
    "climate": ("NASA · 지구의 에너지 균형", "https://science.nasa.gov/earth/earth-observatory/climate-and-earths-energy-budget/"),
    "magnetic_field": ("NASA · 자기권", "https://science.nasa.gov/science-research/planetary-science/earths-magnetosphere/"),
}


def calculate(s):
    kind = s["scenario"]
    if kind == "blackhole":
        r = ENGINE.scenario_blackhole_nearby(s["mass"], s["distance"])["results"]
        g, tidal = r["gravity_ratio_to_sun_at_1au"], r["tidal_ratio_to_sun_at_1au"]
        return dict(headline=f"블랙홀이 끄는 힘은 기준 태양 중력의 {g:,.2f}배예요.",
                    reason="질량이 클수록, 거리가 가까울수록 끌어당기는 힘이 커져요. 같은 질량과 같은 거리라면 블랙홀도 별과 같은 중력을 만들어요.",
                    metrics=[metric("끌어당기는 힘", g, "배", 1, "현재 태양이 지구를 끄는 힘 = 1"), metric("양쪽을 다르게 끄는 조석 효과", tidal, "배", 1, "현재 태양에 의한 조석 효과 = 1"), metric("사건의 지평선 반지름", r["schwarzschild_radius_km"], "km", 2.953, "빛도 빠져나올 수 없는 경계 · 태양 질량 1배 기준과 비교")],
                    limitation="수치 표는 태양을 없애지 않고 블랙홀을 추가한 시작 순간의 조건이에요. 블랙홀만의 힘을 비교하며 태양과 힘을 단순히 더하지 않아요. 위 궤적은 태양·블랙홀을 고정한 중력 모형이고, 실제 접근 운동·상대론·강착 원반의 복사는 생략해요. 이 거리에서 즉시 빨려 들어간다는 뜻은 아니에요.",
                    formula="중력 비 = M / d² · 조석 효과 비 = M / d³ · 사건의 지평선 반지름 ≈ 2.953M km", chart_label="블랙홀의 중력 / 현재 태양의 중력", source="blackhole")
    if kind == "earth_mass":
        factor = ENGINE.scenario_earth_mass_change(s["mass"] - 100)["results"]["surface_gravity_new"]
        return dict(headline=f"지구가 끄는 힘이 현재의 {factor:,.2f}배가 돼요.", reason="지구의 크기를 고정하면 질량이 늘어난 만큼 표면 중력도 커져요. 몸의 질량은 그대로지만, 바닥을 누르는 힘은 달라져요.",
                    metrics=[metric("표면 중력", 9.81*factor, "m/s²", 9.81, "지구의 반지름은 현재와 같음"), metric("50 kg 물체에 작용하는 힘", 50*9.81*factor, "N", 50*9.81, "질량 50 kg은 변하지 않아요"), metric("탈출에 필요한 속력", 11.186*math.sqrt(factor), "km/s", 11.186, "공기 저항과 자전은 생략")],
                    limitation="지구의 크기·밀도 분포 변화와 자전 효과는 생략해요. 질량과 무게는 서로 다른 양이에요.", formula="g = GM/R² · 무게 F = mg · 탈출 속력 = √(2GM/R)", chart_label="표면 중력 (m/s²)")
    if kind == "earth_rotation":
        r = ENGINE.scenario_earth_rotation(s["hours"])["results"]
        base = ENGINE.scenario_earth_rotation(24)["results"]
        return dict(headline=f"하루가 {s['hours']:g}시간, 현재의 {s['hours']/24:.2f}배가 돼요.", reason="더 빨리 자전하면 하루가 짧아져요. 적도에서는 회전에 따른 효과가 중력의 일부를 줄여, 바닥에서 느끼는 힘도 조금 작아져요.",
                    metrics=[metric("자전 한 바퀴", s["hours"], "시간", 24, "현재 약 24시간과 비교"), metric("적도의 유효중력", r["effective_gravity_ms2"], "m/s²", base["effective_gravity_ms2"], "중력에서 회전 효과를 뺀 값"), metric("적도의 지표면 속력", 2*math.pi*6371/(s["hours"]*3600), "km/s", 2*math.pi*6371/86400, "위도 0°에서 계산")],
                    limitation="구형 지구를 가정하며 적도에서 계산해요. 지구의 변형·날씨·자전축 변화와 태양일·항성일의 작은 차이는 생략해요.", formula="유효중력 = 9.81 − (2π/T)²R · R = 6,371 km", chart_label="하루의 길이 (시간)")
    if kind == "magnetic_field":
        factor = ENGINE.scenario_magnetic_field(s["field"])["results"]["field_factor"]
        boundary = factor**(1/3)
        return dict(headline="지구 고유 자기장에 의한 경계를 이 모형에서 정의할 수 없어요." if factor == 0 else f"태양 쪽 자기권 경계의 거리가 현재의 약 {boundary*100:.0f}%가 돼요.",
                    reason="지구의 자기장과 태양풍의 압력이 균형을 이루는 경계를 비교해요. 태양풍이 같다면 자기장이 약할수록 경계가 지구 가까이 와요.",
                    metrics=[metric("자기장 세기", s["field"], "%", 100, "현재 지구 = 100%"), metric("자기권 경계 거리 비", boundary, "배", 1, "지구 중심에서 본 상대 거리 · 0은 쌍극자 모형의 극한")],
                    limitation="쌍극자 자기장과 일정한 태양풍을 가정한 상대값이에요. 0%에서는 지구 고유 자기장에 의한 자기권 모형이 적용되지 않아요. 지상 방사선량·대기 손실·생존 여부는 예측하지 않아요.", formula="B ∝ M/r³ · 자기 압력 ∝ B² · 같은 태양풍에서 경계 거리 비 = (자기장 세기 비)⅓", chart_label="자기권 경계 거리 비 (배)", source="magnetic_field")
    flux, temp, period = 1.0, BASE_TEMP, None
    if kind == "sirius":
        r = ENGINE.scenario_sirius_nearby(s["distance"])["results"]
        flux = 1 + r["radiation_ratio_to_earth"]
        # Use the same calibrated equilibrium formula as all climate experiments.
        temp = ENGINE._calculate_earth_temperature(luminosity_ratio=flux) - 273.15
        gravity = r["gravity_ratio_to_sun_at_1au"]
        metrics = [metric("도착하는 빛의 에너지", flux, "배", 1, "태양 + 시리우스 A의 빛을 합친 값")]
        metrics += [metric("모형 평균 온도", temp, "°C", BASE_TEMP, "평형에 도달했다고 가정한 값"), metric("추가된 별의 중력", gravity, "배", 1, "현재 태양의 중력 = 1 · 방향은 생략")]
        reason = "시리우스 A는 이 모형에서 태양보다 24.7배 밝아요. 태양빛에 이 별의 빛을 더하고, 거리의 제곱에 따라 줄어드는 에너지를 계산해요."
        formula = "빛의 에너지 비 = 1 + 24.7/d² · 별 질량 = 2.063 M☉"
    elif kind == "earth_distance":
        r = ENGINE.scenario_earth_distance((s["distance"]-1)*100)["results"]
        flux, temp = r["radiation_ratio_to_earth"], r["estimated_earth_temp_c"]
        period = math.sqrt(s["distance"]**3)*365.25
        metrics = [metric("받는 햇빛 에너지", flux*100, "%", 100, "현재 지구 = 100%"), metric("모형 평균 온도", temp, "°C", BASE_TEMP, "평형에 도달했다고 가정한 값") ,metric("원궤도 공전 주기", period, "일", 365.25, "새 거리의 원궤도 속도로 출발")]
        reason, formula = "멀어질수록 같은 면적에 도착하는 빛이 줄어요. 원궤도를 가정하면 더 멀리 있는 지구는 한 바퀴 도는 데 오래 걸려요.", "빛의 에너지 비 = 1/d² · 원궤도 주기 T = √(d³)년"
    elif kind == "solar_luminosity":
        r = ENGINE.scenario_solar_luminosity(s["brightness"]-100)["results"]
        flux, temp = r["luminosity_ratio"], r["estimated_earth_temp_c"]
        metrics = [metric("받는 햇빛 에너지", flux*100, "%", 100, "현재 지구 = 100%"), metric("모형 평균 온도", temp, "°C", BASE_TEMP, "평형에 도달했다고 가정한 값")]
        reason, formula = "태양이 밝아질수록 같은 거리의 지구가 받는 에너지가 많아져요. 온도는 에너지와 정비례하지 않고 완만하게 변해요.", "복사 평형 온도 ∝ (태양 밝기)¼"
    elif kind == "earth_albedo":
        r = ENGINE.scenario_earth_albedo((s["albedo"]/30.6-1)*100)["results"]
        temp = r["estimated_earth_temp_c"]
        metrics = [metric("반사하는 햇빛", s["albedo"], "%", 30.6, "들어온 빛 = 100%"), metric("흡수하는 햇빛", 100-s["albedo"], "%", 69.4, "반사되지 않은 에너지"), metric("모형 평균 온도", temp, "°C", BASE_TEMP, "평형에 도달했다고 가정한 값")]
        reason, formula = "반사율이 높아지면 햇빛을 더 많이 우주로 돌려보내요. 흡수하는 에너지가 줄어 모형의 온도도 낮아져요.", "흡수 비율 = 1 − 반사율 · 복사 평형 온도 ∝ (흡수 비율)¼"
    else:
        r = ENGINE.scenario_atmosphere_loss(s["atmosphere"])["results"]
        temp = r["estimated_earth_temp_c"]
        metrics = [metric("남은 대기의 양", s["atmosphere"], "%", 100, "현재 대기 = 100%"), metric("모형의 온실효과 가산값", 33.9*s["atmosphere"]/100, "°C", 33.9, "대기 비율에 따라 선형으로 줄인 가정"), metric("모형 평균 온도", temp, "°C", BASE_TEMP, "평형에 도달했다고 가정한 값")]
        reason, formula = "대기가 열을 붙잡는 효과를 단순하게 비교해요. 대기가 줄어든 만큼 온실효과 가산값을 줄이는 가정을 사용해요.", "모형 온도 = 복사 평형 온도 + 33.9 × 대기 비율 (K)"
    headline = f"이 조건의 모형 평균 온도는 약 {temp:.1f}°C예요."
    limit = CLIMATE_LIMIT + (" 두 별이 만드는 실제 궤도는 계산하지 않아요." if kind == "sirius" else "")
    return dict(headline=headline, reason=reason, metrics=metrics, limitation=limit,
                formula=formula+" · T = 278.5[L(1−A)]¼/√d + 33.9f (K)",
                chart_label=metrics[0]["label"]+f" ({metrics[0]['unit']})", source="climate")


def build_workspace(values=None):
    settings = validate_workspace(values)
    kind = settings.get("scenario", "sun_mass")
    if kind == "sun_mass":
        payload = build_experiment(settings)
        payload.update(kind="orbit", catalog=CATALOG)
        return payload
    spec = BY_ID[kind]
    result = calculate(settings)
    primary = spec["controls"][0]
    chart_index = {"earth_rotation": 1, "magnetic_field": 1, "earth_albedo": 2,
                   "atmosphere_loss": 2, "solar_luminosity": 1}.get(kind, 0)
    chart_metric = result["metrics"][chart_index]
    result["chart_value"] = chart_metric["value"]
    result["chart_label"] = f"{chart_metric['label']} ({chart_metric['unit']})"
    curve = []
    for i in range(41):
        x = primary["min"] + (primary["max"]-primary["min"])*i/40
        point = calculate({**settings, primary["key"]: x})
        curve.append([x, point["metrics"][chart_index]["value"]])
    source = SOURCES.get(result.pop("source", ""))
    return dict(kind="scenario", settings=settings, catalog=CATALOG, lessons=LESSONS,
                scenario=spec, result=result, curve=curve, source=source,
                scene=build_solar_scene(settings,result),
                observation_starter=f"{spec['title']} 실험에서 "+" · ".join(f"{c['label']} {settings[c['key']]:g}{c['unit']}" for c in spec["controls"])+f"로 바꾸었다. {result['headline']}")
