"""
dashboard_dock.py  –  Layer Dashboard Plugin
─────────────────────────────────────────────
Özellikler:
  • KPI kartları : sayım, toplam, ortalama, min, maks
  • Bar + Pasta grafik (sekmeli)
  • Harita seçimiyle otomatik filtre / vurgulama
  • Özellik tablosu (arama + sıralama)
  • Çubuğa / dilime tıkla → haritada seç
  • Dış bağımlılık yok (saf PyQt5 + PyQGIS)
"""

from __future__ import annotations
import math
from collections import defaultdict

from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QFrame, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QSizePolicy, QAbstractItemView, QCheckBox, QScrollArea,
)
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QPainter, QColor, QBrush, QPen, QFont

from qgis.core import QgsProject, QgsVectorLayer

try:
    from qgis.core import NULL
except ImportError:
    NULL = None


# ─── Renk paleti ──────────────────────────────────────────────────────────────
PAL = [
    "#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
]
CARD_COLORS = ["#4e79a7", "#59a14f", "#f28e2b", "#e15759", "#76b7b2", "#b07aa1"]


# ──────────────────────────────────────────────────────────────────────────────
# KPI Kart
# ──────────────────────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────────────────────
# Bar Grafik
# ──────────────────────────────────────────────────────────────────────────────
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


# ──────────────────────────────────────────────────────────────────────────────
# Pasta Grafik
# ──────────────────────────────────────────────────────────────────────────────
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

        # Dilimler
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

        # Yüzde etiketleri
        f = QFont(); f.setPointSize(8); f.setBold(True); p.setFont(f)
        for start, span, i in slices:
            if span < 8:
                continue
            mid = math.radians(-(start + span / 2))
            tx = cx + math.cos(mid) * r * 0.65
            ty = cy + math.sin(mid) * r * 0.65
            p.setPen(QColor("white"))
            p.drawText(int(tx - 18), int(ty - 8), 36, 16,
                       Qt.AlignCenter, f"{span/360*100:.0f}%")

        # Lejant
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
        if not self.data:
            return -1
        W, H = self.width(), self.height()
        leg_h = len(self.data) * 17 + 8
        pie_h = H - leg_h
        r = min(W, pie_h) * 0.42
        cx, cy = W / 2, pie_h / 2
        dx, dy = mx - cx, my - cy
        if math.hypot(dx, dy) > r:
            return -1
        angle = math.degrees(math.atan2(-dy, dx)) % 360
        total = sum(v for _, v in self.data) or 1
        cur = 0.0
        for i, (_, val) in enumerate(self.data):
            span = (val / total) * 360
            if cur <= angle < cur + span:
                return i
            cur += span
        return -1


# ──────────────────────────────────────────────────────────────────────────────
# Ana Dock Widget
# ──────────────────────────────────────────────────────────────────────────────
class DashboardDock(QDockWidget):
    def __init__(self, iface):
        super().__init__("Layer Dashboard")
        self.iface = iface
        self.setMinimumWidth(300)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self._layer = None
        self._all_features = []
        self._updating_selection = False
        
        # Sayfama ve Seçim Durumları
        self._current_page = 0
        self._page_size = 50
        self._filtered_features = []
        self._search_text = ""
        self._kpi_toggles = {}

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        root = QWidget()
        scroll_area.setWidget(root)
        self.setWidget(scroll_area)

        self._main = QVBoxLayout(root)
        self._main.setContentsMargins(8, 8, 8, 8)
        self._main.setSpacing(6)

        self._build_controls()
        self._build_kpi()
        self._build_charts()
        self._build_table()

        QgsProject.instance().layersAdded.connect(self._reload_layers)
        QgsProject.instance().layersRemoved.connect(self._reload_layers)

    # ── Kontroller ────────────────────────────────────────────────────────────
    def _build_controls(self):
        m = self._main
        m.addWidget(_sec("KATMAN"))
        self.layer_cb = QComboBox()
        self.layer_cb.currentIndexChanged.connect(self._on_layer_changed)
        m.addWidget(self.layer_cb)

        row = QHBoxLayout(); row.setSpacing(6)
        left = QVBoxLayout()
        left.addWidget(QLabel("İstatistik alanı"))
        self.stat_cb = QComboBox()
        self.stat_cb.currentIndexChanged.connect(self._refresh)
        left.addWidget(self.stat_cb)

        right = QVBoxLayout()
        right.addWidget(QLabel("Gruplama alanı"))
        self.group_cb = QComboBox()
        self.group_cb.currentIndexChanged.connect(self._refresh)
        right.addWidget(self.group_cb)

        row.addLayout(left); row.addLayout(right)
        m.addLayout(row)

        self.sel_chk = QCheckBox("Yalnızca seçili feature'ları göster")
        self.sel_chk.stateChanged.connect(self._refresh)
        m.addWidget(self.sel_chk)

        btn_row = QHBoxLayout(); btn_row.setSpacing(4)
        btn_r = QPushButton("↻  Yenile")
        btn_r.clicked.connect(self._refresh)
        btn_c = QPushButton("✕  Seçimi temizle")
        btn_c.clicked.connect(self._clear_sel)
        btn_row.addWidget(btn_r); btn_row.addWidget(btn_c)
        m.addLayout(btn_row)
        m.addWidget(_divider())

    # ── KPI ───────────────────────────────────────────────────────────────────
    def _build_kpi(self):
        self._main.addWidget(_sec("ÖZET KART SEÇİMLERİ"))
        toggles_layout = QGridLayout()
        toggles_layout.setSpacing(4)
        kpi_names = ["Toplam Feature", "Seçili", "Toplam", "Ortalama", "Min", "Maks"]
        for i, name in enumerate(kpi_names):
            chk = QCheckBox(name)
            chk.setChecked(True)
            chk.stateChanged.connect(self._refresh_kpi_only)
            self._kpi_toggles[name] = chk
            toggles_layout.addWidget(chk, i // 3, i % 3)
        w_tog = QWidget(); w_tog.setLayout(toggles_layout)
        self._main.addWidget(w_tog)
        
        self._main.addWidget(_sec("ÖZET KARTLARI"))
        self._kpi_grid = QGridLayout()
        self._kpi_grid.setSpacing(6)
        w = QWidget(); w.setLayout(self._kpi_grid)
        self._main.addWidget(w)
        self._cards = []
        self._main.addWidget(_divider())

    def _refresh_kpi_only(self):
        if not self._layer: return
        stat_f = self.stat_cb.currentData()
        self._set_kpis(self._calc_kpis(self._all_features, stat_f, self._layer))

    def _set_kpis(self, items):
        # Kart sayısını ayarla
        while len(self._cards) < len(items):
            c = KPICard()
            self._cards.append(c)
        for c in self._cards:
            self._kpi_grid.removeWidget(c)
            c.hide()
        for i, (lbl, val, col) in enumerate(items):
            c = self._cards[i]
            c.set(lbl, val, col)
            r, ci = divmod(i, 2)
            self._kpi_grid.addWidget(c, r, ci)
            c.show()

    # ── Grafikler ─────────────────────────────────────────────────────────────
    def _build_charts(self):
        self._main.addWidget(_sec("DAĞILIM"))
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab{font-size:11px;padding:3px 10px;}")
        self._bar = BarChart()
        self._pie = PieChart()
        tabs.addTab(self._bar, "Bar")
        tabs.addTab(self._pie, "Pasta")
        self._main.addWidget(tabs)

        hint = QLabel("Çubuğa / dilime tıkla → haritada seç")
        hint.setStyleSheet("color:#bbb;font-size:10px;")
        self._main.addWidget(hint)
        self._main.addWidget(_divider())

    # ── Tablo ─────────────────────────────────────────────────────────────────
    def _build_table(self):
        self._main.addWidget(_sec("ÖZELLİK TABLOSU"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Ara…")
        self._search.textChanged.connect(self._on_search_changed)
        self._main.addWidget(self._search)

        self._table = QTableWidget()
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setMinimumHeight(180)
        self._table.setSortingEnabled(True)
        self._table.itemSelectionChanged.connect(self._on_table_sel)
        self._main.addWidget(self._table)

        pag_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◄")
        self.btn_prev.setToolTip("Önceki Sayfa")
        self.btn_prev.clicked.connect(self._prev_page)
        self.lbl_page = QLabel("Sayfa 1 / 1")
        self.lbl_page.setAlignment(Qt.AlignCenter)
        self.btn_next = QPushButton("►")
        self.btn_next.setToolTip("Sonraki Sayfa")
        self.btn_next.clicked.connect(self._next_page)
        
        self.cb_page_size = QComboBox()
        self.cb_page_size.addItems(["50", "100", "500", "1000"])
        self.cb_page_size.currentTextChanged.connect(self._on_page_size_changed)

        pag_layout.addWidget(self.btn_prev)
        pag_layout.addWidget(self.lbl_page, 1)
        pag_layout.addWidget(self.btn_next)
        pag_layout.addWidget(QLabel("Adet:"))
        pag_layout.addWidget(self.cb_page_size)

        self._main.addLayout(pag_layout)

    # ── Katman yönetimi ───────────────────────────────────────────────────────
    def populate_layers(self):
        self.layer_cb.blockSignals(True)
        self.layer_cb.clear()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                self.layer_cb.addItem(layer.name(), layer.id())
        self.layer_cb.blockSignals(False)
        self._on_layer_changed()

    def _reload_layers(self, *_):
        self.populate_layers()

    def _on_layer_changed(self):
        lid = self.layer_cb.currentData()
        if not lid:
            self._layer = None
            self._clear_ui()
            return
        layer = QgsProject.instance().mapLayer(lid)
        if not isinstance(layer, QgsVectorLayer):
            return
        if self._layer:
            try:
                self._layer.selectionChanged.disconnect(self._on_map_sel)
            except Exception:
                pass
        self._layer = layer
        layer.selectionChanged.connect(self._on_map_sel)
        self._fill_combos(layer)
        self._refresh()

    def _clear_ui(self):
        self.stat_cb.blockSignals(True)
        self.stat_cb.clear()
        self.stat_cb.blockSignals(False)
        
        self.group_cb.blockSignals(True)
        self.group_cb.clear()
        self.group_cb.blockSignals(False)
        
        self._set_kpis([])
        self._bar.set_data([])
        self._pie.set_data([])
        
        self._table.blockSignals(True)
        self._table.clear()
        self._table.setRowCount(0)
        self._table.setColumnCount(0)
        self._table.blockSignals(False)

    def _fill_combos(self, layer):
        num_fields, all_fields = [], []
        for f in layer.fields():
            all_fields.append(f.name())
            if f.isNumeric():
                num_fields.append(f.name())

        self.stat_cb.blockSignals(True)
        self.stat_cb.clear()
        self.stat_cb.addItem("(yalnızca sayım)", None)
        for f in num_fields:
            self.stat_cb.addItem(f, f)
        self.stat_cb.blockSignals(False)

        self.group_cb.blockSignals(True)
        self.group_cb.clear()
        self.group_cb.addItem("(alan seçin)", None)
        for f in all_fields:
            self.group_cb.addItem(f, f)
        self.group_cb.blockSignals(False)

    # ── Yenileme ──────────────────────────────────────────────────────────────
    def _refresh(self):
        layer = self._layer
        if not layer:
            return

        only_sel = self.sel_chk.isChecked()
        features = list(layer.selectedFeatures() if only_sel
                        else layer.getFeatures())
        self._all_features = features

        stat_f = self.stat_cb.currentData()
        group_f = self.group_cb.currentData()

        # KPI
        self._set_kpis(self._calc_kpis(self._all_features, stat_f, layer))

        # Grafik
        chart_data = self._calc_groups(self._all_features, stat_f, group_f)
        click_fn = lambda lbl: self._select_by_group(lbl, group_f)
        self._bar.set_data(chart_data, on_click=click_fn)
        self._pie.set_data(chart_data, on_click=click_fn)

        # Tablo Arama ve Sayfalandırma
        self._search_text = self._search.text().lower()
        if self._search_text:
            self._apply_search()
        else:
            self._filtered_features = self._all_features
            self._current_page = 0
            self._render_table_page()

    def _calc_kpis(self, features, stat_f, layer):
        items = []
        total = len(features)
        sel = len(layer.selectedFeatureIds())
        if self._kpi_toggles["Toplam Feature"].isChecked():
            items.append(("Toplam Feature", str(total), CARD_COLORS[0]))
        if self._kpi_toggles["Seçili"].isChecked():
            items.append(("Seçili", str(sel), CARD_COLORS[1]))
            
        if stat_f:
            vals = _nums(features, stat_f)
            if vals:
                if self._kpi_toggles["Toplam"].isChecked():
                    items.append(("Toplam", _fmt(sum(vals)), CARD_COLORS[2]))
                if self._kpi_toggles["Ortalama"].isChecked():
                    items.append(("Ortalama", _fmt(sum(vals) / len(vals)), CARD_COLORS[3]))
                if self._kpi_toggles["Min"].isChecked():
                    items.append(("Min", _fmt(min(vals)), CARD_COLORS[4]))
                if self._kpi_toggles["Maks"].isChecked():
                    items.append(("Maks", _fmt(max(vals)), CARD_COLORS[5]))
        return items

    def _calc_groups(self, features, stat_f, group_f):
        if not group_f:
            return []
        groups = defaultdict(float)
        for f in features:
            key = str(f[group_f]) if _ok(f[group_f]) else "(boş)"
            if stat_f:
                v = f[stat_f]
                groups[key] += float(v) if _ok(v) else 0.0
            else:
                groups[key] += 1
        return sorted(groups.items(), key=lambda x: x[1], reverse=True)

    # ── Tablo ─────────────────────────────────────────────────────────────────
    def _on_search_changed(self, text):
        self._search_text = text.lower()
        self._apply_search()

    def _apply_search(self):
        if not self._layer: return
        fields = [f.name() for f in self._layer.fields()]
        if not self._search_text:
            self._filtered_features = self._all_features
        else:
            filtered = []
            for f in self._all_features:
                match = False
                for fname in fields:
                    v = f[fname]
                    if _ok(v) and self._search_text in str(v).lower():
                        match = True
                        break
                if match:
                    filtered.append(f)
            self._filtered_features = filtered
        
        self._current_page = 0
        self._render_table_page()

    def _render_table_page(self):
        if not self._layer: return
        self._table.blockSignals(True)
        fields = [f.name() for f in self._layer.fields()]
        sel_ids = set(self._layer.selectedFeatureIds())

        total_feats = len(self._filtered_features)
        total_pages = max(1, math.ceil(total_feats / self._page_size))
        
        if self._current_page >= total_pages:
            self._current_page = max(0, total_pages - 1)
            
        start_idx = self._current_page * self._page_size
        end_idx = min(start_idx + self._page_size, total_feats)
        page_features = self._filtered_features[start_idx:end_idx]

        self.lbl_page.setText(f"Sayfa {self._current_page + 1} / {total_pages}")
        self.btn_prev.setEnabled(self._current_page > 0)
        self.btn_next.setEnabled(self._current_page < total_pages - 1)

        self._table.setSortingEnabled(False)
        self._table.clear()
        self._table.setColumnCount(len(fields))
        self._table.setHorizontalHeaderLabels(fields)
        self._table.setRowCount(len(page_features))

        for row, feat in enumerate(page_features):
            for col, fname in enumerate(fields):
                val = feat[fname]
                item = QTableWidgetItem(str(val) if _ok(val) else "")
                item.setData(Qt.UserRole, feat.id())
                if feat.id() in sel_ids:
                    item.setBackground(QBrush(QColor("#ddeeff")))
                self._table.setItem(row, col, item)

        self._table.setSortingEnabled(True)
        self._table.resizeColumnsToContents()
        self._table.blockSignals(False)

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_table_page()

    def _next_page(self):
        self._current_page += 1
        self._render_table_page()

    def _on_page_size_changed(self, text):
        try:
            self._page_size = int(text)
            self._current_page = 0
            self._render_table_page()
        except:
            pass

    def _on_table_sel(self):
        if self._updating_selection:
            return
        layer = self._layer
        if not layer:
            return
        ids = set()
        for item in self._table.selectedItems():
            fid = item.data(Qt.UserRole)
            if fid is not None:
                ids.add(fid)
        self._updating_selection = True
        layer.selectByIds(list(ids))
        self._updating_selection = False

    # ── Harita seçimi ─────────────────────────────────────────────────────────
    def _on_map_sel(self):
        if self._updating_selection:
            return

        if self.sel_chk.isChecked():
            self._updating_selection = True
            try:
                self._refresh()
            finally:
                self._updating_selection = False
            return
        
        layer = self._layer
        if not layer:
            return
        
        self._updating_selection = True
        try:
            sel_ids = set(layer.selectedFeatureIds())
            for row in range(self._table.rowCount()):
                item = self._table.item(row, 0)
                fid = item.data(Qt.UserRole) if item else None
                bg = QBrush(QColor("#ddeeff")) if fid in sel_ids else QBrush(QColor("white"))
                for col in range(self._table.columnCount()):
                    c = self._table.item(row, col)
                    if c:
                        c.setBackground(bg)
            # KPI seçili sayısını güncelle
            stat_f = self.stat_cb.currentData()
            self._set_kpis(self._calc_kpis(self._all_features, stat_f, layer))
        finally:
            self._updating_selection = False

    def _select_by_group(self, group_value, group_f):
        layer = self._layer
        if not layer or not group_f:
            return
        ids = []
        for f in self._all_features:
            v = f[group_f]
            s = str(v) if _ok(v) else "(boş)"
            if s == group_value:
                ids.append(f.id())
        self._updating_selection = True
        layer.selectByIds(ids)
        self._updating_selection = False
        if hasattr(self.iface.mapCanvas(), 'panToSelected'):
            self.iface.mapCanvas().panToSelected(layer)

    def _clear_sel(self):
        if self._layer:
            self._layer.removeSelection()


# ─── Yardımcılar ──────────────────────────────────────────────────────────────
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


def _ok(val):
    return val is not None and val != NULL


def _nums(features, field):
    vals = []
    for f in features:
        v = f[field]
        if _ok(v):
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                pass
    return vals


def _fmt(value):
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:.2f}"
