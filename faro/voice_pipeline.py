"""Bridge from local ASR text to the session-protected domain."""

from __future__ import annotations

from dataclasses import dataclass, replace

from faro.domain import Command, Decision, FaroDomain, Intent, Source
from faro.parser import ParseResult, parse_command
from faro.plan import DemoPlan


@dataclass(frozen=True)
class PipelineResult:
    transcript: str
    parsed: ParseResult
    decision: Decision | None


class VoicePipeline:
    """Pure orchestration boundary; it has no microphone, Qt or simulator access."""

    def __init__(self, plan: DemoPlan, domain: FaroDomain):
        if domain.plan != plan:
            raise ValueError("pipeline and domain must use the same demo plan")
        self.plan = plan
        self.domain = domain
        self.control_handler = None

    def process(self, transcript: str, *, source: Source, session_id: str,
                generation: int | None = None, zone_clear: bool = False) -> PipelineResult:
        listening = (source is Source.VOICE and self.domain.session is not None
                     and self.domain.session.session_id == session_id
                     and self.domain.session.listening)
        parsed = parse_command(transcript, self.plan, listening_active=listening)
        if not parsed.ok:
            return PipelineResult(transcript, parsed, None)
        if parsed.command is None:
            handler = self.control_handler or self.domain.handle_control
            decision = handler(parsed.intent or "unknown_control", session_id=session_id,
                               source=source, generation=generation)
            return PipelineResult(transcript, parsed, decision)
        command: Command = parsed.command
        if command.intent is Intent.PAUSAR and self.control_handler is not None:
            decision = self.control_handler("pausar", session_id=session_id,
                                            source=source, generation=generation)
            return PipelineResult(transcript, parsed, decision)
        # The fictional sensor signal must come from the coordinator/simulator,
        # never from spoken text. Other commands retain their default.
        if command.intent.value in {"extender_brazo", "extender_manguera"}:
            command = replace(command, zone_clear=zone_clear)
        decision = self.domain.handle_input(command, source=source,
                                            session_id=session_id,
                                            generation=generation)
        return PipelineResult(transcript, parsed, decision)
