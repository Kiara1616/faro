"""Illustrative operation scene for the fictional Faro demo plan."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QWidget


class DemoScene(QWidget):
    """Draw a schematic unit and hole positions; no real coordinates are implied."""

    COLORS = {
        "activo": QColor("#31d7d0"),
        "completado": QColor("#79d9a3"),
        "bloqueado": QColor("#f28478"),
        "pendiente": QColor("#92a9b9"),
    }

    def __init__(self, *, height: int = 250) -> None:
        super().__init__()
        self.setMinimumHeight(height)
        self._plan: list[Mapping[str, object]] = []
        self._operation: Mapping[str, object] = {}
        self._selected: str | None = None
        self._state = "sin_seleccion"

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
        background.setColorAt(0, QColor("#081b2a"))
        background.setColorAt(1, QColor("#143b50"))
        painter.fillRect(self.rect(), background)

        painter.setPen(QPen(QColor("#24485a"), 1))
        for x in range(0, self.width(), 36):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 36):
            painter.drawLine(0, y, self.width(), y)

        painter.setPen(QColor("#9bbdca"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(22, 16, w - 44, 22), "VISTA DE OPERACIÓN · ESQUEMA ILUSTRATIVO")
        painter.setPen(QColor("#54d8d2"))
        painter.drawText(QRectF(w - 190, 16, 165, 22), Qt.AlignmentFlag.AlignRight, "DATOS DE DEMO")

        fields = (
            ("TALADRO ACTIVO", self._selected or "—"),
            ("PRODUCTO", str(self._operation.get("product") or "—")),
            ("OBJETIVO", f"{self._operation['planned_kg']} kg" if self._operation.get("planned_kg") else "—"),
            ("EQUIPO", self._state.replace("_", " ").upper()),
        )
        field_width = min((w - 55) / 4, 190)
        for index, (name, value) in enumerate(fields):
            x = 22 + index * (field_width + 7)
            rect = QRectF(x, 47, field_width, 38)
            painter.setPen(QPen(QColor("#31596b"), 1))
            painter.setBrush(QColor("#163648"))
            painter.drawRoundedRect(rect, 5, 5)
            painter.setPen(QColor("#8fbac8"))
            painter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
            painter.drawText(QRectF(x + 9, 49, field_width - 18, 14), name)
            painter.setPen(QColor("#f1fafb"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(QRectF(x + 9, 63, field_width - 18, 19), value)

        floor_y = h * 0.72
        painter.setPen(QPen(QColor("#5d8290"), 3))
        painter.drawLine(QPointF(16, floor_y), QPointF(w - 16, floor_y))
        painter.fillRect(QRectF(16, floor_y + 3, w - 32, h - floor_y), QColor("#102c3b"))

        # The vehicle is intentionally schematic and stays separate from real equipment controls.
        truck_x, truck_y = w * 0.09, floor_y - 55
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#f4af4d"))
        painter.drawRoundedRect(QRectF(truck_x, truck_y + 12, 124, 43), 8, 8)
        painter.setBrush(QColor("#d99131"))
        painter.drawRoundedRect(QRectF(truck_x + 92, truck_y, 48, 55), 7, 7)
        painter.setBrush(QColor("#2c5365"))
        painter.drawRoundedRect(QRectF(truck_x + 102, truck_y + 8, 28, 19), 3, 3)
        painter.setBrush(QColor("#07141e"))
        for offset in (29, 111):
            painter.drawEllipse(QPointF(truck_x + offset, floor_y + 1), 13, 13)
        painter.setPen(QColor("#dbeaf0"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(truck_x, truck_y - 23, 150, 20), "UNIDAD SIMULADA")

        count = len(self._plan)
        if count:
            start_x = max(w * 0.45, truck_x + 180)
            spacing = (w - start_x - 50) / max(count - 1, 1)
            for index, hole in enumerate(self._plan):
                cx = start_x + index * spacing
                identifier = str(hole.get("id", "—"))
                status = str(hole.get("status", "pendiente"))
                color = self.COLORS.get(status, self.COLORS["pendiente"])
                painter.setPen(QPen(color, 3))
                painter.drawLine(QPointF(cx, floor_y + 8), QPointF(cx, h - 23))
                painter.setBrush(QColor("#102c3b"))
                painter.drawEllipse(QPointF(cx, floor_y), 13, 13)
                painter.setPen(QPen(color, 2))
                painter.drawEllipse(QPointF(cx, floor_y), 13, 13)
                painter.setPen(color)
                painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
                painter.drawText(QRectF(cx - 35, floor_y - 55, 70, 24),
                                 Qt.AlignmentFlag.AlignCenter, identifier)
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                painter.drawText(QRectF(cx - 60, floor_y - 30, 120, 17),
                                 Qt.AlignmentFlag.AlignCenter, status.upper())

                if identifier == self._selected and self._state in {
                    "movimiento_en_curso", "posicionado", "carga_en_curso", "cargado",
                    "retraccion_en_curso", "retraido",
                }:
                    painter.setPen(QPen(QColor("#31d7d0"), 4))
                    painter.drawLine(QPointF(truck_x + 126, truck_y + 28),
                                     QPointF(cx - 12, floor_y - 3))
        painter.end()
