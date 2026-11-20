from pathlib import Path

from faro.domain import EventStatus, FaroDomain, Mode, Source
from faro.parser import parse_command
from faro.plan import load_demo_plan
from faro.voice_pipeline import VoicePipeline


PLAN = load_demo_plan(Path(__file__).resolve().parents[1] / "fixtures" / "malla_demo.json")


def pipeline(mode=Mode.MANUAL):
    domain = FaroDomain(PLAN)
    assert domain.begin_session("demo-voice", "operador de prueba", mode)
    return domain, VoicePipeline(PLAN, domain)


def send(pipe, text, *, source=Source.TEXT, generation=None, zone_clear=False):
    return pipe.process(text, source=source, session_id="demo-voice",
                        generation=generation, zone_clear=zone_clear)


def test_unknown_text_never_reaches_domain():
    domain, pipe = pipeline()
    before = domain.snapshot()
    result = send(pipe, "hacer cualquier cosa")
    assert result.decision is None and not result.parsed.ok
    assert domain.snapshot() == before


def test_voice_commands_use_session_generation_and_same_domain_rules():
    domain, pipe = pipeline(Mode.VOZ)
    assert domain.set_listening("demo-voice", True)
    generation = domain.session.generation
    assert send(pipe, "Oye Faro, seleccionar taladro uno cero uno", source=Source.VOICE,
                generation=generation).decision.accepted
    assert send(pipe, "Oye Faro, consultar taladro 101", source=Source.VOICE,
                generation=generation).decision.accepted
    assert send(pipe, "Oye Faro, preparar carga", source=Source.VOICE,
                generation=generation).decision.accepted
    assert send(pipe, "Oye Faro, validar producto alfa, cien kilos", source=Source.VOICE,
                generation=generation).decision.accepted
    denied = send(pipe, "Oye Faro, extender brazo", source=Source.VOICE,
                  generation=generation, zone_clear=False)
    assert not denied.decision.accepted and denied.decision.reason == "fictional_zone_occupied"
    moving = send(pipe, "Oye Faro, extender brazo", source=Source.VOICE,
                  generation=generation, zone_clear=True)
    assert moving.decision.accepted
    assert domain.state.value == "movimiento_en_curso"
    assert not send(pipe, "Oye Faro, extender brazo", source=Source.VOICE,
                    generation=generation, zone_clear=True).decision.accepted


def test_stale_voice_and_manual_voice_are_rejected_without_mutation():
    domain, pipe = pipeline(Mode.VOZ)
    assert domain.set_listening("demo-voice", True)
    current = domain.session.generation
    assert domain.set_mode("demo-voice", Mode.MANUAL)
    before = domain.snapshot()
    stale = send(pipe, "consultar estado", source=Source.VOICE, generation=current)
    assert stale.decision is not None and not stale.decision.accepted
    assert stale.decision.reason == "voice_disabled_in_manual"
    assert domain.snapshot() == before


def test_partial_final_duplicate_are_not_forwarded_twice():
    domain, pipe = pipeline(Mode.MANUAL)
    first = send(pipe, "seleccionar taladro 101")
    assert first.decision.accepted
    duplicate = send(pipe, "seleccionar taladro 101")
    assert not duplicate.decision.accepted
    assert duplicate.decision.reason == "current_hole_not_closed"


def test_controls_produce_explicit_decisions_and_modes_change():
    domain, pipe = pipeline(Mode.MANUAL)
    mode = send(pipe, "cambiar a modo voz")
    assert mode.decision is not None and mode.decision.accepted
    assert domain.session.mode is Mode.VOZ
    assert domain.set_listening("demo-voice", True)
    denied = send(pipe, "confirmar", source=Source.VOICE,
                  generation=domain.session.generation)
    assert denied.decision is not None and not denied.decision.accepted
    assert denied.decision.reason == "confirmation_not_integrated"
