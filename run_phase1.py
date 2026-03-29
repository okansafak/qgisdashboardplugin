import re

with open('dashboard_dock.py', 'r', encoding='utf-8') as f:
    c = f.read()

# __init__ modifications
c = c.replace(
'''        self._layer = None
        self._all_features = []
        self._updating_selection = False''',
'''        self._layer = None
        self._all_features = []
        self._updating_selection = False
        
        self._current_page = 0
        self._page_size = 50
        self._filtered_features = []
        self._search_text = ""
        self._kpi_toggles = {}'''
)

# _build_kpi
b_kpi = '''    def _build_kpi(self):
        self._main.addWidget(_sec("ÖZET"))
        self._kpi_grid = QGridLayout()
        self._kpi_grid.setSpacing(6)
        w = QWidget(); w.setLayout(self._kpi_grid)
        self._main.addWidget(w)
        self._cards = []
        self._main.addWidget(_divider())'''
        
n_kpi = '''    def _build_kpi(self):
        self._main.addWidget(_sec("ÖZET SEÇENEKLERİ"))
        toggles_layout = QGridLayout()
        toggles_layout.setSpacing(4)
        kpi_names = ["Toplam", "Seçili", "Sum", "Ortalama", "Min", "Maks"]
        for i, name in enumerate(kpi_names):
            chk = QCheckBox(name)
            chk.setChecked(True)
            chk.stateChanged.connect(self._refresh_kpi_only)
            self._kpi_toggles[name] = chk
            toggles_layout.addWidget(chk, i // 3, i % 3)
        w_tog = QWidget(); w_tog.setLayout(toggles_layout)
        self._main.addWidget(w_tog)
        
        self._main.addWidget(_sec("ÖZET"))
        self._kpi_grid = QGridLayout()
        self._kpi_grid.setSpacing(6)
        w = QWidget(); w.setLayout(self._kpi_grid)
        self._main.addWidget(w)
        self._cards = []
        self._main.addWidget(_divider())'''
c = c.replace(b_kpi, n_kpi)

# Add _refresh_kpi_only
kpi_funcs_start = '''    def _set_kpis(self, items):'''
n_kpi_funcs_start = '''    def _refresh_kpi_only(self):
        if not self._layer: return
        stat_f = self.stat_cb.currentData()
        self._set_kpis(self._calc_kpis(self._all_features, stat_f, self._layer))

    def _set_kpis(self, items):'''
c = c.replace(kpi_funcs_start, n_kpi_funcs_start)

# _build_table
b_table = '''    def _build_table(self):
        self._main.addWidget(_sec("ÖZELLİK TABLOSU"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Ara…")
        self._search.textChanged.connect(self._filter_table)
        self._main.addWidget(self._search)

        self._table = QTableWidget()
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setMinimumHeight(180)
        self._table.setSortingEnabled(True)
        self._table.itemSelectionChanged.connect(self._on_table_sel)
        self._main.addWidget(self._table)'''

n_table = '''    def _build_table(self):
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
        self._main.addLayout(pag_layout)'''
c = c.replace(b_table, n_table)

with open('dashboard_dock.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("Phase 1 done")
