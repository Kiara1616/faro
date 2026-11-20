"""Touch-friendly local web console for Faro's fictional simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import threading
import time
from typing import Any

from faro.controller import FaroController
from faro.domain import State
from faro.plan import DemoPlan, load_demo_plan
from faro.scenarios import Scenario, load_scenarios
from faro.simulator import SimEvent, SimStatus


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_LABELS = {
    State.SIN_SELECCION: "Sin taladro seleccionado",
    State.SELECCIONADO: "Taladro seleccionado",
    State.CONSULTADO: "Plan consultado",
    State.PREPARADO: "Preparación lista",
    State.CONFIRMACION_PENDIENTE: "Confirmación requerida",
    State.MOVIMIENTO_EN_CURSO: "Movimiento en curso",
    State.POSICIONADO: "En posición",
    State.CARGA_EN_CURSO: "Carga en curso",
    State.CARGADO: "Carga simulada completa",
    State.RETRACCION_EN_CURSO: "Retracción en curso",
    State.RETRAIDO: "Retraído",
    State.CERRADO: "Taladro cerrado",
    State.FALLO: "Revisión requerida",
    State.RESULTADO_DESCONOCIDO: "Resultado desconocido",
}
REASON_LABELS = {
    "fictional_zone_occupied": "La zona de movimiento figura ocupada en este escenario.",
    "plan_mismatch": "El producto o la cantidad no coincide con el plan ficticio.",
    "hole_blocked": "Ese taladro está bloqueado en el plan de demostración.",
    "no_hole_selected": "Selecciona un taladro antes de continuar.",
    "hole_mismatch": "La instrucción menciona un taladro distinto al activo.",
    "wrong_state": "Ese paso todavía no corresponde en el recorrido.",
    "not_prepared_or_validated": "Completa preparación y validación antes de solicitar movimiento.",
    "wrong_delivery_method": "El método de entrega no coincide con el plan ficticio.",
    "not_positioned_or_validated": "Completa la extensión simulada antes de iniciar la carga.",
    "not_retracted": "Retrae el brazo o la manguera antes de cerrar el taladro.",
    "hole_not_closed": "Cierra el taladro actual antes de avanzar.",
    "end_of_plan": "No quedan más taladros disponibles en este plan.",
    "confirmation_expired": "La confirmación venció. Revisa el estado antes de continuar.",
    "confirmation_context_changed": "El contexto cambió; la orden requiere una nueva revisión.",
    "no_confirmation_pending": "No hay una orden pendiente de confirmación.",
    "submitted": "Orden aceptada; esperando el resultado de la simulación.",
    "confirmed": "Confirmación registrada; la simulación está en curso.",
    "confirmation_cancelled": "Orden pendiente cancelada; no se envió al simulador.",
    "hole_selected": "Taladro seleccionado.",
    "plan_consulted": "Plan consultado.",
    "prepared": "Preparación registrada.",
    "plan_validated": "Producto y cantidad coinciden con el plan ficticio.",
    "hole_closed": "Taladro cerrado en la simulación.",
    "select_next_hole": "Siguiente taladro disponible; selección explícita requerida.",
}
SCENARIO_LABELS = {
    "normal": "Flujo normal",
    "zona_ocupada": "Zona ocupada",
    "fallo_brazo": "Fallo de brazo",
    "demora_timeout": "Demora y revisión",
    "adaptador_lento": "Respuesta demorada",
}
EVENT_LABELS = {
    SimStatus.IN_PROGRESS: ("Acción en curso", "La simulación todavía está ejecutando el paso."),
    SimStatus.COMPLETED: ("Acción completada", "El simulador confirmó el resultado para el taladro activo."),
    SimStatus.FAILED: ("Acción fallida", "La simulación se detuvo y requiere revisión."),
    SimStatus.CANCELLED: ("Acción cancelada", "El simulador confirmó la cancelación."),
    SimStatus.TIMEOUT: ("Sin respuesta", "El resultado es desconocido; revisa antes de continuar."),
}


def _reason_text(reason: str) -> str:
    if reason in REASON_LABELS:
        return REASON_LABELS[reason]
    return reason.replace("_", " ").strip().capitalize() or "No se aceptó la instrucción."


def _scenario_from_environment(scenarios: dict[str, Scenario]) -> Scenario:
    requested = os.environ.get("FARO_SCENARIO", "normal")
    return scenarios.get(requested, scenarios["normal"])


@dataclass
class WebConsole:
    """One shared demo session with a lock around controller and audit access."""

    plan: DemoPlan
    controller: FaroController
    scenario: Scenario
    history: list[dict[str, Any]] = field(default_factory=list)
    last_message: dict[str, str] = field(default_factory=lambda: {
        "text": "Selecciona el taladro sugerido para comenzar.", "tone": "info"
    })
    last_sim_action: str = ""
    zone_clear: bool = False
    lock: threading.RLock = field(default_factory=threading.RLock, repr=False)
    last_tick_at: float = field(default_factory=time.monotonic, repr=False)

    @classmethod
    def create(cls, root: str | Path = PROJECT_ROOT,
               audit_path: str | Path | None = None,
               scenario_name: str | None = None) -> "WebConsole":
        root = Path(root)
        plan = load_demo_plan(root / "fixtures" / "malla_demo.json")
        scenarios = load_scenarios(root / "fixtures" / "escenarios_demo.json")
        if scenario_name is None:
            scenario = _scenario_from_environment(scenarios)
        else:
            scenario = scenarios.get(scenario_name)
            if scenario is None:
                raise ValueError(f"Unknown demo scenario: {scenario_name}")
        database = Path(audit_path) if audit_path else root / "faro-web-audit.sqlite3"
        controller = FaroController.create(plan, database, scenario=scenario)
        return cls(plan=plan, controller=controller, scenario=scenario)

    def execute_command(self, command_text: str) -> dict[str, Any]:
        command_text = command_text.strip()
        if not command_text:
            raise ValueError("Escribe una instrucción antes de enviarla.")
        with self.lock:
            result = self.controller.process(command_text,
                                            zone_clear=(self.zone_clear
                                                        and self.controller.zone_clear_available))
            decision = result.decision
            accepted = bool(decision and decision.accepted)
            intent = result.parsed.intent or "instrucción"
            reason = decision.reason if decision is not None else result.parsed.reason
            if decision is not None and decision.request is not None:
                self.last_sim_action = decision.request.action
            if accepted and reason == "submitted" and self.controller.confirmation_pending:
                text = self._confirmation_text()
            elif accepted:
                text = _reason_text(reason)
            else:
                text = _reason_text(reason)
            tone = "success" if accepted else "rejected"
            self.last_message = {"text": text, "tone": tone}
            self._record(
                title=command_text,
                detail=("Aceptada · " if accepted else "Rechazada · ") + _reason_text(reason),
                accepted=accepted,
            )
            return self._snapshot_unlocked()

    def set_zone_clear(self, enabled: bool) -> dict[str, Any]:
        with self.lock:
            self.zone_clear = bool(enabled) and self.controller.zone_clear_available
            if self.zone_clear:
                text = "Zona marcada como despejada para esta simulación. No proviene de un sensor."
                tone = "info"
            elif self.controller.zone_clear_available:
                text = "La zona simulada no está marcada como despejada."
                tone = "info"
            else:
                text = "Este escenario mantiene la zona simulada ocupada."
                tone = "rejected"
            self.last_message = {"text": text, "tone": tone}
            return self._snapshot_unlocked()

    def recover_unknown(self) -> dict[str, Any]:
        with self.lock:
            recovered = self.controller.recover_unknown("revisión manual en consola web")
            if recovered:
                text = "Revisión registrada. No se repitió la orden; el recorrido permanece detenido."
                self.last_message = {"text": text, "tone": "info"}
                self._record(title="Revisión manual", detail=text, accepted=True)
            else:
                self.last_message = {
                    "text": "No hay un resultado desconocido que requiera esta revisión.",
                    "tone": "rejected",
                }
            return self._snapshot_unlocked()

    def advance_if_due(self, interval: float = 0.65) -> dict[str, Any]:
        with self.lock:
            now = time.monotonic()
            if now - self.last_tick_at >= interval:
                self.last_tick_at = now
                pending_action = self.controller.domain.pending
                if pending_action is not None:
                    self.last_sim_action = pending_action.action
                event = self.controller.tick()
                if event is not None:
                    title, detail = EVENT_LABELS.get(
                        event.status,
                        ("Estado actualizado", _reason_text(event.reason)),
                    )
                    accepted = event.status not in {SimStatus.FAILED, SimStatus.TIMEOUT}
                    tone = "success" if event.status is SimStatus.COMPLETED else (
                        "rejected" if not accepted else "info"
                    )
                    self.last_message = {"text": f"{title}: {detail}", "tone": tone}
                    self._record(title=title, detail=detail, accepted=accepted)
            return self._snapshot_unlocked()

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return self._snapshot_unlocked()

    def _record(self, *, title: str, detail: str, accepted: bool) -> None:
        self.history.append({
            "time": datetime.now().astimezone().strftime("%H:%M:%S"),
            "title": title[:100],
            "detail": detail,
            "accepted": accepted,
        })
        del self.history[:-30]

    def _confirmation_text(self) -> str:
        pending = self.controller.confirmation_snapshot() or {}
        action = str(pending.get("action", "orden")).replace("_", " ")
        return f"Taladro {pending.get('hole_id', '—')}: revisa y confirma {action}."

    def _suggestion(self) -> dict[str, str]:
        domain = self.controller.domain
        state = domain.state
        pending = self.controller.confirmation_snapshot()
        if pending:
            return {
                "title": "Revisar la orden pendiente",
                "description": self._confirmation_text(),
                "command": "",
                "button_label": "Usa Confirmar o Cancelar",
            }
        if state in {State.FALLO, State.RESULTADO_DESCONOCIDO}:
            return {
                "title": "Recorrido detenido",
                "description": "Revisa el estado y la bitácora antes de iniciar otro paso.",
                "command": "",
                "button_label": "Se requiere revisión",
            }
        hole = domain.selected_hole
        if state is State.SIN_SELECCION:
            target_id = domain.expected_next_hole_id
            target = next((item for item in self.plan.holes if item.id == target_id), None)
            if target is None:
                target = next((item for item in self.plan.holes
                               if not item.blocked and item.id not in domain.completed_holes), None)
            if target is None:
                return {
                    "title": "Recorrido completo",
                    "description": "No quedan taladros disponibles en el plan.",
                    "command": "",
                    "button_label": "Plan completado",
                }
            return {
                "title": f"Seleccionar taladro {target.id}",
                "description": "Empieza con el siguiente taladro disponible del plan.",
                "command": f"seleccionar taladro {target.id}",
                "button_label": "Comenzar recorrido" if not domain.completed_holes else "Seleccionar taladro",
            }
        if hole is None:
            return {
                "title": "Consulta el estado",
                "description": "El estado actual no tiene un taladro asociado.",
                "command": "consultar estado",
                "button_label": "Consultar estado",
            }
        commands = {
            State.SELECCIONADO: (f"consultar taladro {hole.id}", "Consultar el plan", "Revisa el producto, la cantidad y el método previstos."),
            State.CONSULTADO: ("preparar carga", "Preparar carga", "Deja listo el paso de preparación del recorrido."),
            State.POSICIONADO: ("iniciar carga", "Iniciar carga simulada", "Solicita la carga del taladro según el plan ficticio."),
            State.CARGADO: (f"retraer {hole.delivery_method}", "Retraer equipo", "Retrae el método de entrega antes de cerrar el taladro."),
            State.RETRAIDO: ("cerrar taladro", "Cerrar taladro", "Registra el cierre de este taladro en la simulación."),
            State.CERRADO: ("siguiente taladro", "Avanzar al siguiente", "Continúa con el próximo taladro disponible."),
        }
        if state is State.PREPARADO and not domain.plan_validated:
            command = f"validar {hole.product} {hole.planned_kg} kilos"
            return {
                "title": "Validar producto y cantidad",
                "description": "Compara los datos con el plan antes de solicitar el movimiento.",
                "command": command,
                "button_label": "Validar datos",
            }
        if state is State.PREPARADO and domain.plan_validated:
            return {
                "title": f"Extender {hole.delivery_method}",
                "description": "Marca la zona ficticia como despejada; después confirma la orden.",
                "command": f"extender {hole.delivery_method}",
                "button_label": "Solicitar extensión",
            }
        if state is State.CERRADO:
            command, title, description = commands[state]
            return {"title": title, "description": description,
                    "command": command, "button_label": "Continuar recorrido"}
        if state in commands:
            command, title, description = commands[state]
            return {"title": title, "description": description,
                    "command": command, "button_label": "Continuar"}
        if state in {State.MOVIMIENTO_EN_CURSO, State.CARGA_EN_CURSO, State.RETRACCION_EN_CURSO}:
            return {
                "title": "Esperando el simulador",
                "description": "El resultado aparecerá aquí cuando la simulación termine.",
                "command": "",
                "button_label": "Acción en curso",
            }
        return {
            "title": "Esperando el siguiente paso",
            "description": "Consulta el estado del taladro para continuar.",
            "command": "consultar estado",
            "button_label": "Consultar estado",
        }

    def _snapshot_unlocked(self) -> dict[str, Any]:
        domain = self.controller.domain
        selected = domain.selected_hole
        completed = domain.completed_holes
        operable_count = sum(not hole.blocked for hole in self.plan.holes)
        plan_holes = []
        for hole in self.plan.holes:
            status = "Bloqueado" if hole.blocked else (
                "Completado" if hole.id in completed else (
                    "Activo" if selected and selected.id == hole.id else "Pendiente"
                )
            )
            plan_holes.append({
                "id": hole.id,
                "product": hole.product,
                "planned_kg": hole.planned_kg,
                "delivery_method": hole.delivery_method,
                "blocked": hole.blocked,
                "status": status,
            })
        action_steps = {
            "extender_brazo": 4,
            "extender_manguera": 4,
            "iniciar_carga": 5,
            "retraer_brazo": 6,
            "retraer_manguera": 6,
        }
        step_for_state = {
            State.SIN_SELECCION: 0,
            State.SELECCIONADO: 1,
            State.CONSULTADO: 2,
            State.PREPARADO: 3 if not domain.plan_validated else 4,
            State.CONFIRMACION_PENDIENTE: 4,
            State.MOVIMIENTO_EN_CURSO: 4,
            State.POSICIONADO: 5,
            State.CARGA_EN_CURSO: 5,
            State.CARGADO: 6,
            State.RETRACCION_EN_CURSO: 6,
            State.RETRAIDO: 7,
            State.CERRADO: 7,
            State.FALLO: action_steps.get(self.last_sim_action, 0),
            State.RESULTADO_DESCONOCIDO: action_steps.get(self.last_sim_action, 0),
        }
        step = step_for_state[domain.state]
        completed_steps = 8 if domain.state is State.CERRADO else step
        alert = None
        if domain.alert is not None:
            alert = {
                "message": _reason_text(domain.alert.reason),
                "blocking": domain.alert.blocking,
            }
        zone_clear = self.zone_clear and self.controller.zone_clear_available
        if not self.controller.zone_clear_available:
            zone_text = "ocupada (escenario)"
        else:
            zone_text = "despejada" if zone_clear else "pendiente de marcar"
        return {
            "plan": {
                "name": self.plan.name,
                "holes": plan_holes,
                "completed_count": len(completed),
                "available_count": operable_count,
            },
            "operation": {
                "hole_id": selected.id if selected else None,
                "hole_status": "Taladro activo" if selected else (
                    "Plan completado" if len(completed) == operable_count else "Sin selección"
                ),
                "product": selected.product if selected else None,
                "planned_kg": selected.planned_kg if selected else None,
                "delivery_method": selected.delivery_method if selected else None,
                "state": domain.state.value,
            },
            "scenario": {
                "name": self.scenario.name,
                "label": SCENARIO_LABELS.get(self.scenario.name, "Escenario de demostración"),
                "zone_clear": zone_clear,
                "zone_clear_available": self.controller.zone_clear_available,
                "zone_label": f"Zona simulada: {zone_text}",
            },
            "progress": {
                "current_step": step,
                "completed_steps": completed_steps,
            },
            "suggestion": self._suggestion(),
            "confirmation": self.controller.confirmation_snapshot(),
            "alert": alert,
            "history": list(self.history),
            "last_message": dict(self.last_message),
        }


class FaroRequestHandler(BaseHTTPRequestHandler):
    """Small same-origin static/API server; it never connects to equipment."""

    console: WebConsole
    web_root: Path
    protocol_version = "HTTP/1.1"
    server_version = "FaroLocal/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        # Keep the console reserved for startup instructions and runtime errors.
        return

    def _headers(self, content_type: str, content_length: int) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; script-src 'self'; "
            "style-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("Connection", "close")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._headers("application/json; charset=utf-8", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, filename: str) -> None:
        path = self.web_root / filename
        if not path.is_file():
            self._send_json(404, {"error": "No encontrado."})
            return
        body = path.read_bytes()
        content_type = "font/woff2" if path.suffix == ".woff2" else (
            mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        )
        if content_type.startswith("text/") or content_type in {"application/javascript"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self._headers(content_type, len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/":
            self._send_file("index.html")
        elif self.path == "/app.js":
            self._send_file("app.js")
        elif self.path == "/style.css":
            self._send_file("style.css")
        elif self.path == "/assets/Inter-latin.woff2":
            self._send_file("assets/Inter-latin.woff2")
        elif self.path == "/api/state":
            self._send_json(200, self.console.advance_if_due())
        else:
            self._send_json(404, {"error": "No encontrado."})

    def do_POST(self) -> None:
        if self.headers.get("Origin") != f"http://{self.headers.get('Host', '')}":
            self._send_json(403, {"error": "Origen de la solicitud no permitido."})
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self._send_json(415, {"error": "Se requiere una solicitud JSON."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > 4096:
            self._send_json(400, {"error": "Tamaño de solicitud no válido."})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError
            if self.path == "/api/command":
                command = payload.get("command")
                if not isinstance(command, str):
                    raise ValueError
                state = self.console.execute_command(command)
            elif self.path == "/api/recover":
                state = self.console.recover_unknown()
            elif self.path == "/api/zone-clear":
                enabled = payload.get("enabled")
                if type(enabled) is not bool:
                    raise ValueError("El estado de la zona debe ser verdadero o falso.")
                state = self.console.set_zone_clear(enabled)
            else:
                self._send_json(404, {"error": "No encontrado."})
                return
        except ValueError as error:
            message = str(error) or "El cuerpo de la solicitud no es válido."
            self._send_json(400, {"error": message})
            return
        self._send_json(200, state)


def create_request_handler(console: WebConsole, web_root: str | Path) -> type[FaroRequestHandler]:
    """Bind one console instance to a handler class for the local server."""
    return type(
        "BoundFaroRequestHandler",
        (FaroRequestHandler,),
        {"console": console, "web_root": Path(web_root)},
    )


def serve_web(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Serve the tablet-ready interface on localhost or an opted-in LAN host."""
    console = WebConsole.create()
    handler = create_request_handler(console, PROJECT_ROOT / "web")
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    print(f"Consola Faro disponible en http://{host}:{server.server_port}")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        print("En la tablet, abre http://<IPv4-de-este-equipo>:" + str(server.server_port))
        print("Usa la misma red Wi-Fi y conserva esta consola abierta durante la demostración.")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nConsola Faro detenida.")
    finally:
        server.server_close()
