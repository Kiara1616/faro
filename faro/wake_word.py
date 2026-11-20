"""Gate voice commands behind the mandatory local wake phrase."""

from __future__ import annotations

from dataclasses import dataclass
import re
import time


@dataclass(frozen=True)
class WakeResult:
    status: str  # ignored, activated, command
    command: str | None = None


class WakeCommandGate:
    """Accept one command only after a leading ``Oye Faro`` wake phrase."""

    _WAKE_PREFIX = re.compile(r"^\s*oye[\s,.:;!?¡¿-]+faro\b", re.IGNORECASE)
    _WAKE_SEPARATOR = re.compile(r"^[\s,.:;!?¡¿-]+")

    def __init__(self, *, command_window_seconds: float = 6.0) -> None:
        if command_window_seconds <= 0:
            raise ValueError("command_window_seconds must be positive")
        self.command_window_seconds = float(command_window_seconds)
        self._armed_until: float | None = None

    def reset(self) -> None:
        self._armed_until = None

    def expire(self, *, now: float | None = None) -> bool:
        """Close an armed command window when its deadline has passed."""
        now = time.monotonic() if now is None else now
        if self._armed_until is not None and now >= self._armed_until:
            self.reset()
            return True
        return False

    def consume(self, transcript: str, *, now: float | None = None) -> WakeResult:
        """Ignore ambient speech; pass through one command after the wake phrase.

        ``Oye Faro, <command>`` is accepted in one utterance. Saying only
        ``Oye Faro`` opens a short window for the next utterance.
        """
        if not isinstance(transcript, str):
            raise TypeError("transcript must be str")
        now = time.monotonic() if now is None else now
        if self._armed_until is not None:
            if not self.expire(now=now):
                armed_match = self._WAKE_PREFIX.match(transcript)
                if armed_match is not None:
                    remainder = self._command_after_wake(transcript, armed_match)
                    if not remainder:
                        self._armed_until = now + self.command_window_seconds
                        return WakeResult("activated")
                    self.reset()
                    return WakeResult("command", remainder)
                self.reset()
                command = transcript.strip()
                return WakeResult("command", command) if command else WakeResult("ignored")

        match = self._WAKE_PREFIX.match(transcript)
        if match is None:
            return WakeResult("ignored")

        remainder = self._command_after_wake(transcript, match)
        if not remainder:
            self._armed_until = now + self.command_window_seconds
            return WakeResult("activated")
        return WakeResult("command", remainder)

    @classmethod
    def _command_after_wake(cls, transcript: str, match: re.Match[str]) -> str:
        remainder = transcript[match.end():]
        return cls._WAKE_SEPARATOR.sub("", remainder, count=1).strip()
