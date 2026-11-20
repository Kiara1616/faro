"""Retired indicator-review prototype, retained for historical reference.

This module is not used by the active per-hole Faro application. Its readings
and workflow are fictional; it has no equipment or industrial interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
import unicodedata


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text.casefold())
    ascii_text = "".join(ch for ch in ascii_text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", ascii_text)).strip()


def _without_invocation(text: str) -> str:
    """Allow an optional spoken address after listening was enabled explicitly."""
    return re.sub(
        r"^\s*(?:oye\s+)?faro(?:\s*[,.:;]\s*|\s+|$)",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )


def _parse_record(text: str) -> tuple[str, float] | None:
    """Accept one indicator, one number and its explicit unit; never guess."""
    # Speech recognizers commonly return number words. These are the three
    # fictional demo readings only; free-form number interpretation would
    # create avoidable ambiguity in a voice command.
    spoken_demo_values = {
        "registrar temperatura cuarenta y dos grados": ("temperatura", 42.0),
        "registrar presion cuatro coma dos bar": ("presion", 4.2),
        "registrar bateria ochenta y siete por ciento": ("bateria", 87.0),
    }
    matched_demo = spoken_demo_values.get(_normalize(text))
    if matched_demo is not None:
        return matched_demo
    folded = unicodedata.normalize("NFKD", text.casefold())
    folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
    match = re.fullmatch(
        r"\s*registrar\s+(temperatura|presion|bateria)\s+"
        r"(-?\d+(?:[.,]\d+)?)\s+(grados?|bar|por\s+ciento|porciento|%)\s*",
        folded,
    )
    if not match:
        return None
    key, number, unit = match.groups()
    expected_units = {
        "temperatura": {"grado", "grados"},
        "presion": {"bar"},
        "bateria": {"por ciento", "porciento", "%"},
    }
    if unit not in expected_units[key]:
        return None
    return key, float(number.replace(",", "."))


@dataclass(frozen=True)
class Decision:
    accepted: bool
    intent: str
    message: str
    transcript: str
    timestamp: str
    snapshot: dict


@dataclass
class FaroEngine:
    """State machine for a small, explicitly allowed set of Spanish commands."""

    view: str = "estado"
    review_active: bool = False
    review_step: int = 0
    review_completed: bool = False
    inspected: bool = False
    recorded: bool = False
    requires_human: bool = False
    inspected_reading: tuple | None = None
    db_path: str | Path | None = None
    history: list[dict] = field(default_factory=list)
    indicators: dict = field(default_factory=lambda: {
        "temperatura": {"value": 42, "unit": "°C", "status": "vigente", "source": "simulador"},
        "presion": {"value": 4.2, "unit": "bar", "status": "vigente", "source": "simulador"},
        "bateria": {"value": 87, "unit": "%", "status": "vigente", "source": "simulador"},
    })

    STEPS = ("temperatura", "presion", "bateria")
    DEMO_TOLERANCE = {"temperatura": 1.0, "presion": 0.2, "bateria": 2.0}
    COMMANDS = (
        "mostrar estado", "mostrar indicadores", "iniciar revision auxiliar",
        "consultar temperatura", "consultar presion", "consultar bateria",
        "confirmar paso", "siguiente paso", "cancelar revision", "ver historial", "mostrar revision",
    )

    def __post_init__(self) -> None:
        for item in self.indicators.values():
            item.setdefault("updated_at", _now())
        if self.db_path is not None:
            with sqlite3.connect(self.db_path) as connection:
                connection.execute(
                    "CREATE TABLE IF NOT EXISTS decisions ("
                    "id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, transcript TEXT NOT NULL, "
                    "intent TEXT NOT NULL, accepted INTEGER NOT NULL, decision TEXT NOT NULL, "
                    "step INTEGER NOT NULL, source TEXT NOT NULL DEFAULT 'text')"
                )
                columns = {row[1] for row in connection.execute("PRAGMA table_info(decisions)")}
                if "source" not in columns:
                    connection.execute("ALTER TABLE decisions ADD COLUMN source TEXT NOT NULL DEFAULT 'text'")
                if not self.history:
                    rows = connection.execute(
                        "SELECT timestamp, transcript, intent, accepted, decision, step, source "
                        "FROM decisions ORDER BY id"
                    ).fetchall()
                    self.history = [
                        {"timestamp": row[0], "transcript": row[1], "intent": row[2],
                         "accepted": bool(row[3]), "decision": row[4], "step": row[5], "source": row[6]}
                        for row in rows
                    ]

    def _reading_signature(self, key: str) -> tuple:
        item = self.indicators[key]
        return (item["value"], item["unit"], item["status"], item["updated_at"])

    def _clear_observation(self) -> None:
        self.inspected = False
        self.recorded = False
        self.inspected_reading = None

    def snapshot(self) -> dict:
        step = self.STEPS[self.review_step] if self.review_active and self.review_step < len(self.STEPS) else None
        return {
            "view": self.view,
            "simulation_only": True,
            "indicators": {key: dict(value) for key, value in self.indicators.items()},
            "workflow": {
                "active": self.review_active,
                "step": self.review_step + 1 if self.review_active else 0,
                "total": len(self.STEPS),
                "label": step or ("Revisión completada" if self.review_completed else "Sin revisión activa"),
                "completed": self.review_completed,
                "inspected": self.inspected,
                "recorded": self.recorded,
                "requires_human": self.requires_human,
            },
            "history": [dict(item) for item in self.history],
        }

    def handle(self, text: str, *, source: str = "text") -> Decision:
        if source not in {"text", "voice"}:
            raise ValueError("source must be 'text' or 'voice'")
        original = text if isinstance(text, str) else ""
        addressed_command = _without_invocation(original)
        command = _normalize(addressed_command)
        record = _parse_record(addressed_command)
        accepted = False
        intent = "desconocido"
        step_before = self.review_step + 1 if self.review_active else 0

        if not command:
            message = "No se recibió un comando completo. Repita la instrucción."
        elif command not in self.COMMANDS and not command.startswith("registrar "):
            message = "Comando no permitido o ambiguo. No se realizó ningún cambio."
        elif command.startswith("registrar "):
            intent = "registrar_indicador"
            if record is None:
                message = "Registro ambiguo: diga un único indicador, valor y unidad. No se guardó el valor."
            elif not self.review_active:
                message = "Inicie la revisión auxiliar antes de registrar un valor."
            elif self.requires_human:
                message = "Hay una discrepancia pendiente de verificación humana. No se guardó el valor."
            elif record[0] != self.STEPS[self.review_step]:
                message = f"El paso actual es {self.STEPS[self.review_step]}; no se guardó el valor."
            elif not self.inspected:
                message = "Consulte el indicador actual antes de registrar un valor."
            elif self.indicators[record[0]]["status"] != "vigente":
                self._clear_observation()
                message = "El dato de referencia no está vigente; se requiere verificación humana."
            elif self.inspected_reading != self._reading_signature(record[0]):
                self._clear_observation()
                message = "El indicador cambió desde la consulta; vuelva a consultarlo antes de registrar."
            else:
                key, declared = record
                reference = self.indicators[key]["value"]
                if abs(declared - reference) > self.DEMO_TOLERANCE[key]:
                    self.requires_human = True
                    message = (
                        f"Discrepancia en {key}: se declaró {declared:g} frente a "
                        f"{reference:g} del simulador. No se guardó el valor; verificación humana requerida."
                    )
                else:
                    self.recorded = True
                    accepted = True
                    message = f"Valor ficticio de {key} registrado dentro de la tolerancia de demostración."
        elif command == "mostrar estado":
            intent, accepted, message = "mostrar_estado", True, "Mostrando estado ficticio de la unidad."
            self.view = "estado"
        elif command == "mostrar indicadores":
            intent, accepted, message = "mostrar_indicadores", True, "Mostrando indicadores ficticios."
            self.view = "indicadores"
        elif command == "mostrar revision":
            intent = "mostrar_revision"
            if self.review_active or self.review_completed:
                self.view = "revision"
                accepted, message = True, "Mostrando revisión auxiliar simulada."
            else:
                message = "No hay una revisión activa ni completada para mostrar."
        elif command == "ver historial":
            intent, accepted, message = "ver_historial", True, "Mostrando historial de decisiones."
        elif command == "iniciar revision auxiliar":
            intent = "iniciar_revision"
            if self.review_active:
                message = "Ya hay una revisión activa."
            else:
                self.review_active = True
                self.review_completed = False
                self.review_step = 0
                self._clear_observation()
                self.requires_human = False
                self.view = "revision"
                accepted, message = True, "Revisión auxiliar simulada iniciada. Consulte temperatura."
        elif command.startswith("consultar "):
            intent = "consultar_indicador"
            key = command.removeprefix("consultar ")
            if not self.review_active:
                message = "Inicie la revisión auxiliar antes de consultar un paso."
            elif key != self.STEPS[self.review_step]:
                message = f"El paso actual es {self.STEPS[self.review_step]}; no se avanzó."
            elif self.indicators[key]["status"] != "vigente":
                self._clear_observation()
                message = f"El dato de {key} no está vigente; se requiere verificación humana."
            elif self.requires_human:
                message = "Hay una discrepancia pendiente de verificación humana."
            else:
                self.inspected = True
                self.recorded = False
                self.inspected_reading = self._reading_signature(key)
                item = self.indicators[key]
                accepted = True
                message = f"{key.capitalize()}: {item['value']} {item['unit']} (dato ficticio del simulador)."
        elif command == "confirmar paso":
            intent = "confirmar_paso"
            if not self.review_active:
                message = "No hay una revisión activa."
            elif self.requires_human:
                message = "Hay una discrepancia pendiente de verificación humana."
            elif not self.inspected or not self.recorded:
                message = "Consulte y registre el indicador del paso actual antes de confirmarlo."
            elif self.indicators[self.STEPS[self.review_step]]["status"] != "vigente":
                self._clear_observation()
                message = "El indicador no está vigente; no se confirmó el paso."
            elif self.inspected_reading != self._reading_signature(self.STEPS[self.review_step]):
                self._clear_observation()
                message = "El indicador cambió desde la consulta; vuelva a consultarlo y registrarlo."
            else:
                self.review_step += 1
                self._clear_observation()
                accepted = True
                if self.review_step == len(self.STEPS):
                    self.review_active = False
                    self.review_completed = True
                    message = "Revisión auxiliar simulada completada."
                else:
                    message = f"Paso confirmado. Consulte {self.STEPS[self.review_step]}."
        elif command == "siguiente paso":
            intent = "siguiente_paso"
            message = "Confirme el indicador actual para avanzar; no se omitió ningún paso." if self.review_active else "No hay una revisión activa."
        elif command == "cancelar revision":
            intent = "cancelar_revision"
            if self.review_active:
                self.review_active = False
                self.review_completed = False
                self.review_step = 0
                self._clear_observation()
                self.requires_human = False
                self.view = "estado"
                accepted, message = True, "Revisión auxiliar simulada cancelada."
            else:
                message = "No hay una revisión activa."
        else:
            message = "Comando no permitido. No se realizó ningún cambio."

        stamp = _now()
        event = {
            "timestamp": stamp,
            "transcript": original,
            "intent": intent,
            "accepted": accepted,
            "decision": message,
            "step": step_before,
            "source": source,
        }
        self.history.append(event)
        if self.db_path is not None:
            with sqlite3.connect(self.db_path) as connection:
                connection.execute(
                    "INSERT INTO decisions(timestamp, transcript, intent, accepted, decision, step, source) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (stamp, original, intent, int(accepted), message, event["step"], source),
                )
        return Decision(accepted, intent, message, original, stamp, self.snapshot())
