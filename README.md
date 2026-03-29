# 📊 Layer Dashboard — QGIS Plugin

[English](#english) | [Türkçe](#türkçe)

---

<a name="english"></a>
## 🇬🇧 English

**Layer Dashboard** is a powerful, interactive analytics dock panel for QGIS that transforms any vector layer into a live dashboard with KPI summary cards, bar/pie charts, a paginated feature table, and map-linked selection — all without leaving QGIS.

### ✨ Features
| Feature | Description |
|---|---|
| **KPI Summary Cards** | Total features, selected count, sum, average, min, max — toggleable on/off |
| **Bar & Pie Charts** | Grouped distribution charts with click-to-select-on-map interaction |
| **Paginated Table** | High-performance feature table with search and configurable page sizes |
| **Multi-Language** | English / Türkçe UI with persistent language preference |
| **Zoom to Selection** | Click a chart slice or bar → features are selected and zoomed to on the map |

### 📦 Installation
1. Download the latest release `.zip` from [Releases](https://github.com/okansafak/qgisdashboardplugin/releases).
2. In QGIS: **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select the `.zip` file and click **Install Plugin**.

### 🚀 Quick Start
1. **Open:** Click the dashboard icon in the toolbar or **Vector → Layer Dashboard**.
2. **Select Layer:** Choose a vector layer from the dropdown.
3. **Fields:** Pick a **Statistics Field** (numeric) and a **Grouping Field**.
4. **Interact:** Click charts to select/zoom on map, use search for the table.

---

<a name="türkçe"></a>
## 🇹🇷 Türkçe

**Layer Dashboard**, herhangi bir vektör katmanını KPI özet kartları, bar/pasta grafikleri, sayfalı özellik tablosu ve harita bağlantılı seçim özellikleriyle canlı bir panoya dönüştüren güçlü ve etkileşimli bir QGIS eklentisidir.

### ✨ Özellikler
| Özellik | Açıklama |
|---|---|
| **KPI Özet Kartları** | Toplam nesne, seçili sayısı, toplam, ortalama, min, maks — açılıp kapatılabilir |
| **Bar ve Pasta Grafikleri** | Haritadan seçim etkileşimli gruplandırılmış dağılım grafikleri |
| **Sayfalı Tablo** | Arama özellikli ve yapılandırılabilir sayfa boyutlu yüksek performanslı tablo |
| **Çoklu Dil** | Kalıcı dil tercihi ile İngilizce / Türkçe arayüz |
| **Seçime Yakınlaş** | Grafik dilimine veya çubuğuna tıkla → nesneler seçilir ve haritada odaklanır |

### 📦 Kurulum
1. En son sürüm `.zip` dosyasını [Releases](https://github.com/okansafak/qgisdashboardplugin/releases) sayfasından indirin.
2. QGIS'te: **Eklentiler → Eklentileri Yönet ve Yükle → ZIP'ten Yükle**.
3. `.zip` dosyasını seçin ve **Eklentiyi Kur** butonuna tıklayın.

### 🚀 Hızlı Başlangıç
1. **Aç:** Araç çubuğundaki pano simgesine veya **Vektör → Layer Dashboard** menüsüne tıklayın.
2. **Katman Seç:** Açılır menüden bir vektör katmanı seçin.
3. **Alanlar:** Bir **İstatistik Alanı** (sayısal) ve bir **Gruplama Alanı** seçin.
4. **Etkileşim:** Haritada seçmek/odaklanmak için grafiklere tıklayın, tablo için aramayı kullanın.

---

## 🌍 Multi-Language Support / Çoklu Dil Desteği

The plugin ships with **English** and **Türkçe** translations. / Eklenti **İngilizce** ve **Türkçe** çevirileriyle birlikte gelir.

| Detail / Detay | Description / Açıklama |
|---|---|
| **Persistence / Kalıcılık** | Sorted via `QgsSettings` / `QgsSettings` ile kaydedilir |
| **Live switching / Anlık Geçiş** | UI updates instantly / Arayüz anında güncellenir |

## 🏗️ Project Structure / Proje Yapısı

```
dynamicdashboard/
├── ui/              # UI Components / Arayüz Bileşenleri
├── utils/           # Utilities / Yardımcı Araçlar (Translation, Stats)
├── dashboard_dock.py # Main Dock Logic / Ana Panel Mantığı
├── plugin_main.py    # Plugin Entry / Eklenti Girişi
└── metadata.txt      # Metadata / Üst Veri
```

---

## ⚙️ Configuration / Yapılandırma

### KPI Summary Cards / KPI Özet Kartları
- **Min:** Zero values are excluded to avoid skew. / Sıfır değerler, istatistiği bozmaması için hariç tutulur.
- **Max/Sum/Avg:** Requires numeric field. / Sayısal alan gerektirir.

### Pagination / Sayfalandırma
Supports 50, 100, 500, 1000 records per page. / Sayfa başına 50, 100, 500, 1000 kayıt destekler.

---

## 🔧 Requirements / Gereksinimler
- **QGIS:** ≥ 3.16
- **Python:** 3.x

---

## 📬 Contact / İletişim
- **Repository:** [github.com/okansafak/qgisdashboardplugin](https://github.com/okansafak/qgisdashboardplugin)
- **Issues:** [github.com/okansafak/qgisdashboardplugin/issues](https://github.com/okansafak/qgisdashboardplugin/issues)
