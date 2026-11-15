from scripts.check_offline_boundary import violations


def test_runtime_has_no_network_client_boundary():
    assert violations() == []
