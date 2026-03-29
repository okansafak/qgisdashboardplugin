import re

with open('dashboard_dock.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Imports -> Add QgsSettings
if 'from qgis.core import QgsProject, QgsVectorLayer, QgsSettings' not in code:
    code = code.replace('from qgis.core import QgsProject, QgsVectorLayer', 'from qgis.core import QgsProject, QgsVectorLayer, QgsSettings')

# 2. Add LANG dictionary
lang_dict = '''
LANG = {
    "en": {
        "sec_layer": "LAYER",
        "lbl_stat_area": "Statistics Field",
        "lbl_group_area": "Grouping Field",
        "chk_only_sel": "Show selected features only",
        "btn_refresh": "↻ Refresh",
        "btn_clear": "✕ Clear Selection",
        "cb_only_count": "(count only)",
        "cb_select_fld": "(select field)",
        
        "sec_kpi_opts": "SUMMARY TOGGLES",
        "sec_kpi_cards": "SUMMARY CARDS",
        "kpi_total_feat": "Total Features",
        "kpi_selected": "Selected",
        "kpi_sum": "Sum",
        "kpi_avg": "Average",
        "kpi_min": "Min",
        "kpi_max": "Max",
        
        "sec_charts": "DISTRIBUTION",
        "tab_bar": "Bar Chart",
        "tab_pie": "Pie Chart",
        "lbl_chart_hint": "Click on bar / slice -> select on map",
        "lbl_empty": "(empty)",
        
        "sec_table": "FEATURE TABLE",
        "ph_search": "Search...",
        "tt_prev": "Previous Page",
        "tt_next": "Next Page",
        "lbl_page": "Page {cur} / {tot}",
        "lbl_qty": "Size:"
    },
    "tr": {
        "sec_layer": "KATMAN",
        "lbl_stat_area": "İstatistik alanı",
        "lbl_group_area": "Gruplama alanı",
        "chk_only_sel": "Yalnızca seçili feature'ları göster",
        "btn_refresh": "↻ Yenile",
        "btn_clear": "✕ Seçimi temizle",
        "cb_only_count": "(yalnızca sayım)",
        "cb_select_fld": "(alan seçin)",
        
        "sec_kpi_opts": "ÖZET KART SEÇİMLERİ",
        "sec_kpi_cards": "ÖZET KARTLARI",
        "kpi_total_feat": "Toplam Feature",
        "kpi_selected": "Seçili",
        "kpi_sum": "Toplam",
        "kpi_avg": "Ortalama",
        "kpi_min": "Min",
        "kpi_max": "Maks",
        
        "sec_charts": "DAĞILIM",
        "tab_bar": "Bar Grafik",
        "tab_pie": "Pasta Grafik",
        "lbl_chart_hint": "Çubuğa / dilime tıkla → haritada seç",
        "lbl_empty": "(boş)",
        
        "sec_table": "ÖZELLİK TABLOSU",
        "ph_search": "Ara…",
        "tt_prev": "Önceki Sayfa",
        "tt_next": "Sonraki Sayfa",
        "lbl_page": "Sayfa {cur} / {tot}",
        "lbl_qty": "Adet:"
    }
}
'''
if 'LANG = {' not in code:
    code = code.replace('\nPAL = [', lang_dict + '\nPAL = [')


# 3. Modify DashboardDock.__init__
init_orig = '''        self._current_page = 0
        self._page_size = 50
        self._filtered_features = []
        self._search_text = ""
        self._kpi_toggles = {}'''

init_new = '''        self._current_page = 0
        self._page_size = 50
        self._filtered_features = []
        self._search_text = ""
        self._kpi_toggles = {}
        
        # Dil Seçimi
        self._lang = QgsSettings().value("LayerDashboard/Locale", "en")'''
if 'self._lang =' not in code:
    code = code.replace(init_orig, init_new)

# Add tr() method
tr_method = '''    def tr(self, key):
        return LANG.get(self._lang, LANG["en"]).get(key, key)'''
if 'def tr(self, key):' not in code:
    code = code.replace('def _build_controls(self):', tr_method + '''

    def _build_controls(self):''')


# 4. We will replace labels in _build_controls
b_ctrl_orig = '''        m.addWidget(_sec("KATMAN"))'''
b_ctrl_new = '''        # Dil Secimi UI
        row_h = QHBoxLayout()
        self._lbl_sec_layer = _sec(self.tr("sec_layer"))
        row_h.addWidget(self._lbl_sec_layer)
        row_h.addStretch()
        self.lang_cb = QComboBox()
        self.lang_cb.addItem("English", "en")
        self.lang_cb.addItem("Türkçe", "tr")
        idx = self.lang_cb.findData(self._lang)
        self.lang_cb.setCurrentIndex(max(0, idx))
        self.lang_cb.currentIndexChanged.connect(self._on_lang_changed)
        row_h.addWidget(self.lang_cb)
        m.addLayout(row_h)'''
if '_lbl_sec_layer =' not in code:
    code = code.replace(b_ctrl_orig, b_ctrl_new)


# Rebuild UI fields with translation
code = code.replace('left.addWidget(QLabel("İstatistik alanı"))', 'self._lbl_stat_area = QLabel(self.tr("lbl_stat_area")); left.addWidget(self._lbl_stat_area)')
code = code.replace('right.addWidget(QLabel("Gruplama alanı"))', 'self._lbl_group_area = QLabel(self.tr("lbl_group_area")); right.addWidget(self._lbl_group_area)')
code = code.replace('self.sel_chk = QCheckBox("Yalnızca seçili feature\'ları göster")', 'self.sel_chk = QCheckBox(self.tr("chk_only_sel"))')
code = code.replace('btn_r = QPushButton("↻  Yenile")', 'self.btn_r = QPushButton(self.tr("btn_refresh"))')
code = code.replace('btn_c = QPushButton("✕  Seçimi temizle")', 'self.btn_c = QPushButton(self.tr("btn_clear"))')
code = code.replace('self.stat_cb.addItem("(yalnızca sayım)", None)', 'self.stat_cb.addItem(self.tr("cb_only_count"), None)')
code = code.replace('self.group_cb.addItem("(alan seçin)", None)', 'self.group_cb.addItem(self.tr("cb_select_fld"), None)')

code = code.replace('self._main.addWidget(_sec("ÖZET KART SEÇİMLERİ"))', 'self._lbl_sec_kpi_opts = _sec(self.tr("sec_kpi_opts")); self._main.addWidget(self._lbl_sec_kpi_opts)')
code = code.replace('self._main.addWidget(_sec("ÖZET KARTLARI"))', 'self._lbl_sec_kpi_cards = _sec(self.tr("sec_kpi_cards")); self._main.addWidget(self._lbl_sec_kpi_cards)')
code = code.replace('kpi_names = ["Toplam Feature", "Seçili", "Toplam", "Ortalama", "Min", "Maks"]', 'kpi_names = ["kpi_total_feat", "kpi_selected", "kpi_sum", "kpi_avg", "kpi_min", "kpi_max"]')
code = code.replace('chk = QCheckBox(name)', 'chk = QCheckBox(self.tr(name))')

code = code.replace('self._main.addWidget(_sec("DAĞILIM"))', 'self._lbl_sec_charts = _sec(self.tr("sec_charts")); self._main.addWidget(self._lbl_sec_charts)')
code = code.replace('tabs.addTab(self._bar, "Bar")', 'self._tabs = tabs; self._tabs.addTab(self._bar, self.tr("tab_bar"))')
code = code.replace('tabs.addTab(self._pie, "Pasta")', 'self._tabs.addTab(self._pie, self.tr("tab_pie"))')
code = code.replace('hint = QLabel("Çubuğa / dilime tıkla → haritada seç")', 'self._lbl_chart_hint = QLabel(self.tr("lbl_chart_hint"))')
code = code.replace('self._main.addWidget(hint)', 'self._main.addWidget(self._lbl_chart_hint)')
code = code.replace('"(boş)"', 'self.tr("lbl_empty")')

code = code.replace('self._main.addWidget(_sec("ÖZELLİK TABLOSU"))', 'self._lbl_sec_table = _sec(self.tr("sec_table")); self._main.addWidget(self._lbl_sec_table)')
code = code.replace('self._search.setPlaceholderText("Ara…")', 'self._search.setPlaceholderText(self.tr("ph_search"))')
code = code.replace('self.btn_prev.setToolTip("Önceki Sayfa")', 'self.btn_prev.setToolTip(self.tr("tt_prev"))')
code = code.replace('self.btn_next.setToolTip("Sonraki Sayfa")', 'self.btn_next.setToolTip(self.tr("tt_next"))')
code = code.replace('self.lbl_page = QLabel("Sayfa 1 / 1")', 'self.lbl_page = QLabel(self.tr("lbl_page").format(cur=1, tot=1))')
code = code.replace('pag_layout.addWidget(QLabel("Adet:"))', 'self._lbl_qty = QLabel(self.tr("lbl_qty")); pag_layout.addWidget(self._lbl_qty)')

code = code.replace('self.lbl_page.setText(f"Sayfa {self._current_page + 1} / {total_pages}")', 'self.lbl_page.setText(self.tr("lbl_page").format(cur=self._current_page+1, tot=total_pages))')

code = code.replace('items.append(("Toplam Feature", str(total), CARD_COLORS[0]))', 'items.append((self.tr("kpi_total_feat"), str(total), CARD_COLORS[0]))')
code = code.replace('if self._kpi_toggles["Toplam Feature"].isChecked():', 'if self._kpi_toggles["kpi_total_feat"].isChecked():')
code = code.replace('if self._kpi_toggles["Seçili"].isChecked():', 'if self._kpi_toggles["kpi_selected"].isChecked():')
code = code.replace('items.append(("Seçili", str(sel), CARD_COLORS[1]))', 'items.append((self.tr("kpi_selected"), str(sel), CARD_COLORS[1]))')
code = code.replace('if self._kpi_toggles["Toplam"].isChecked():', 'if self._kpi_toggles["kpi_sum"].isChecked():')
code = code.replace('items.append(("Toplam", _fmt(sum(vals)), CARD_COLORS[2]))', 'items.append((self.tr("kpi_sum"), _fmt(sum(vals)), CARD_COLORS[2]))')
code = code.replace('if self._kpi_toggles["Ortalama"].isChecked():', 'if self._kpi_toggles["kpi_avg"].isChecked():')
code = code.replace('items.append(("Ortalama", _fmt(sum(vals) / len(vals)), CARD_COLORS[3]))', 'items.append((self.tr("kpi_avg"), _fmt(sum(vals) / len(vals)), CARD_COLORS[3]))')
code = code.replace('if self._kpi_toggles["Min"].isChecked():', 'if self._kpi_toggles["kpi_min"].isChecked():')
code = code.replace('items.append(("Min", _fmt(min(vals)), CARD_COLORS[4]))', 'items.append((self.tr("kpi_min"), _fmt(min(vals)), CARD_COLORS[4]))')
code = code.replace('if self._kpi_toggles["Maks"].isChecked():', 'if self._kpi_toggles["kpi_max"].isChecked():')
code = code.replace('items.append(("Maks", _fmt(max(vals)), CARD_COLORS[5]))', 'items.append((self.tr("kpi_max"), _fmt(max(vals)), CARD_COLORS[5]))')
code = code.replace('btn_row.addWidget(btn_r); btn_row.addWidget(btn_c)', 'btn_row.addWidget(self.btn_r); btn_row.addWidget(self.btn_c)')

# Language dynamic change method
retranslate_method = '''
    def _on_lang_changed(self):
        code = self.lang_cb.currentData()
        if code and code != self._lang:
            self._lang = code
            QgsSettings().setValue("LayerDashboard/Locale", code)
            self._retranslate_ui()

    def _retranslate_ui(self):
        self._lbl_sec_layer.setText(self.tr("sec_layer").upper())
        self._lbl_stat_area.setText(self.tr("lbl_stat_area"))
        self._lbl_group_area.setText(self.tr("lbl_group_area"))
        self.sel_chk.setText(self.tr("chk_only_sel"))
        self.btn_r.setText(self.tr("btn_refresh"))
        self.btn_c.setText(self.tr("btn_clear"))
        
        self._lbl_sec_kpi_opts.setText(self.tr("sec_kpi_opts").upper())
        self._lbl_sec_kpi_cards.setText(self.tr("sec_kpi_cards").upper())
        for key, chk in self._kpi_toggles.items():
            chk.setText(self.tr(key))
            
        self._lbl_sec_charts.setText(self.tr("sec_charts").upper())
        self._tabs.setTabText(0, self.tr("tab_bar"))
        self._tabs.setTabText(1, self.tr("tab_pie"))
        self._lbl_chart_hint.setText(self.tr("lbl_chart_hint"))
        
        self._lbl_sec_table.setText(self.tr("sec_table").upper())
        self._search.setPlaceholderText(self.tr("ph_search"))
        self.btn_prev.setToolTip(self.tr("tt_prev"))
        self.btn_next.setToolTip(self.tr("tt_next"))
        self._lbl_qty.setText(self.tr("lbl_qty"))
        
        if self._layer:
            self._fill_combos(self._layer)
        
        self._refresh()
'''
if 'def _on_lang_changed(self):' not in code:
    code = code.replace('def _clear_sel(self):', retranslate_method + '\n    def _clear_sel(self):')


with open('dashboard_dock_v2.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Translation replacements injected into dashboard_dock_v2.py")
