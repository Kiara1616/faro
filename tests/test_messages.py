from faro.messages import confirmation_prompt, execution_message


def test_messages_distinguish_progress_from_completion():
    progress = execution_message("101", "extender_brazo", "in_progress")
    completed = execution_message("101", "extender_brazo", "completed")
    assert "en curso" in progress and "completada" not in progress
    assert "completada" in completed and "simulación" in completed


def test_messages_include_hole_and_safe_failure_state():
    prompt = confirmation_prompt("102", "iniciar_carga")
    failed = execution_message("102", "iniciar_carga", "failed")
    assert "Taladro 102" in prompt and "confirmar" in prompt
    assert "revisar estado" in failed


def test_messages_include_cancelled_and_timeout_states():
    assert "cancelada" in execution_message("101", "extender_brazo", "cancelled")
    assert "sin respuesta" in execution_message("101", "extender_brazo", "timeout")
