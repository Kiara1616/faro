from scripts.diagnose_offline import check


def test_offline_check_reports_plan_without_network(tmp_path):
    (tmp_path / "fixtures").mkdir()
    (tmp_path / "fixtures" / "malla_demo.json").write_text("{}", encoding="utf-8")
    result = check(tmp_path)
    assert result["plan"] is True
    assert result["required_ok"] is False
