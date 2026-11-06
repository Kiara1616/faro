import os

import pytest


pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from faro.ui import FaroWindow


@pytest.fixture(scope="module")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def test_manual_recovery_button_is_disabled_until_review(qt_app):
    window = FaroWindow()
    window.render_state({"command_status": "ejecución: timeout"})
    assert window.recovery_button.isEnabled()
    window.render_state({"command_status": "recuperado manualmente"})
    assert not window.recovery_button.isEnabled()
    window.close()
