from qgis.core import QgsSettings

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

class Translator:
    def __init__(self):
        # QgsSettings().value can sometimes be a QVariant object in older QGIS Python bindings,
        # forcing it to string avoids exceptions like 'QVariant' object has no attribute ...
        val = QgsSettings().value("LayerDashboard/Locale", "tr")
        self.lang = str(val) if val else "tr"
        if self.lang not in LANG:
            self.lang = "en"

    def set_lang(self, code):
        if code in LANG:
            self.lang = code
            QgsSettings().setValue("LayerDashboard/Locale", code)

    def current(self):
        return self.lang

    def tr(self, key):
        return LANG.get(self.lang, LANG["en"]).get(key, key)
