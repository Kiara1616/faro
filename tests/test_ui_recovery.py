import os

import pytest


pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from faro.ui import FaroWindow


@pytest.fixture(scope="module")
def qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app
    app.closeAllWindows()
    app.processEvents()


def test_manual_recovery_button_is_disabled_until_review(qt_app):
    window = FaroWindow()
    window.render_state({"command_status": "ejecución: timeout"})
    assert window.recovery_button.isEnabled()
    window.render_state({"confirmation": {
        "hole_id": "101", "action": "extender_brazo",
        "product": "producto alfa", "planned_kg": 100,
    }})
    assert window.workflow_status.text() == "CONFIRMACIÓN REQUERIDA"
    assert not window.confirmation_controls.isHidden()
    assert "taladro 101" in window.workflow_detail.text()
    assert "extender brazo" in window.workflow_detail.text()
    window.render_state({"command_status": "recuperado manualmente"})
    assert not window.recovery_button.isEnabled()
    assert window.confirmation_controls.isHidden()
    window.close()


def test_recovery_uses_operational_state_after_status_text_changes(qt_app):
    window = FaroWindow()
    window.render_state({"operation": {"state": "resultado_desconocido"},
                         "command_status": "condición ficticia de demostración"})
    assert window.recovery_button.isEnabled()
    window.render_state({"operation": {"state": "fallo"},
                         "command_status": "ejecución: timeout"})
    assert not window.recovery_button.isEnabled()
    window.close()


def test_console_contract_keeps_simulation_and_plan_context_visible(qt_app):
    window = FaroWindow()
    window.render_state({
        "operation": {"hole_id": "101", "product": "producto alfa",
                       "planned_kg": 100, "delivery_method": "brazo",
                       "scenario": "normal", "state": "en_curso"},
        "session": {"mode": "manual", "operator_label": "Operador de prueba",
                    "listening": False, "simulation_only": True},
        "workflow": {"active": True, "status": "EN CURSO", "label": "movimiento",
                      "step": 2, "total": 3, "scenario": "normal"},
        "command_status": "en curso",
        "history": [{"transcript": "extender brazo", "accepted": True,
                     "decision": "accepted", "state": "en_curso"}],
    })
    assert "PLAN Y EQUIPO SIMULADOS" in window.simulation_notice.text()
    assert window.manual_card.isHidden()
    assert "Espera el resultado" in window.next_command.text()
    assert window.workflow_status.text() == "EN CURSO"
    assert window.execution_status.text() == "Estado de ejecución: en curso"
    assert window.decision_state.text() == "ACEPTADO"
    window.close()


def test_console_contract_exposes_blocking_alert_without_color_only_signal(qt_app):
    window = FaroWindow()
    window.render_state({
        "workflow": {"active": True, "status": "RECHAZADO", "label": "validación"},
        "command_status": "rechazado",
        "alert": {"reason": "producto divergente", "blocking": True},
        "history": [{"transcript": "iniciar carga beta", "accepted": False,
                     "decision": "plan_mismatch", "state": "fallo"}],
    })
    assert "requiere revisión" in window.execution_status.text()
    assert "producto divergente" in window.execution_status.text()
    assert "BLOQUEANTE" in window.execution_status.text()
    assert window.decision_state.text() == "RECHAZADO"
    window.close()


def test_next_step_after_validation_points_to_movement(qt_app):
    window = FaroWindow()
    window.render_state({"operation": {
        "state": "preparado", "hole_id": "101", "product": "producto alfa",
        "planned_kg": 100, "delivery_method": "brazo", "plan_validated": True,
    }})
    assert "Simular zona despejada" in window.next_command.text()
    assert "extender brazo" in window.next_command.text()
    window.close()
