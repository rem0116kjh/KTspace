"""Eight-planet educational view, in AU and Julian years.

Circular Kepler reference orbits are schematic initial conditions, not ephemerides.
External-body experiments integrate test particles in two fixed Newtonian fields.
The near-field cutoff ends a trace; it does not classify a collision or capture.
"""
import math
from functools import lru_cache
from orbital_dynamics import G, YEAR_DAYS

PLANET_VIEW = [
    ("mercury", "수성", .387, .5, "#b6aaa1", 3),
    ("venus", "금성", .723, 2.1, "#e3be8d", 4.5),
    ("earth", "지구", 1.0, 0.0, "#78e6cf", 5),
    ("mars", "화성", 1.524, 3.4, "#e59078", 4),
    ("jupiter", "목성", 5.203, 5.3, "#cda98c", 8),
    ("saturn", "토성", 9.537, 1.4, "#e1cb99", 7),
    ("uranus", "천왕성", 19.19, 4.4, "#a0d4de", 5.5),
    ("neptune", "해왕성", 30.07, 2.8, "#7d9ff0", 5.5),
]
DURATION = 2.0
CLOSE_AU = .025


def circular_position(radius, phase, time):
    angle = phase + math.tau * time / math.sqrt(radius**3)
    return radius*math.cos(angle), radius*math.sin(angle)


def acceleration(x, y, mass, source_x):
    r = math.hypot(x, y)
    dx, dy = source_x-x, -y
    d = math.hypot(dx, dy)
    return (-G*x/r**3 + G*mass*dx/d**3,
            -G*y/r**3 + G*mass*dy/d**3)


def integrate_trace(radius, phase, mass, source_x, duration=DURATION, step_days=.25):
    """Adaptive Velocity Verlet in a prescribed, stationary two-source potential."""
    x, y = circular_position(radius, phase, 0)
    v = math.sqrt(G/radius)
    vx, vy = -v*math.sin(phase), v*math.cos(phase)
    t, last_sample = 0.0, 0.0
    points = [[0.0, x, y]]
    status = "complete"
    for _ in range(30000):
        r, d = math.hypot(x,y), math.hypot(x-source_x,y)
        if min(r,d) <= CLOSE_AU:
            status = "close_approach"
            break
        if t >= duration-1e-12:
            break
        dt = min(step_days/YEAR_DAYS, .035*math.sqrt(r**3/G),
                 .035*math.sqrt(d**3/(G*mass)), duration-t)
        ax, ay = acceleration(x,y,mass,source_x)
        nx, ny = x+vx*dt+ax*dt*dt/2, y+vy*dt+ay*dt*dt/2
        # Do not evaluate a singular acceleration if a step enters the cutoff.
        if min(math.hypot(nx,ny),math.hypot(nx-source_x,ny)) <= CLOSE_AU:
            x,y,t = nx,ny,t+dt
            status = "close_approach"
            break
        nax,nay = acceleration(nx,ny,mass,source_x)
        vx,vy = vx+(ax+nax)*dt/2, vy+(ay+nay)*dt/2
        x,y,t = nx,ny,t+dt
        sample_gap = min(duration/440, .18*math.sqrt(r**3/G),
                         .18*math.sqrt(d**3/(G*mass)))
        if t-last_sample >= sample_gap or t >= duration-1e-12:
            points.append([t,x,y])
            last_sample = t
            if len(points) >= 1800 and t < duration-1e-12:
                status = "step_limit"
                break
    else:
        status = "step_limit"
    if t > points[-1][0]:
        points.append([t,x,y])
    return dict(trajectory=points, status=status, end_years=t)


@lru_cache(maxsize=48)
def _paths(kind, distance, mass):
    bodies = []
    external = kind in ("blackhole","sirius")
    source_x = 1+distance
    for ident,name,radius,phase,color,size in PLANET_VIEW:
        if ident == "earth" and kind == "earth_distance":
            radius = distance
        if external:
            path = integrate_trace(radius,phase,mass,source_x)
        else:
            path = dict(trajectory=[[DURATION*i/480,*circular_position(radius,phase,DURATION*i/480)] for i in range(481)],
                        status="complete",end_years=DURATION)
        bodies.append(dict(id=ident,name=name,radius_au=radius,period_years=math.sqrt(radius**3),
                           phase=phase,color=color,size=size,**path))
    return bodies


def build_solar_scene(settings, result):
    kind = settings["scenario"]
    external = kind in ("blackhole","sirius")
    distance = settings.get("distance",1.0)
    mass = settings["mass"] if kind == "blackhole" else 2.063 if kind == "sirius" else 0.0
    bodies = _paths(kind,distance,mass)
    if external:
        note = "태양과 추가 천체를 고정하고, 각 행성이 받는 두 천체의 중력으로 궤적을 계산해요. 행성끼리의 힘과 실제 접근 운동은 생략해요."
        detail = "점선은 추가 천체가 없을 때의 원궤도예요. 가까운 접근에서는 계산을 멈추며, 충돌하거나 빨려 들어갔다고 판정하지 않아요. 아래 비교 수치는 시작 순간의 조건 기준이에요."
    else:
        note = "8개 행성의 원궤도 공전을 보여줘요. 거리 실험은 지구 궤도에 반영하며, 다른 지구 환경 조건은 공전 궤도를 바꾸지 않는다고 가정해요."
        detail = "지구 확대에서는 자전·대기·빛·자기장 등 선택한 조건을 보여줘요. 자전은 속도 차이를 보기 쉽게 별도의 느린 배율로 표시해요."
    metric = result["metrics"][0]
    if kind in ("solar_luminosity","earth_albedo","atmosphere_loss","sirius","earth_distance"):
        metric = next((m for m in result["metrics"] if m["label"] == "모형 평균 온도"),metric)
    if kind == "magnetic_field":
        metric = result["metrics"][1]
    temp = next((m["value"] for m in result["metrics"] if m["label"] == "모형 평균 온도"),15)
    flux = (1+24.7/distance**2 if kind=="sirius" else 1/distance**2 if kind=="earth_distance"
            else settings.get("brightness",100)/100)
    return dict(duration_years=DURATION,bodies=bodies,source=dict(kind=kind,x=1+distance,y=0,mass=mass,
                name="블랙홀" if kind=="blackhole" else "시리우스 A",initial_distance_au=distance) if external else None,
                note=note,detail=detail,projection_note="행성의 거리 간격을 줄여 표시하고, 천체 크기는 확대했어요. 실제 비율은 아니에요.",
                focus=dict(kind=kind,temperature_c=temp,flux=flux,atmosphere=settings.get("atmosphere",100)/100,
                           field=settings.get("field",100)/100,albedo=settings.get("albedo",30.6)/100,
                           rotation_hours=settings.get("hours",24),gravity=settings.get("mass",100)/100 if kind=="earth_mass" else 1,
                           brightness=settings.get("brightness",100)/100,
                           metric=metric),
                source_url="https://nssdc.gsfc.nasa.gov/planetary/factsheet/")
