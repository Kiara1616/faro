"""Closed Spanish command parser for Faro's fictional MMU simulator.

This module only interprets text. Session, task state and action authorization
belong to the domain. It never infers a missing ID, product, quantity or unit.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from faro.domain import Command, Intent
from faro.plan import DemoPlan


@dataclass(frozen=True)
class ParseResult:
    status: str  # ok, unknown, ambiguous
    intent: str | None
    command: Command | None
    reason: str
    original: str
    normalized: str

    @property
    def ok(self) -> bool:
        return self.status == "ok"


# Deliberate aliases only. Control intents are parsed but are not yet handled
# by faro.domain; the coordinator routes them through session/confirmation logic.
_SIMPLE: dict[str, Intent | str] = {
    "consultar estado": Intent.CONSULTAR_ESTADO,
    "consultar plan": Intent.CONSULTAR_PLAN,
    "preparar carga": Intent.PREPARAR_CARGA,
    "extender brazo": Intent.EXTENDER_BRAZO,
    "extender manguera": Intent.EXTENDER_MANGUERA,
    "iniciar carga": Intent.INICIAR_CARGA,
    "pausar": Intent.PAUSAR,
    "retraer brazo": Intent.RETRAER_BRAZO,
    "retraer manguera": Intent.RETRAER_MANGUERA,
    "cerrar taladro": Intent.CERRAR_TALADRO,
    "siguiente taladro": Intent.SIGUIENTE_TALADRO,
    "cancelar": "cancelar_confirmacion",
    "confirmar": "confirmar",
    "cambiar a modo manual": "modo_manual",
    "cambiar a modo voz": "modo_voz",
}

_UNITS = {"kilos", "kilogramos"}
_SMALL = {
    1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco",
    6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez",
    11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince",
    16: "dieciseis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve",
    20: "veinte", 21: "veintiuno", 22: "veintidos", 23: "veintitres",
    24: "veinticuatro", 25: "veinticinco", 26: "veintiseis",
    27: "veintisiete", 28: "veintiocho", 29: "veintinueve",
}
_TENS = {30: "treinta", 40: "cuarenta", 50: "cincuenta", 60: "sesenta",
         70: "setenta", 80: "ochenta", 90: "noventa"}
_HUNDREDS = {200: "doscientos", 300: "trescientos", 400: "cuatrocientos",
             500: "quinientos", 600: "seiscientos", 700: "setecientos",
             800: "ochocientos", 900: "novecientos"}


def _number_words(value: int) -> str:
    """Canonical Spanish cardinal spelling for the closed 1..999 demo range."""
    if value in _SMALL:
        return _SMALL[value]
    if value < 100:
        tens, units = divmod(value, 10)
        head = _TENS[tens * 10]
        return head if units == 0 else f"{head} y {_SMALL[units]}"
    if value == 100:
        return "cien"
    hundreds, remainder = divmod(value, 100)
    head = "ciento" if hundreds == 1 else _HUNDREDS[hundreds * 100]
    return head if remainder == 0 else f"{head} {_number_words(remainder)}"


_SPOKEN_KG = {_number_words(value): value for value in range(1, 1000)}


def _normalize(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.casefold())
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(folded.split())


def _result(status: str, intent: str | None, command: Command | None,
            reason: str, original: str, normalized: str) -> ParseResult:
    return ParseResult(status, intent, command, reason, original, normalized)


def parse_command(text: str, plan: DemoPlan, *, listening_active: bool = False) -> ParseResult:
    """Parse one complete phrase against the fixture's IDs and products.

    `listening_active` only permits removal of an optional initial address.
    The session boundary must independently verify source, mode and generation.
    """
    if not isinstance(text, str) or not isinstance(plan, DemoPlan) or type(listening_active) is not bool:
        raise TypeError("text, plan and listening_active must be str, DemoPlan and bool")
    original = text
    normalized = _normalize(text)
    if listening_active:
        normalized = re.sub(r"^(?:oye )?faro(?:,? +|,?$)", "", normalized, count=1).strip()

    if not normalized:
        return _result("unknown", None, None, "empty", original, normalized)
    if re.search(r"\b(?:no|nunca|jamas|tampoco|sin)\b", normalized):
        return _result("ambiguous", None, None, "negated", original, normalized)

    simple = _SIMPLE.get(normalized)
    if simple is not None:
        if isinstance(simple, Intent):
            return _result("ok", simple.value, Command(simple), "matched", original, normalized)
        return _result("ok", simple, None, "matched_control", original, normalized)

    ids = {hole.id for hole in plan.holes}
    spoken_ids = {
        _number_words(int(hole_id)): hole_id for hole_id in ids
        if 1 <= int(hole_id) < 1000
    }
    for verb, intent in (("seleccionar", Intent.SELECCIONAR_TALADRO),
                         ("consultar", Intent.CONSULTAR_TALADRO)):
        prefix = f"{verb} taladro "
        if normalized.startswith(prefix):
            raw_id = normalized[len(prefix):]
            hole_id = raw_id if raw_id in ids else spoken_ids.get(raw_id)
            if hole_id is None:
                return _result("ambiguous", intent.value, None, "unknown_or_incomplete_hole_id", original, normalized)
            return _result("ok", intent.value, Command(intent, hole_id=hole_id), "matched", original, normalized)

    if normalized.startswith("validar producto "):
        declaration = normalized[len("validar "):]
        product_names = {_normalize(hole.product): hole.product for hole in plan.holes}
        for product_key, product in product_names.items():
            prefix = product_key + " "
            comma_prefix = product_key + ", "
            if declaration.startswith(prefix) or declaration.startswith(comma_prefix):
                quantity = declaration[len(comma_prefix if declaration.startswith(comma_prefix) else prefix):]
                words = quantity.split()
                if len(words) < 2 or words[-1] not in _UNITS:
                    return _result("ambiguous", Intent.DECLARAR_PLAN.value, None,
                                   "missing_or_invalid_quantity_unit", original, normalized)
                raw_kg = " ".join(words[:-1])
                # A finite demo bound also prevents giant digit strings from
                # exhausting conversion time; larger values are not inferred.
                kg = (int(raw_kg) if len(raw_kg) <= 9 and re.fullmatch(r"[1-9][0-9]*", raw_kg)
                      else _SPOKEN_KG.get(raw_kg))
                if kg is None:
                    return _result("ambiguous", Intent.DECLARAR_PLAN.value, None,
                                   "invalid_or_incomplete_quantity", original, normalized)
                return _result("ok", Intent.DECLARAR_PLAN.value,
                               Command(Intent.DECLARAR_PLAN, product=product, kg=kg),
                               "matched", original, normalized)
        return _result("ambiguous", Intent.DECLARAR_PLAN.value, None,
                       "unknown_or_incomplete_product", original, normalized)

    if re.search(r"\b(?:y|luego|despues|tambien|ademas)\b|;", normalized):
        return _result("ambiguous", None, None, "compound", original, normalized)
    if normalized.startswith(("seleccionar taladro", "consultar taladro", "validar ")):
        return _result("ambiguous", None, None, "incomplete", original, normalized)
    return _result("unknown", None, None, "unknown_phrase", original, normalized)
