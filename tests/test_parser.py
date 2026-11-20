"""Closed command corpus: real simulator intents plus adversarial phrases."""

from pathlib import Path

import pytest

from faro.parser import parse_command
from faro.plan import load_demo_plan


PLAN = load_demo_plan(Path(__file__).resolve().parents[1] / "fixtures" / "malla_demo.json")


POSITIVE = [
    ("consultar estado", "consultar_estado", None, None, None, False),
    ("Consultar Estado", "consultar_estado", None, None, None, False),
    ("consultar plan", "consultar_plan", None, None, None, False),
    ("consultar taladro", "consultar_plan", None, None, None, False),
    ("preparar carga", "preparar_carga", None, None, None, False),
    ("extender brazo", "extender_brazo", None, None, None, False),
    ("extender manguera", "extender_manguera", None, None, None, False),
    ("iniciar carga", "iniciar_carga", None, None, None, False),
    ("pausar", "pausar", None, None, None, False),
    ("retraer brazo", "retraer_brazo", None, None, None, False),
    ("retraer manguera", "retraer_manguera", None, None, None, False),
    ("cerrar taladro", "cerrar_taladro", None, None, None, False),
    ("siguiente taladro", "siguiente_taladro", None, None, None, False),
    ("seleccionar taladro 101", "seleccionar_taladro", "101", None, None, False),
    ("seleccionar taladro ciento dos", "seleccionar_taladro", "102", None, None, False),
    ("seleccionar taladro 103", "seleccionar_taladro", "103", None, None, False),
    ("consultar taladro 101", "consultar_taladro", "101", None, None, False),
    ("consultar taladro ciento tres", "consultar_taladro", "103", None, None, False),
    ("validar producto alfa, 100 kilos", "declarar_plan", None, "producto alfa", 100, False),
    ("validar producto beta 120 kilogramos", "declarar_plan", None, "producto beta", 120, False),
    ("validar producto alfa, cien kilos", "declarar_plan", None, "producto alfa", 100, False),
    ("validar producto beta, ciento veinte kilos", "declarar_plan", None, "producto beta", 120, False),
    ("validar producto alfa, ochenta kilogramos", "declarar_plan", None, "producto alfa", 80, False),
    ("validar producto beta, 99 kilos", "declarar_plan", None, "producto beta", 99, False),
    ("validar producto alfa, treinta y cinco kilos", "declarar_plan", None, "producto alfa", 35, False),
    ("confirmar", "confirmar", None, None, None, False),
    ("cancelar", "cancelar_confirmacion", None, None, None, False),
    ("cambiar a modo manual", "modo_manual", None, None, None, False),
    ("cambiar a modo voz", "modo_voz", None, None, None, False),
    ("Oye Faro, consultar estado", "consultar_estado", None, None, None, True),
    ("Faro seleccionar taladro 101", "seleccionar_taladro", "101", None, None, True),
    ("  Faro   validar producto alfa, cien kilos  ", "declarar_plan", None, "producto alfa", 100, True),
]


NEGATIVE = [
    "", " ", "Faro", "Oye Faro", "Faro consultar estado",
    "Oye Faro seleccionar taladro 101", "no consultar estado", "nunca iniciar carga",
    "sin extender brazo", "tampoco retraer manguera", "no validar producto alfa, cien kilos",
    "extender brazo y cargar", "consultar estado y consultar plan",
    "seleccionar taladro 101 luego iniciar carga", "preparar carga; iniciar carga",
    "pausar y confirmar", "cambiar a modo voz y consultar estado",
    "seleccionar taladro", "seleccionar taladro 999",
    "consultar taladro ciento cuatro", "seleccionar taladro 10",
    "seleccionar taladro 101 102", "consultar taladro 101 ahora",
    "validar producto", "validar producto alfa", "validar producto alfa 100",
    "validar producto alfa, cien", "validar producto alfa, 0 kilos",
    "validar producto beta, -1 kilos", "validar producto beta, 1.5 kilos",
    "validar producto beta, 9999999999 kilos",
    "validar producto gamma, cien kilos", "validar producto alfa, 100 kg",
    "validar producto alfa, 100 kilos y cargar",
    "validar producto alfa, cien kilos iniciar carga",
    "validar producto alfa, veinte kilos luego confirmar",
    "extender brazo por favor", "activar detonador", "disparar",
    "iniciar bombeo", "seguro confirmar", "cancelar confirmacion",
]


@pytest.mark.parametrize("phrase,intent,hole_id,product,kg,listening", POSITIVE)
def test_positive_corpus(phrase, intent, hole_id, product, kg, listening):
    result = parse_command(phrase, PLAN, listening_active=listening)
    assert result.status == "ok", (phrase, result)
    assert result.intent == intent
    if result.command is not None:
        assert result.command.hole_id == hole_id
        assert result.command.product == product
        assert result.command.kg == kg
    else:
        assert intent in {"confirmar", "cancelar_confirmacion", "modo_manual", "modo_voz"}


@pytest.mark.parametrize("phrase", NEGATIVE)
def test_negative_corpus(phrase):
    result = parse_command(phrase, PLAN)
    assert result.status in {"unknown", "ambiguous"}, (phrase, result)
    assert result.command is None


def test_voice_address_requires_active_listening():
    assert parse_command("Oye Faro, confirmar", PLAN, listening_active=True).intent == "confirmar"
    rejected = parse_command("Oye Faro, confirmar", PLAN, listening_active=False)
    assert rejected.command is None and rejected.status != "ok"


def test_no_inference_from_partial_plan_and_no_gate_from_wake_address():
    partial = parse_command("validar producto alfa, cien", PLAN, listening_active=True)
    assert partial.command is None
    assert parse_command("Faro", PLAN, listening_active=True).status == "unknown"
    assert parse_command("no extender brazo", PLAN, listening_active=True).reason == "negated"


def test_fixture_ids_and_products_are_enforced():
    assert {hole.id for hole in PLAN.holes} == {"101", "102", "103"}
    assert parse_command("seleccionar taladro 999", PLAN).command is None
    assert parse_command("validar producto gamma, 100 kilos", PLAN).command is None
