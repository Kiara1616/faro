from pathlib import Path


PITCH = Path(__file__).resolve().parents[1] / "planning" / "PITCH_5_MINUTOS.md"


def test_pitch_contains_flow_fallback_and_explicit_limits():
    text = PITCH.read_text(encoding="utf-8").casefold()
    required = (
        "flujo normal",
        "caso de seguridad",
        "respaldo si falla el micrófono",
        "no implementado",
        "no hay conectores",
        "simulador",
        "acta de ensayo",
        "pendiente",
    )
    for phrase in required:
        assert phrase in text, f"pitch perdió el límite o sección requerida: {phrase}"
    assert "reduce accidentes o ahorra tiempo" in text
    assert "hipótesis" in text
