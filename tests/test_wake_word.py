from faro.wake_word import WakeCommandGate


def test_ambient_speech_without_leading_wake_phrase_is_ignored():
    gate = WakeCommandGate()

    assert gate.consume("hola", now=0).status == "ignored"
    assert gate.consume("estaba conversando y oye faro consultar estado", now=1).status == "ignored"


def test_wake_phrase_and_command_in_one_utterance_passes_only_command():
    gate = WakeCommandGate()

    result = gate.consume("Oye Faro, consultar estado", now=0)

    assert result.status == "command"
    assert result.command == "consultar estado"


def test_wake_phrase_accepts_recognized_punctuation_between_words():
    gate = WakeCommandGate()

    result = gate.consume("Oye, Faro: consultar estado", now=0)

    assert result.status == "command"
    assert result.command == "consultar estado"


def test_standalone_wake_phrase_allows_exactly_one_following_utterance():
    gate = WakeCommandGate()

    assert gate.consume("Oye Faro", now=0).status == "activated"
    command = gate.consume("preparar carga", now=2)
    assert command.status == "command"
    assert command.command == "preparar carga"
    assert gate.consume("consultar estado", now=3).status == "ignored"


def test_wake_window_expires_and_can_be_reported_to_ui():
    gate = WakeCommandGate(command_window_seconds=6)

    assert gate.consume("Oye Faro", now=10).status == "activated"
    assert gate.expire(now=15.99) is False
    assert gate.expire(now=16) is True
    assert gate.consume("preparar carga", now=16).status == "ignored"


def test_repeating_standalone_wake_phrase_renews_window():
    gate = WakeCommandGate(command_window_seconds=6)

    assert gate.consume("Oye Faro", now=0).status == "activated"
    assert gate.consume("Oye Faro", now=5).status == "activated"
    assert gate.consume("consultar estado", now=10.9).status == "command"
