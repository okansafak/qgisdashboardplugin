# 📊 Layer Dashboard — QGIS Plugin

**Layer Dashboard** is a powerful, interactive analytics dock panel for QGIS that transforms any vector layer into a live dashboard with KPI summary cards, bar/pie charts, a paginated feature table, and map-linked selection — all without leaving QGIS.

| Feature | Description |
|---|---|
| **KPI Summary Cards** | Total features, selected count, sum, average, min, max — toggleable on/off |
| **Bar & Pie Charts** | Grouped distribution charts with click-to-select-on-map interaction |
| **Paginated Table** | High-performance feature table with search and configurable page sizes |
| **Multi-Language** | English / Türkçe UI with persistent language preference |
| **Zoom to Selection** | Click a chart slice or bar → features are selected and zoomed to on the map |

---

## 🖥️ Screenshots

> After installing the plugin, open it from **Vector → Layer Dashboard** or click the dashboard icon in the toolbar.

---

## 📦 Installation

### Option A — Install from ZIP

1. Download the latest release `.zip` from [Releases](https://github.com/okansafak/qgisdashboardplugin/releases) or clone this repository.
2. In QGIS, go to **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select the downloaded `.zip` file and click **Install Plugin**.
4. The plugin will appear under **Vector → Layer Dashboard** and as a toolbar icon.

### Option B — Manual Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/okansafak/qgisdashboardplugin.git
   ```
2. Copy the `dynamicdashboard` folder into your QGIS plugins directory:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS and enable **Layer Dashboard** in the Plugin Manager.

---

## 🚀 Quick Start

1. **Open the Dashboard:** Click the dashboard icon in the toolbar, or go to **Vector → Layer Dashboard**.
2. **Select a Layer:** Choose any loaded vector layer from the dropdown at the top of the panel.
3. **Choose Fields:**
   - **Statistics Field** — pick a numeric field for Sum / Average / Min / Max calculations.
   - **Grouping Field** — pick any field to generate distribution charts.
4. **Interact:**
   - Click on a **bar** or **pie slice** to select matching features on the map and zoom to their extent.
   - Use the **search box** to filter table rows across all attributes instantly.
   - Toggle KPI cards on/off using the checkboxes under **Summary Toggles**.

---

## 🌍 Multi-Language Support

The plugin ships with **English** and **Türkçe** translations. The language selector is located in the top-right corner of the dashboard panel.

| Behaviour | Detail |
|---|---|
| **Default language** | Turkish (`tr`) on first launch |
| **Persistence** | Your choice is saved via `QgsSettings` and remembered across sessions |
| **Live switching** | Changing the language instantly rebuilds the entire UI — no restart needed |
| **Adding new languages** | Edit `utils/i18n.py` and add a new key (e.g. `"de"`) to the `LANG` dictionary |

---

## 🏗️ Project Structure

```
dynamicdashboard/
│
├── __init__.py            # QGIS plugin entry point (classFactory)
├── plugin_main.py         # Plugin lifecycle: toolbar, menu, dock management
├── dashboard_dock.py      # Main dock widget: controls, KPI, charts, table, events
├── metadata.txt           # QGIS plugin metadata
├── icon.svg               # Toolbar icon
│
├── ui/                    # UI Components
│   ├── __init__.py
│   └── components.py      # KPICard, BarChart, PieChart widgets + color palettes
│
└── utils/                 # Utilities
    ├── __init__.py
    ├── i18n.py             # Translation dictionary (LANG) + Translator class
    └── stats.py            # Statistical helpers: _nums(), _fmt(), _ok()
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `plugin_main.py` | Registers toolbar icon and menu entry, creates/destroys the dock widget |
| `dashboard_dock.py` | Orchestrates the full dashboard: layer selection, KPI calculation, chart data, table pagination, map selection sync |
| `ui/components.py` | Self-contained PyQt5 widgets for KPI cards and interactive charts with hover/click events |
| `utils/i18n.py` | Centralized translation management with QgsSettings persistence |
| `utils/stats.py` | Pure Python statistical functions decoupled from any Qt/QGIS dependency |

---

## ⚙️ Configuration & Behaviour

### KPI Summary Cards

| Card | Calculation | Notes |
|---|---|---|
| **Total Features** | `len(features)` | All features in the current view (or selected subset) |
| **Selected** | `len(selectedFeatureIds)` | Number of features currently selected on the map |
| **Sum** | `sum(values)` | Requires a numeric statistics field |
| **Average** | `sum / count` | Requires a numeric statistics field |
| **Min** | `min(non-zero values)` | Zero values are excluded to avoid skew from empty/null geometries |
| **Max** | `max(values)` | Requires a numeric statistics field |

Each card can be individually toggled via the checkboxes in the **Summary Toggles** section.

### Pagination

The feature table supports configurable page sizes for handling large datasets:

| Page Size | Recommended Use |
|---|---|
| **50** (default) | General browsing and exploration |
| **100** | Medium datasets |
| **500** | Large datasets with fast hardware |
| **1000** | Maximum density view |

The search bar filters across **all attributes** simultaneously. Pagination automatically resets to page 1 when a search query changes.

### Chart Interaction

- **Bar Chart:** Hover to highlight, click to select matching features on the map.
- **Pie Chart:** Hover to explode the slice, click to select matching features.
- Both charts trigger `zoomToSelected()` so the map viewport adjusts to show all selected features.

---

## 🔧 Requirements

| Requirement | Version |
|---|---|
| **QGIS** | ≥ 3.16 |
| **Python** | 3.x (bundled with QGIS) |
| **Dependencies** | None — uses only PyQt5 and PyQGIS (included in QGIS) |

---

## 🐛 Known Issues & Troubleshooting

| Issue | Solution |
|---|---|
| Plugin doesn't appear after install | Restart QGIS completely. Go to **Plugins → Manage and Install Plugins** and ensure **Layer Dashboard** is checked. |
| `ValueError: source code string cannot contain null bytes` | Delete `__pycache__` folders inside the plugin directory and all subdirectories, then restart QGIS. |
| Cannot uninstall from Plugin Manager | Close QGIS first, manually delete the `dynamicdashboard` folder from the plugins directory, then reopen QGIS. |
| Min value always shows 0 | Fixed in v1.0.0 — zero values are now excluded from the minimum calculation. |

---

## 📝 Changelog

### v1.0.0 (2026-03-29)
- ✅ Initial release with modular architecture
- ✅ KPI summary cards with toggleable visibility
- ✅ Interactive bar and pie charts with map selection
- ✅ Paginated feature table with full-text search
- ✅ Multi-language support (English / Türkçe)
- ✅ Persistent language preference via QgsSettings
- ✅ Zoom-to-extent on chart click
- ✅ Min value calculation excludes zero values

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source. See the repository for license details.

---

## 📬 Contact

- **Repository:** [github.com/okansafak/qgisdashboardplugin](https://github.com/okansafak/qgisdashboardplugin)
- **Issues:** [github.com/okansafak/qgisdashboardplugin/issues](https://github.com/okansafak/qgisdashboardplugin/issues)
