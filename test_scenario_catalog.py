from solar_system_sim_v2_openai import PLANETS, SimulationEngine
from scenario_catalog import CATEGORY_LABELS, SCENARIO_PRESETS, presets_for, run_preset


def test_catalog_has_exactly_100_unique_scenarios():
    assert len(SCENARIO_PRESETS) == 100
    assert len({item["id"] for item in SCENARIO_PRESETS}) == 100
    assert len({item["title"] for item in SCENARIO_PRESETS}) == 100


def test_every_category_has_scenarios():
    assert {item["type"] for item in SCENARIO_PRESETS} == set(CATEGORY_LABELS)
    assert all(presets_for(category) for category in CATEGORY_LABELS)


def test_all_presets_run_through_engine():
    engine = SimulationEngine(PLANETS)
    for preset in SCENARIO_PRESETS:
        result = run_preset(engine, preset)
        assert result["type"] == preset["type"]
        assert "results" in result
