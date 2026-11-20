"""Illustrative operation scene for the fictional Faro demo plan."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

class DemoScene(QWidget):
    """Draw a schematic unit and hole positions; no real coordinates are implied."""

    STAGE_LABELS = {
        "sin_seleccion": "Sin selección",
        "seleccionado": "Seleccionado",
        "consultado": "Plan consultado",
        "preparado": "Plan verificado",
        "confirmacion_pendiente": "Confirmación pendiente",
        "movimiento_en_curso": "Extensión en curso",
        "posicionado": "Posicionado",
        "carga_en_curso": "Carga en curso",
        "cargado": "Carga completa",
        "retraccion_en_curso": "Retiro en curso",
        "retraido": "Retraído",
        "cerrado": "Taladro cerrado",
        "fallo": "Fallo simulado",
        "resultado_desconocido": "Resultado desconocido",
    }

    COLORS = {
        "activo": QColor("#2563eb"),
        "completado": QColor("#1e40af"),
        "bloqueado": QColor("#b42318"),
        "pendiente": QColor("#64748b"),
    }

    def __init__(self, *, height: int = 250) -> None:
        super().__init__()
        self.setMinimumHeight(height)
        self._plan: list[Mapping[str, object]] = []
        self._operation: Mapping[str, object] = {}
        self._selected: str | None = None
        self._state = "sin_seleccion"
        self._truck_pixmap = QPixmap(str(Path(__file__).resolve().parent / "assets" / "truck-mining-blue.png"))

    def set_snapshot(self, plan: Sequence[Mapping[str, object]], operation: Mapping[str, object]) -> None:
        self._plan = list(plan)
        self._operation = operation
        self._selected = str(operation.get("hole_id")) if operation.get("hole_id") else None
        self._state = str(operation.get("state", "sin_seleccion"))
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        background = QLinearGradient(0, 0, w, h)
        background.setColorAt(0, QColor("#f7f8fc"))
        background.setColorAt(1, QColor("#f7f8fc"))
        painter.fillRect(self.rect(), background)

        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Inter", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(22, 16, w - 44, 22), "REFERENCIA DE MALLA")

        fields = (
            ("TALADRO ACTIVO", self._selected or "—"),
            ("PRODUCTO", str(self._operation.get("product") or "—")),
            ("OBJETIVO", f"{self._operation['planned_kg']} kg" if self._operation.get("planned_kg") else "—"),
            ("ETAPA", self.STAGE_LABELS.get(self._state, "Estado actualizado").upper()),
        )
        field_width = min((w - 55) / 4, 190)
        for index, (name, value) in enumerate(fields):
            x = 22 + index * (field_width + 7)
            rect = QRectF(x, 47, field_width, 38)
            if index:
                painter.setPen(QPen(QColor("#cbd5e1"), 1))
                painter.drawLine(QPointF(x - 4, 49), QPointF(x - 4, 84))
            painter.setPen(QColor("#64748b"))
            painter.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            painter.drawText(QRectF(x + 9, 49, field_width - 18, 14), name)
            painter.setPen(QColor("#0f172a"))
            painter.setFont(QFont("Inter", 12, QFont.Weight.Bold))
            painter.drawText(QRectF(x + 9, 63, field_width - 18, 19), value)

        floor_y = h * 0.72
        painter.setPen(QPen(QColor("#cbd5e1"), 3))
        painter.drawLine(QPointF(16, floor_y), QPointF(w - 16, floor_y))
        painter.fillRect(QRectF(16, floor_y + 3, w - 32, h - floor_y), QColor("#f7f8fc"))

        # The vehicle is intentionally schematic and stays separate from real equipment controls.
        truck_x = w * 0.06
        truck_width = min(w * 0.27, 260)
        truck_height = truck_width * 0.5
        truck_y = floor_y - truck_height + 12
        if self._truck_pixmap.isNull():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#2563eb"))
            painter.drawRoundedRect(QRectF(truck_x, floor_y - 43, truck_width, 43), 6, 6)
        else:
            painter.drawPixmap(
                QRectF(truck_x, truck_y, truck_width, truck_height),
                self._truck_pixmap,
                QRectF(self._truck_pixmap.rect()),
            )

        count = len(self._plan)
        if count:
            start_x = max(w * 0.45, truck_x + truck_width + 55)
            spacing = (w - start_x - 50) / max(count - 1, 1)
            for index, hole in enumerate(self._plan):
                cx = start_x + index * spacing
                identifier = str(hole.get("id", "—"))
                status = str(hole.get("status", "pendiente"))
                color = self.COLORS.get(status, self.COLORS["pendiente"])
                painter.setPen(QPen(color, 3))
                painter.drawLine(QPointF(cx, floor_y + 8), QPointF(cx, h - 23))
                painter.setBrush(QColor("#f7f8fc"))
                painter.drawEllipse(QPointF(cx, floor_y), 13, 13)
                painter.setPen(QPen(color, 2))
                painter.drawEllipse(QPointF(cx, floor_y), 13, 13)
                painter.setPen(color)
                painter.setFont(QFont("Inter", 18, QFont.Weight.Bold))
                painter.drawText(QRectF(cx - 35, floor_y - 55, 70, 24),
                                 Qt.AlignmentFlag.AlignCenter, identifier)
                painter.setFont(QFont("Inter", 10, QFont.Weight.Bold))
                painter.drawText(QRectF(cx - 60, floor_y - 30, 120, 17),
                                 Qt.AlignmentFlag.AlignCenter, status.upper())

                if identifier == self._selected and self._state in {
                    "movimiento_en_curso", "posicionado", "carga_en_curso", "cargado",
                    "retraccion_en_curso", "retraido",
                }:
                    painter.setPen(QPen(QColor("#2563eb"), 4))
                    painter.drawLine(QPointF(truck_x + truck_width * 0.72, truck_y + 10),
                                     QPointF(cx - 12, floor_y - 3))
        painter.end()
