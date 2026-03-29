import math
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPainter, QColor, QBrush, QPen, QFont
from ..utils.stats import _fmt

PAL = [
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
]
CARD_COLORS = ["#4e79a7", "#59a14f", "#f28e2b", "#e15759", "#76b7b2", "#b07aa1"]

def _sec(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color:#aaa;font-size:10px;font-weight:bold;letter-spacing:1px;"
    )
    return lbl

def _divider():
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setStyleSheet("color:#eee;")
    return f

class KPICard(QFrame):
    def __init__(self, label="", value="", color="#4e79a7"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 6, 10, 6)
        v.setSpacing(1)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet("color:#999;font-size:10px;")
        v.addWidget(self._lbl)
        self._val = QLabel(value)
        v.addWidget(self._val)
        self._apply(color)

    def _apply(self, color):
        self.setStyleSheet(f"""
            QFrame {{
                background:white;
                border-left:4px solid {color};
                border-top:1px solid #e8e8e8;
                border-right:1px solid #e8e8e8;
                border-bottom:1px solid #e8e8e8;
                border-radius:6px;
            }}
        """)
        self._val.setStyleSheet(
            f"color:{color};font-size:16px;font-weight:bold;"
        )

    def set(self, label, value, color):
        self._lbl.setText(label)
        self._val.setText(value)
        self._apply(color)

class BarChart(QWidget):
    def __init__(self):
        super().__init__()
        self.data = []
        self.on_click = None
        self._hover = -1
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_data(self, data, on_click=None):
        self.data = data[:15]
        self.on_click = on_click
        self._hover = -1
        self.setMinimumHeight(max(120, len(self.data) * 32 + 28))
        self.update()

    def paintEvent(self, _):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        ML, MR, MT, MB = 110, 56, 12, 8
        n = len(self.data)
        max_v = max(v for _, v in self.data) or 1
        bar_area = W - ML - MR
        row_h = (H - MT - MB) / n
        bh = min(row_h * 0.55, 22)

        for i, (lbl, val) in enumerate(self.data):
            yc = MT + i * row_h + row_h / 2
            bw = max(3, (val / max_v) * bar_area)
            col = QColor(PAL[i % len(PAL)])
            if i == self._hover:
                col = col.lighter(130)

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(col))
            p.drawRoundedRect(int(ML), int(yc - bh / 2), int(bw), int(bh), 3, 3)

            f = QFont(); f.setPointSize(8); p.setFont(f)
            p.setPen(QColor("#555"))
            short = lbl if len(lbl) <= 14 else lbl[:13] + "…"
            p.drawText(0, int(yc - 9), ML - 4, 18,
                       Qt.AlignRight | Qt.AlignVCenter, short)

            p.setPen(QColor("#777"))
            p.drawText(int(ML + bw + 4), int(yc - 9), MR, 18,
                       Qt.AlignLeft | Qt.AlignVCenter, _fmt(val))
        p.end()

    def mouseMoveEvent(self, e):
        idx = self._row(e.y())
        if idx != self._hover:
            self._hover = idx
            self.update()
            self.setCursor(Qt.PointingHandCursor if idx >= 0 else Qt.ArrowCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            idx = self._row(e.y())
            if idx >= 0 and self.on_click:
                self.on_click(self.data[idx][0])

    def leaveEvent(self, _):
        self._hover = -1
        self.update()

    def _row(self, y):
        if not self.data:
            return -1
        n = len(self.data)
        MT, MB = 12, 8
        rh = (self.height() - MT - MB) / n
        idx = int((y - MT) / rh)
        return idx if 0 <= idx < n else -1

class PieChart(QWidget):
    def __init__(self):
        super().__init__()
        self.data = []
        self.on_click = None
        self._hover = -1
        self.setMinimumHeight(220)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def set_data(self, data, on_click=None):
        self.data = data[:10]
        self.on_click = on_click
        self._hover = -1
        self.setMinimumHeight(max(220, len(self.data) * 18 + 160))
        self.update()

    def paintEvent(self, _):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()
        leg_h = len(self.data) * 17 + 8
        pie_h = H - leg_h
        r = min(W, pie_h) * 0.42
        cx, cy = W / 2, pie_h / 2
        total = sum(v for _, v in self.data) or 1

        slices = []
        ang = 0.0
        for i, (_, val) in enumerate(self.data):
            span = (val / total) * 360
            slices.append((ang, span, i))
            ang += span

        for start, span, i in slices:
            col = QColor(PAL[i % len(PAL)])
            offset = 7 if i == self._hover else 0
            rad = math.radians(-(start + span / 2))
            ox, oy = math.cos(rad) * offset, math.sin(rad) * offset
            p.setPen(QPen(QColor("white"), 1.5))
            p.setBrush(QBrush(col))
            p.drawPie(int(cx - r + ox), int(cy - r + oy),
                      int(r * 2), int(r * 2),
                      int(start * 16), int(span * 16))

        f = QFont(); f.setPointSize(8); f.setBold(True); p.setFont(f)
        for start, span, i in slices:
            if span < 8: continue
            mid = math.radians(-(start + span / 2))
            tx = cx + math.cos(mid) * r * 0.65
            ty = cy + math.sin(mid) * r * 0.65
            p.setPen(QColor("white"))
            p.drawText(int(tx - 18), int(ty - 8), 36, 16,
                       Qt.AlignCenter, f"{span/360*100:.0f}%")

        lf = QFont(); lf.setPointSize(8); p.setFont(lf)
        ly = int(pie_h) + 4
        for i, (lbl, val) in enumerate(self.data):
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(PAL[i % len(PAL)])))
            p.drawRoundedRect(8, ly + i * 17 + 3, 10, 10, 2, 2)
            p.setPen(QColor("#555"))
            short = lbl if len(lbl) <= 22 else lbl[:20] + "…"
            p.drawText(22, ly + i * 17, W - 26, 17,
                       Qt.AlignLeft | Qt.AlignVCenter,
                       f"{short}  ({_fmt(val)})")
        p.end()

    def mouseMoveEvent(self, e):
        idx = self._slice_at(e.x(), e.y())
        if idx != self._hover:
            self._hover = idx
            self.update()
            self.setCursor(Qt.PointingHandCursor if idx >= 0 else Qt.ArrowCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            idx = self._slice_at(e.x(), e.y())
            if idx >= 0 and self.on_click:
                self.on_click(self.data[idx][0])

    def leaveEvent(self, _):
        self._hover = -1
        self.update()

    def _slice_at(self, mx, my):
        if not self.data: return -1
        W, H = self.width(), self.height()
        leg_h = len(self.data) * 17 + 8
        pie_h = H - leg_h
        r = min(W, pie_h) * 0.42
        cx, cy = W / 2, pie_h / 2
        dx, dy = mx - cx, my - cy
        if math.hypot(dx, dy) > r: return -1
        angle = math.degrees(math.atan2(-dy, dx)) % 360
        total = sum(v for _, v in self.data) or 1
        cur = 0.0
        for i, (_, val) in enumerate(self.data):
            span = (val / total) * 360
            if cur <= angle < cur + span: return i
            cur += span
        return -1
