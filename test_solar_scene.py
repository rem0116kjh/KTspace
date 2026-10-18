import json
import math
import pytest
from orbital_dynamics import G
from scenario_workspace import CATALOG, build_workspace
from solar_scene import acceleration, integrate_trace


@pytest.mark.parametrize("spec",[s for s in CATALOG if s["id"]!="sun_mass"],ids=lambda s:s["id"])
def test_all_other_experiments_have_eight_finite_planet_traces(spec):
    p=build_workspace({"scenario":spec["id"]})
    scene=p["scene"]
    assert [b["name"] for b in scene["bodies"]]==["수성","금성","지구","화성","목성","토성","천왕성","해왕성"]
    json.dumps(scene,allow_nan=False)
    for body in scene["bodies"]:
        times=[p[0] for p in body["trajectory"]]
        assert times[0]==0
        assert all(b>a for a,b in zip(times,times[1:]))
        assert times[-1]==pytest.approx(body["end_years"])
        assert 0<times[-1]<=scene["duration_years"]+1e-9


def test_reference_earth_completes_one_orbit_in_a_year():
    earth=next(b for b in build_workspace({"scenario":"earth_mass"})["scene"]["bodies"] if b["id"]=="earth")
    at_year=min(earth["trajectory"],key=lambda p:abs(p[0]-1))
    assert at_year==pytest.approx([1,1,0],abs=1e-10)


def test_distance_changes_earth_orbit_but_not_other_planets():
    a=build_workspace({"scenario":"earth_distance","distance":1})["scene"]
    b=build_workspace({"scenario":"earth_distance","distance":1.5})["scene"]
    for before,after in zip(a["bodies"],b["bodies"]):
        if before["id"]=="earth":
            assert after["trajectory"][0][1]==1.5
            assert after["period_years"]==pytest.approx(1.5**1.5)
        else:
            assert before["trajectory"]==after["trajectory"]


def test_ground_conditions_do_not_falsely_change_earth_orbit():
    a=build_workspace({"scenario":"earth_mass","mass":100})["scene"]
    b=build_workspace({"scenario":"earth_mass","mass":300})["scene"]
    assert a["bodies"]==b["bodies"]
    assert b["focus"]["gravity"]==3
    atmosphere=build_workspace({"scenario":"atmosphere_loss","atmosphere":0})["scene"]
    magnetic=build_workspace({"scenario":"magnetic_field","field":0})["scene"]
    assert atmosphere["focus"]["atmosphere"]==0
    assert magnetic["focus"]["field"]==0


def test_external_position_matches_initial_earth_distance():
    scene=build_workspace({"scenario":"blackhole","distance":2})["scene"]
    earth=next(b for b in scene["bodies"] if b["id"]=="earth")
    _,x,y=earth["trajectory"][0]
    assert math.hypot(x-scene["source"]["x"],y-scene["source"]["y"])==pytest.approx(2)


def test_additional_force_is_a_vector_sum_not_scalar_ratio_sum():
    # Earth at x=1, Sun at 0, extra 10 solar masses at x=3.
    ax,ay=acceleration(1,0,10,3)
    assert ax==pytest.approx(-G+10*G/4)
    assert ay==0


def test_restricted_orbit_converges_with_smaller_step():
    def endpoint(step):
        return integrate_trace(1,0,1,11,duration=1,step_days=step)["trajectory"][-1][1:]
    reference=endpoint(.125)
    coarse=math.dist(endpoint(1),reference)
    fine=math.dist(endpoint(.5),reference)
    assert fine<coarse/3


def test_near_approach_is_terminated_and_not_reported_as_capture():
    scene=build_workspace({"scenario":"blackhole","mass":50,"distance":.1})["scene"]
    earth=next(b for b in scene["bodies"] if b["id"]=="earth")
    assert earth["status"]=="close_approach"
    assert earth["end_years"]<.1
    assert "판정하지 않아요" in scene["detail"]


def test_earth_close_view_uses_the_calculated_temperature_and_rotation():
    p=build_workspace({"scenario":"solar_luminosity","brightness":200})
    temperature=next(m["value"] for m in p["result"]["metrics"] if m["label"]=="모형 평균 온도")
    assert p["scene"]["focus"]["temperature_c"]==temperature
    assert p["scene"]["focus"]["brightness"]==2
    q=build_workspace({"scenario":"earth_rotation","hours":12})
    assert q["scene"]["focus"]["rotation_hours"]==12
