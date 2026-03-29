"""
dashboard_dock.py  –  Layer Dashboard Plugin (Modular Architecture)
"""

from __future__ import annotations
import math
from collections import defaultdict

from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QFrame, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QAbstractItemView, QCheckBox, QScrollArea,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QBrush
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis

from .utils.stats import _nums, _fmt, _ok
from .utils.i18n import Translator
from .ui.components import KPICard, BarChart, PieChart, CARD_COLORS, _sec, _divider

class DashboardDock(QDockWidget):
    def __init__(self, iface):
        super().__init__("Layer Dashboard")
        self.iface = iface
        self.setMinimumWidth(300)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self._translator = Translator()

        self._layer = None
        self._all_features = []
        self._updating_selection = False
        
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

        try:
            self._build_controls()
            self._build_kpi()
            self._build_charts()
            self._build_table()
        except Exception as e:
            QgsMessageLog.logMessage(f"Dashboard init error: {str(e)}", "Layer Dashboard", Qgis.Critical)

        QgsProject.instance().layersAdded.connect(self._reload_layers)
        QgsProject.instance().layersRemoved.connect(self._reload_layers)

    def tr(self, key):
        return self._translator.tr(key)

    # ── Kontroller ────────────────────────────────────────────────────────────
    def _build_controls(self):
        m = self._main
        
        top_row = QHBoxLayout()
        top_row.addWidget(_sec(self.tr("sec_layer")))
        top_row.addStretch()
        self.lang_cb = QComboBox()
        self.lang_cb.addItem("English", "en")
        self.lang_cb.addItem("Türkçe", "tr")
        idx = self.lang_cb.findData(self._translator.current())
        self.lang_cb.setCurrentIndex(idx if idx >= 0 else 0)
        self.lang_cb.currentIndexChanged.connect(self._on_lang_changed)
        top_row.addWidget(self.lang_cb)
        m.addLayout(top_row)
        
        self.layer_cb = QComboBox()
        self.layer_cb.currentIndexChanged.connect(self._on_layer_changed)
        m.addWidget(self.layer_cb)

        row = QHBoxLayout(); row.setSpacing(6)
        left = QVBoxLayout()
        left.addWidget(QLabel(self.tr("lbl_stat_area")))
        self.stat_cb = QComboBox()
        self.stat_cb.currentIndexChanged.connect(self._refresh)
        left.addWidget(self.stat_cb)

        right = QVBoxLayout()
        right.addWidget(QLabel(self.tr("lbl_group_area")))
        self.group_cb = QComboBox()
        self.group_cb.currentIndexChanged.connect(self._refresh)
        right.addWidget(self.group_cb)

        row.addLayout(left); row.addLayout(right)
        m.addLayout(row)

        self.sel_chk = QCheckBox(self.tr("chk_only_sel"))
        self.sel_chk.stateChanged.connect(self._refresh)
        m.addWidget(self.sel_chk)

        btn_row = QHBoxLayout(); btn_row.setSpacing(4)
        btn_r = QPushButton(self.tr("btn_refresh"))
        btn_r.clicked.connect(self._refresh)
        btn_c = QPushButton(self.tr("btn_clear"))
        btn_c.clicked.connect(self._clear_sel)
        btn_row.addWidget(btn_r); btn_row.addWidget(btn_c)
        m.addLayout(btn_row)
        m.addWidget(_divider())

    # ── KPI ───────────────────────────────────────────────────────────────────
    def _build_kpi(self):
        self._main.addWidget(_sec(self.tr("sec_kpi_opts")))
        toggles_layout = QGridLayout()
        toggles_layout.setSpacing(4)
        kpi_names = ["kpi_total_feat", "kpi_selected", "kpi_sum", "kpi_avg", "kpi_min", "kpi_max"]
        for i, name in enumerate(kpi_names):
            chk = QCheckBox(self.tr(name))
            chk.setChecked(True)
            chk.stateChanged.connect(self._refresh_kpi_only)
            self._kpi_toggles[name] = chk
            toggles_layout.addWidget(chk, i // 3, i % 3)
        w_tog = QWidget(); w_tog.setLayout(toggles_layout)
        self._main.addWidget(w_tog)
        
        self._main.addWidget(_sec(self.tr("sec_kpi_cards")))
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
        self._main.addWidget(_sec(self.tr("sec_charts")))
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab{font-size:11px;padding:3px 10px;}")
        self._bar = BarChart()
        self._pie = PieChart()
        tabs.addTab(self._bar, self.tr("tab_bar"))
        tabs.addTab(self._pie, self.tr("tab_pie"))
        self._main.addWidget(tabs)

        hint = QLabel(self.tr("lbl_chart_hint"))
        hint.setStyleSheet("color:#bbb;font-size:10px;")
        self._main.addWidget(hint)
        self._main.addWidget(_divider())

    # ── Tablo ─────────────────────────────────────────────────────────────────
    def _build_table(self):
        self._main.addWidget(_sec(self.tr("sec_table")))
        self._search = QLineEdit()
        self._search.setPlaceholderText(self.tr("ph_search"))
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
        self.btn_prev.setToolTip(self.tr("tt_prev"))
        self.btn_prev.clicked.connect(self._prev_page)
        self.lbl_page = QLabel(self.tr("lbl_page").format(cur=1, tot=1))
        self.lbl_page.setAlignment(Qt.AlignCenter)
        self.btn_next = QPushButton("►")
        self.btn_next.setToolTip(self.tr("tt_next"))
        self.btn_next.clicked.connect(self._next_page)
        
        self.cb_page_size = QComboBox()
        self.cb_page_size.addItems(["50", "100", "500", "1000"])
        self.cb_page_size.currentTextChanged.connect(self._on_page_size_changed)

        pag_layout.addWidget(self.btn_prev)
        pag_layout.addWidget(self.lbl_page, 1)
        pag_layout.addWidget(self.btn_next)
        pag_layout.addWidget(QLabel(self.tr("lbl_qty")))
        pag_layout.addWidget(self.cb_page_size)

        self._main.addLayout(pag_layout)

    def _on_lang_changed(self):
        code = self.lang_cb.currentData()
        if code and code != self._translator.current():
            self._translator.set_lang(code)
            
            if self._layer:
                try: self._layer.selectionChanged.disconnect(self._on_map_sel)
                except: pass
            
            self._clear_layout(self._main)
            self._layer = None
            self._current_page = 0
            
            self._build_controls()
            self._build_kpi()
            self._build_charts()
            self._build_table()
            
            self.populate_layers()
            
    def _clear_layout(self, layout):
        if layout is None: return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
                item.layout().deleteLater()

    # ── Katman yönetimi ───────────────────────────────────────────────────────
    def populate_layers(self):
        if not hasattr(self, 'layer_cb'): return
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
        if not hasattr(self, 'layer_cb'): return
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
        if hasattr(self, 'stat_cb'):
            self.stat_cb.blockSignals(True)
            self.stat_cb.clear()
            self.stat_cb.blockSignals(False)
        
        if hasattr(self, 'group_cb'):
            self.group_cb.blockSignals(True)
            self.group_cb.clear()
            self.group_cb.blockSignals(False)
        
        if hasattr(self, '_bar'):
            self._set_kpis([])
            self._bar.set_data([])
            self._pie.set_data([])
        
        if hasattr(self, '_table'):
            self._table.blockSignals(True)
            self._table.clear()
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            self._table.blockSignals(False)

    def _fill_combos(self, layer):
        if not hasattr(self, 'stat_cb'): return
        num_fields, all_fields = [], []
        for f in layer.fields():
            all_fields.append(f.name())
            if f.isNumeric():
                num_fields.append(f.name())

        self.stat_cb.blockSignals(True)
        self.stat_cb.clear()
        self.stat_cb.addItem(self.tr("cb_only_count"), None)
        for f in num_fields:
            self.stat_cb.addItem(f, f)
        self.stat_cb.blockSignals(False)

        self.group_cb.blockSignals(True)
        self.group_cb.clear()
        self.group_cb.addItem(self.tr("cb_select_fld"), None)
        for f in all_fields:
            self.group_cb.addItem(f, f)
        self.group_cb.blockSignals(False)

    # ── Yenileme ──────────────────────────────────────────────────────────────
    def _refresh(self):
        layer = self._layer
        if not layer or not hasattr(self, 'sel_chk'): return

        only_sel = self.sel_chk.isChecked()
        features = list(layer.selectedFeatures() if only_sel
                        else layer.getFeatures())
        self._all_features = features

        stat_f = self.stat_cb.currentData()
        group_f = self.group_cb.currentData()

        self._set_kpis(self._calc_kpis(self._all_features, stat_f, layer))

        chart_data = self._calc_groups(self._all_features, stat_f, group_f)
        click_fn = lambda lbl: self._select_by_group(lbl, group_f)
        self._bar.set_data(chart_data, on_click=click_fn)
        self._pie.set_data(chart_data, on_click=click_fn)

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
        if self._kpi_toggles["kpi_total_feat"].isChecked():
            items.append((self.tr("kpi_total_feat"), str(total), CARD_COLORS[0]))
        if self._kpi_toggles["kpi_selected"].isChecked():
            items.append((self.tr("kpi_selected"), str(sel), CARD_COLORS[1]))
            
        if stat_f:
            vals = _nums(features, stat_f)
            if vals:
                if self._kpi_toggles["kpi_sum"].isChecked():
                    items.append((self.tr("kpi_sum"), _fmt(sum(vals)), CARD_COLORS[2]))
                if self._kpi_toggles["kpi_avg"].isChecked():
                    items.append((self.tr("kpi_avg"), _fmt(sum(vals) / len(vals)), CARD_COLORS[3]))
                if self._kpi_toggles["kpi_min"].isChecked():
                    items.append((self.tr("kpi_min"), _fmt(min(vals)), CARD_COLORS[4]))
                if self._kpi_toggles["kpi_max"].isChecked():
                    items.append((self.tr("kpi_max"), _fmt(max(vals)), CARD_COLORS[5]))
        return items

    def _calc_groups(self, features, stat_f, group_f):
        if not group_f: return []
        groups = defaultdict(float)
        for f in features:
            key = str(f[group_f]) if _ok(f[group_f]) else self.tr("lbl_empty")
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
        if not self._layer or not hasattr(self, '_table'): return
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

        self.lbl_page.setText(self.tr("lbl_page").format(cur=self._current_page + 1, tot=total_pages))
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
        except: pass

    def _on_table_sel(self):
        if self._updating_selection: return
        layer = self._layer
        if not layer: return
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
        if self._updating_selection: return

        if self.sel_chk.isChecked():
            self._updating_selection = True
            try: self._refresh()
            finally: self._updating_selection = False
            return
        
        layer = self._layer
        if not layer or not hasattr(self, '_table'): return
        
        self._updating_selection = True
        try:
            sel_ids = set(layer.selectedFeatureIds())
            for row in range(self._table.rowCount()):
                item = self._table.item(row, 0)
                fid = item.data(Qt.UserRole) if item else None
                bg = QBrush(QColor("#ddeeff")) if fid in sel_ids else QBrush(QColor("white"))
                for col in range(self._table.columnCount()):
                    c = self._table.item(row, col)
                    if c: c.setBackground(bg)
            
            stat_f = self.stat_cb.currentData()
            self._set_kpis(self._calc_kpis(self._all_features, stat_f, layer))
        finally:
            self._updating_selection = False

    def _select_by_group(self, group_value, group_f):
        layer = self._layer
        if not layer or not group_f: return
        ids = []
        for f in self._all_features:
            v = f[group_f]
            s = str(v) if _ok(v) else self.tr("lbl_empty")
            if s == group_value:
                ids.append(f.id())
        self._updating_selection = True
        layer.selectByIds(ids)
        self._updating_selection = False
        if hasattr(self.iface.mapCanvas(), 'zoomToSelected'):
            self.iface.mapCanvas().zoomToSelected(layer)
        elif hasattr(self.iface.mapCanvas(), 'panToSelected'):
            self.iface.mapCanvas().panToSelected(layer)

    def _clear_sel(self):
        if self._layer:
            self._layer.removeSelection()
