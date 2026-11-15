from scripts.verify_demo_scenarios import verify


def test_demo_scenarios_cover_two_holes_and_injected_failure():
    report = verify()
    assert report["simulation_only"] is True
    assert report["normal"]["completed_holes"] == ["101", "102"]
    assert report["normal"]["state"] == "cerrado"
    assert report["normal"]["terminal_events"] == ["completed"] * 6
    assert report["failure"]["failed"] is True
    assert report["failure"]["terminal_events"] == ["failed"]
