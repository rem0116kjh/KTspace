"""Two-body lab in AU, Julian years and solar masses.

The central mass is fixed after t=0. No mutual planetary forces or relativity.
The circular model assumes the new mass always existed, not adiabatic mass loss.
"""
import math
from learning_content import explain_for_learners

G = 4 * math.pi**2
YEAR_DAYS = 365.25
VELOCITY_KMS = 149_597_870.7 / (YEAR_DAYS * 86400)
DEFAULTS = {"mass": 0.8, "radius": 1.0, "model": "impulse", "step": 1.0}
LESSONS = [
    {"id": "mass", "number": "01", "title": "태양이 가벼워진다면?", "tag": "처음 해 보는 실험", "minutes": 5,
     "question": "태양의 질량이 20% 줄면, 지구가 도는 길은 어떻게 바뀔까요?", "mass": 0.8, "model": "impulse", "radius": 1},
    {"id": "escape", "number": "02", "title": "지구가 태양을 떠날 수도 있을까?", "tag": "탈출 알아보기", "minutes": 5,
     "question": "태양의 질량이 갑자기 절반이 되면, 지구는 계속 태양을 돌 수 있을까요?", "mass": 0.5, "model": "impulse", "radius": 1},
    {"id": "kepler", "number": "03", "title": "더 멀리서 돌면 얼마나 걸릴까?", "tag": "거리 바꿔 보기", "minutes": 10,
     "question": "지구가 지금보다 1.5배 멀리서 동그랗게 돈다면, 한 바퀴 도는 시간은 어떻게 될까요?", "mass": 1, "model": "circular", "radius": 1.5},
    {"id": "energy", "number": "04", "title": "컴퓨터의 계산은 얼마나 정확할까?", "tag": "심화 탐구", "minutes": 15,
     "question": "컴퓨터가 움직임을 더 잘게 나누어 계산하면, 계산의 오차는 줄어들까요?", "mass": 1.5, "model": "impulse", "radius": 1},
]


def validate_settings(values=None):
    values = {} if values is None else values
    if not isinstance(values, dict):
        raise ValueError("설정은 객체여야 합니다.")
    result = dict(DEFAULTS)
    for key, low, high in [("mass", 0.2, 2.0), ("radius", 0.5, 2.0), ("step", 0.25, 4.0)]:
        value = values.get(key, result[key])
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{key}: {low}~{high} 범위의 유한한 수가 필요합니다.")
        result[key] = float(value)
    model = values.get("model", result["model"])
    if model not in ("impulse", "circular"):
        raise ValueError("지원하지 않는 궤도 모델입니다.")
    result["model"] = model
    return result


def orbit_elements(mass, radius=1.0, model="impulse"):
    """Analytic elements for an initially tangential circular velocity."""
    settings = validate_settings({"mass": mass, "radius": radius, "model": model})
    mass, radius = settings["mass"], settings["radius"]
    v2 = G * (mass if model == "circular" else 1.0) / radius
    energy = v2 / 2 - G * mass / radius
    eccentricity = 0.0 if model == "circular" else abs(1 - mass) / mass
    parabolic = math.isclose(eccentricity, 1.0, abs_tol=1e-10)
    bound = eccentricity < 1 and not parabolic
    a = -G * mass / (2 * energy) if not parabolic else None
    p = radius if model == "circular" else radius / mass
    peri = p / (1 + eccentricity)
    apo = a * (1 + eccentricity) if bound else None
    period = math.sqrt(a**3 / mass) if bound else None
    return {"eccentricity": eccentricity, "semimajor_au": a, "perihelion_au": peri,
            "aphelion_au": apo, "period_days": period * YEAR_DAYS if period else None,
            "energy_km2_s2": energy * VELOCITY_KMS**2, "velocity_kms": math.sqrt(v2) * VELOCITY_KMS,
            "escape_kms": math.sqrt(2 * G * mass / radius) * VELOCITY_KMS,
            "state": "ellipse" if bound and eccentricity > 1e-10 else "circle" if bound else "parabola" if parabolic else "hyperbola",
            "bound": bound}


def integrate(mass, radius=1.0, model="impulse", step_days=1.0, duration_years=2.0):
    """Velocity Verlet; normalize energy error by GM_sun/r, also valid at E=0."""
    settings = validate_settings({"mass": mass, "radius": radius, "model": model, "step": step_days})
    if not math.isfinite(duration_years) or not 0 < duration_years <= 6:
        raise ValueError("적분 기간은 0~6년 이내여야 합니다.")
    steps = math.ceil(duration_years * YEAR_DAYS / settings["step"])
    dt = duration_years / steps
    gm = G * mass
    x, y = radius, 0.0
    vx, vy = 0.0, math.sqrt(G * (mass if model == "circular" else 1.0) / radius)
    e0 = (vx**2 + vy**2) / 2 - gm / radius
    h0 = x * vy - y * vx
    energy_scale = G / radius
    max_energy_error = max_momentum_error = 0.0
    trajectory, diagnostics = [], []
    stride = max(1, steps // 700)
    ax, ay = -gm * x / radius**3, 0.0
    for i in range(steps + 1):
        r = math.hypot(x, y)
        energy = (vx**2 + vy**2) / 2 - gm / r
        err = (energy - e0) / energy_scale
        momentum_err = abs((x * vy - y * vx - h0) / h0)
        max_energy_error = max(max_energy_error, abs(err))
        max_momentum_error = max(max_momentum_error, momentum_err)
        if i % stride == 0 or i == steps:
            trajectory.append([round(i * dt, 8), round(x, 8), round(y, 8)])
            diagnostics.append([round(i * dt, 8), err * 100])
        if i == steps:
            break
        nx, ny = x + vx * dt + ax * dt**2 / 2, y + vy * dt + ay * dt**2 / 2
        nr = math.hypot(nx, ny)
        nax, nay = -gm * nx / nr**3, -gm * ny / nr**3
        vx, vy = vx + (ax + nax) * dt / 2, vy + (ay + nay) * dt / 2
        x, y, ax, ay = nx, ny, nax, nay
    return {"trajectory": trajectory, "diagnostics": diagnostics, "steps": steps,
            "max_energy_error_pct": max_energy_error * 100,
            "max_momentum_error_pct": max_momentum_error * 100,
            "duration_years": duration_years, "actual_step_days": dt * YEAR_DAYS}


def build_experiment(values=None):
    settings = validate_settings(values)
    elements = orbit_elements(settings["mass"], settings["radius"], settings["model"])
    period = elements["period_days"]
    duration = min(6.0, max(2.0, period / YEAR_DAYS if period else 2.0))
    simulation = integrate(settings["mass"], settings["radius"], settings["model"], settings["step"], duration)
    baseline = orbit_elements(1.0, settings["radius"], "circular")
    comparison = orbit_elements(settings["mass"], settings["radius"], "circular" if settings["model"] == "impulse" else "impulse")
    mass, e = settings["mass"], elements["eccentricity"]
    if settings["model"] == "circular":
        explanation = f"태양이 처음부터 {mass:.2f} M☉였다고 가정하면, 원궤도에 필요한 속도는 {elements['velocity_kms']:.2f} km/s입니다. 거리를 고정한 비교에서는 T² = a³/M을 따릅니다. 이 모델은 질량이 천천히 감소하는 실제 과정과는 다릅니다."
    elif not elements["bound"]:
        explanation = f"초기 위치와 속도를 유지한 채 태양 질량이 {mass:.2f} M☉가 되면 단위 질량당 역학적 에너지가 0 이상입니다. 이심률 e = {e:.3f}인 열린 궤도가 되어 공전 주기와 원일점이 정의되지 않습니다."
    else:
        explanation = f"질량이 바뀌는 순간에도 지구의 속도는 {elements['velocity_kms']:.2f} km/s로 유지됩니다. 새로운 중력에 맞는 원궤도 속도와 달라지면서 이심률 e = {e:.3f}인 궤도가 만들어집니다. 에너지가 음수여서 지구는 태양에 묶여 있습니다."
    return {"settings": settings, "elements": elements, "baseline": baseline, "comparison": comparison,
            "simulation": simulation, "lessons": LESSONS, "explanation": explanation,
            "learning": explain_for_learners(settings, elements, baseline),
            "threshold": [[m / 100, abs(1 - m / 100) / (m / 100)] for m in range(20, 201, 2)],
            "units": {"distance": "AU", "time": "Julian year (365.25 days)", "mass": "M☉", "G": G}}
