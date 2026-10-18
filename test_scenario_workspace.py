"""Physical invariants and API contracts for all selectable experiments."""
import json
import math
import pytest
from orbital_dynamics import build_experiment
from scenario_workspace import CATALOG, build_workspace, validate_workspace


@pytest.mark.parametrize("spec", CATALOG, ids=lambda c: c["id"])
def test_every_category_and_control_boundary_returns_finite_data(spec):
    base = {"scenario": spec["id"]}
    cases = [base]
    for c in spec["controls"]:
        cases.extend({**base, c["key"]: edge} for edge in (c["min"], c["max"]))
    for settings in cases:
        p = build_workspace(settings)
        json.dumps(p, allow_nan=False)
        assert len(p["catalog"]) == 10
        assert len(p["lessons"]) == 4
        if spec["id"] != "sun_mass":
            assert p["kind"] == "scenario"
            assert len(p["curve"]) >= 2
            assert p["result"]["limitation"]
            assert p["result"]["formula"]
            assert p["result"]["headline"] in p["observation_starter"]


def test_existing_orbit_settings_and_results_are_preserved():
    settings = {"mass": .5, "radius": 1.5, "model": "impulse", "step": .5}
    old, new = build_experiment(settings), build_workspace(settings)
    for field in old:
        assert new[field] == old[field]
    assert new["elements"]["period_days"] is None


@pytest.mark.parametrize("settings", [[], True, "blackhole", {"scenario": []}, {"scenario": "unknown"},
    {"scenario":"blackhole","distance":0}, {"scenario":"blackhole","mass":True},
    {"scenario":"blackhole","mass":float("nan")}, {"scenario":"sirius","distance":float("inf")},
    {"scenario":"atmosphere_loss","atmosphere":101}, {"scenario":"magnetic_field","field":-1}])
def test_invalid_settings_fail_with_readable_error(settings):
    with pytest.raises(ValueError):
        validate_workspace(settings)


def test_blackhole_inverse_square_and_inverse_cube_laws():
    a = build_workspace({"scenario":"blackhole","mass":10,"distance":1})["result"]["metrics"]
    b = build_workspace({"scenario":"blackhole","mass":10,"distance":2})["result"]["metrics"]
    assert a[0]["value"] == pytest.approx(10)
    assert a[0]["value"]/b[0]["value"] == pytest.approx(4)
    assert a[1]["value"]/b[1]["value"] == pytest.approx(8)
    assert a[2]["value"] == pytest.approx(29.53)
    assert a[2]["value"] == b[2]["value"]


def test_curve_keeps_secondary_distance_fixed():
    p = build_workspace({"scenario":"blackhole","distance":2})
    assert all(y == pytest.approx(x/4) for x,y in p["curve"])


def test_same_blackhole_mass_at_same_distance_has_solar_gravity():
    p = build_workspace({"scenario":"blackhole","mass":1,"distance":1})
    assert p["result"]["metrics"][0]["value"] == 1
    assert "즉시 빨려" in p["result"]["limitation"]


def test_doubled_earth_mass_doubles_weight_not_body_mass():
    a = build_workspace({"scenario":"earth_mass","mass":100})["result"]["metrics"]
    b = build_workspace({"scenario":"earth_mass","mass":200})["result"]["metrics"]
    assert b[0]["value"] == pytest.approx(2*a[0]["value"])
    assert b[1]["value"] == pytest.approx(2*a[1]["value"])
    assert b[2]["value"] == pytest.approx(math.sqrt(2)*a[2]["value"])


def test_faster_rotation_reduces_effective_equatorial_gravity():
    a = build_workspace({"scenario":"earth_rotation","hours":24})["result"]["metrics"]
    b = build_workspace({"scenario":"earth_rotation","hours":12})["result"]["metrics"]
    assert b[1]["value"] < a[1]["value"]
    assert b[2]["value"] == pytest.approx(2*a[2]["value"])


def test_climate_baselines_agree_across_experiments():
    scenarios = [("earth_distance","distance",1), ("solar_luminosity","brightness",100),
                 ("earth_albedo","albedo",30.6), ("atmosphere_loss","atmosphere",100)]
    temps = []
    for kind, key, value in scenarios:
        metrics = build_workspace({"scenario":kind,key:value})["result"]["metrics"]
        temp = next(m for m in metrics if m["label"] == "모형 평균 온도")
        assert temp["value"] == pytest.approx(temp["baseline"])
        temps.append(temp["value"])
    assert max(temps)-min(temps) < 1e-8


def test_atmosphere_zero_removes_only_assumed_greenhouse_offset():
    full = build_workspace({"scenario":"atmosphere_loss","atmosphere":100})["result"]["metrics"][-1]["value"]
    zero = build_workspace({"scenario":"atmosphere_loss","atmosphere":0})["result"]["metrics"][-1]["value"]
    assert full-zero == pytest.approx(33.9)


def test_sirius_adds_light_instead_of_replacing_sun():
    a = build_workspace({"scenario":"sirius","distance":1})["result"]["metrics"][0]["value"]
    b = build_workspace({"scenario":"sirius","distance":2})["result"]["metrics"][0]["value"]
    assert a == pytest.approx(25.7)
    assert (a-1)/(b-1) == pytest.approx(4)


def test_magnetic_boundary_and_zero_field_are_not_dose_predictions():
    p = build_workspace({"scenario":"magnetic_field","field":50})
    assert p["result"]["metrics"][1]["value"] == pytest.approx(.5**(1/3))
    z = build_workspace({"scenario":"magnetic_field","field":0})
    assert "정의할 수 없어요" in z["result"]["headline"]
    assert "방사선량" in z["result"]["limitation"]
