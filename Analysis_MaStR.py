
"""
Analysis_MaStR.py: Processes cleaned Berlin MaStR data into yearly statistics.

This script takes the filtered Berlin solar dataset and calculates:
1. Annual Gross Additions (Zubau) in terms of capacity (kW) and unit count.
2. Annual Decommissioning (Abbau) in terms of capacity (kW) and unit count.
3. Cumulative Net Capacity and Total Units currently in operation.
4. Export of the time-series data for visualization or further reporting.

5. Monthly detail cube (plant type, size class, usage, feed-in type, orientation, tilt)
   for the detail dashboard (detail.html).

Input:  solar_berlin_cleaned.csv
Output: solar_berlin_yearly.csv, solar_berlin_detail.json
"""

__author__      = "afanegas"
__version__     = "1.0"
__date__        = "2025-12-22"

# %%
import json
import pandas as pd


# %%
# 1. Daten laden
INPUT_FILE = 'solar_berlin_cleaned.csv'
df = pd.read_csv(INPUT_FILE, low_memory=False)
# 2. Datum konvertieren
df['Inbetriebnahmedatum'] = pd.to_datetime(df['Inbetriebnahmedatum'], errors='coerce')
df['DatumEndgueltigeStilllegung'] = pd.to_datetime(df['DatumEndgueltigeStilllegung'], errors='coerce')
df['DatumDownload'] = pd.to_datetime(df['DatumDownload'], errors='coerce')

# %%
# --- DYNAMISCHE JAHRESSPANNE ---
min_year = int(df['Inbetriebnahmedatum'].dt.year.min())
max_year = int(max(df['Inbetriebnahmedatum'].dt.year.max(), df['DatumEndgueltigeStilllegung'].dt.year.max()))

# --- 1. JAHR DataFrame ERSTELLEN ---
df_year = pd.DataFrame({'Jahr': range(min_year, max_year + 1)})
#sace Datumdownload in a separate column
df_year['DatumDownload'] = df['DatumDownload'].iloc[0]

# --- 2. ZUBAU ("In Betrieb" + "Endgültig stillgelegt") ---
# Stillgelegte Einheiten zählen im Jahr ihrer Inbetriebnahme als Zubau, da sie in Schritt 3 wieder abgezogen werden
df_year_zubau = df[df['EinheitBetriebsstatus'].isin(["In Betrieb", "Endgültig stillgelegt"])].copy()
df_year_zubau['Jahr'] = df_year_zubau['Inbetriebnahmedatum'].dt.year

zubau_stats = df_year_zubau.groupby('Jahr').agg(
    Zubau_Leistung_kW=('Bruttoleistung', 'sum'),
    Zubau_Anzahl=('Bruttoleistung', 'count')
).reset_index()

# --- 3. ABBAU ("Endgültig stillgelegt") ---
df_year_abbau = df[df['EinheitBetriebsstatus'] == "Endgültig stillgelegt"].copy()
df_year_abbau['Jahr'] = df_year_abbau['DatumEndgueltigeStilllegung'].dt.year

abbau_stats = df_year_abbau.groupby('Jahr').agg(
    Abbau_Leistung_kW=('Bruttoleistung', 'sum'),
    Abbau_Anzahl=('Bruttoleistung', 'count')
).reset_index()

# --- 4. ZUSAMMENFÜHREN IN df_year ---
df_year = df_year.merge(zubau_stats, on='Jahr', how='left')
df_year = df_year.merge(abbau_stats, on='Jahr', how='left')
df_year = df_year.fillna(0)

# --- 5. NETTO-ZUBAU PRO JAHR ---
df_year['Netto_Zubau_Leistung_kW'] = df_year['Zubau_Leistung_kW'] - df_year['Abbau_Leistung_kW']
df_year['Netto_Zubau_Anzahl'] = df_year['Zubau_Anzahl'] - df_year['Abbau_Anzahl']

# --- 6. NETTO-BESTAND & KUMULIERUNG  ---
df_year['Kum_Zubau_kW'] = df_year['Zubau_Leistung_kW'].cumsum()
df_year['Kum_Abbau_kW'] = df_year['Abbau_Leistung_kW'].cumsum()
df_year['Bestand_Leistung_kW'] = df_year['Kum_Zubau_kW'] - df_year['Kum_Abbau_kW']

df_year['Kum_Zubau_Anzahl'] = df_year['Zubau_Anzahl'].cumsum()
df_year['Kum_Abbau_Anzahl'] = df_year['Abbau_Anzahl'].cumsum()
df_year['Bestand_Anzahl'] = df_year['Kum_Zubau_Anzahl'] - df_year['Kum_Abbau_Anzahl']



# %%
# --- 7. FILTER AB 2005 ---
df_year_05 = df_year[df_year['Jahr'] >= 2005].copy()

# %%
# Export des vollständigen DataFrames (gesamte Historie)
OUTPUT_FILE = 'solar_berlin_yearly.csv'
df_year.to_csv(OUTPUT_FILE, 
              index=False,           # Verhindert, dass die Zeilennummern als eigene Spalte gespeichert werden
              sep=',',               # Standard-Komma als Trenner
              encoding='utf-8-sig')  # Sorgt für korrekte Umlaute in Excel

print("Export erfolgreich: Die Datei 'solar_berlin_yearly.csv' wurde erstellt.")

# %%
# --- 8. DETAIL-WÜRFEL (für detail.html) ---
# Monatliche Zu- und Abgänge je Anlagentyp und Merkmal. Gleicher Statusfilter wie beim Jahres-CSV,
# damit der Bestand auf beiden Seiten identisch ist.
df_detail = df[df['EinheitBetriebsstatus'].isin(["In Betrieb", "Endgültig stillgelegt"])].copy()

# Balkonkraftwerk: im MaStR als steckerfertig gemeldet ODER Bruttoleistung <= 2 kWp und Nettonennleistung <= 800 W
ist_stecker = df_detail['ArtDerSolaranlage'].str.startswith('Stecker', na=False)
ist_klein = (df_detail['Bruttoleistung'] <= 2) & (df_detail['Nettonennleistung'] <= 0.8)
df_detail['Segment'] = (ist_stecker | ist_klein).astype(int)  # 0 = Gebäude/Freifläche, 1 = Balkonkraftwerk

KEINE_ANGABE = 'keine Angabe'
# Reihenfolge der Kategorien je Merkmal (Index = Kategorie-Nummer im Würfel)
DETAIL_ORDER = {
    'groesse': ['≤ 2 kWp', '2–10 kWp', '10–30 kWp', '30–100 kWp', '100–750 kWp', '> 750 kWp'],
    'nutzung': ['Haushalt', 'Gewerbe, Handel, Dienstl.', 'Öffentliches Gebäude', 'Industrie', 'Sonstige', KEINE_ANGABE],
    'einspeisung': ['Teileinspeisung / Eigenverbrauch', 'Volleinspeisung', KEINE_ANGABE],
    'ausrichtung': ['Süd', 'Süd-West', 'Süd-Ost', 'Ost-West', 'Ost', 'West', 'Nord / NO / NW', KEINE_ANGABE],
    'neigung': ['< 5° (flach)', '5–20°', '21–40°', '41–60°', '61–89°', '90° (vertikal)', KEINE_ANGABE],
}
# MaStR-Werte -> Kategorien (nicht aufgeführte Werte bleiben unverändert)
DETAIL_MAPPING = {
    'nutzung': ('Nutzungsbereich', {'Gewerbe, Handel und Dienstleistungen': 'Gewerbe, Handel, Dienstl.',
                                    'Landwirtschaft': 'Sonstige'}),
    'einspeisung': ('Einspeisungsart', {'Teileinspeisung (einschließlich Eigenverbrauch)': 'Teileinspeisung / Eigenverbrauch'}),
    'ausrichtung': ('Hauptausrichtung', {'Nord': 'Nord / NO / NW', 'Nord-Ost': 'Nord / NO / NW',
                                         'Nord-West': 'Nord / NO / NW', 'nachgeführt': KEINE_ANGABE}),
    'neigung': ('HauptausrichtungNeigungswinkel', {'unter 5 Grad (horizontal)': '< 5° (flach)', '5 - 20 Grad': '5–20°',
                                                   '21 - 40 Grad': '21–40°', '41 - 60 Grad': '41–60°',
                                                   '61 - 89 Grad': '61–89°', '90 Grad (vertikal)': '90° (vertikal)',
                                                   'Nachgeführt': KEINE_ANGABE}),
}

detail_kategorien = {
    'groesse': pd.cut(df_detail['Bruttoleistung'], bins=[0, 2, 10, 30, 100, 750, float('inf')],
                      labels=DETAIL_ORDER['groesse']).astype(str)
}
for name, (spalte, mapping) in DETAIL_MAPPING.items():
    # MaStR liefert teils Werte mit Leerzeichen am Ende
    kategorie = df_detail[spalte].str.strip().replace(mapping).fillna(KEINE_ANGABE)
    unbekannt = ~kategorie.isin(DETAIL_ORDER[name])
    if unbekannt.any():
        print(f"Hinweis: unbekannte Werte in {spalte} als '{KEINE_ANGABE}' gezählt: {sorted(kategorie[unbekannt].unique())}")
        kategorie[unbekannt] = KEINE_ANGABE
    detail_kategorien[name] = kategorie

DETAIL_MIN_YEAR = 2009  # ältere Jahre werden in diesem Jahr zusammengefasst (zählen nur für den Bestand)
ist_stillgelegt = df_detail['EinheitBetriebsstatus'] == "Endgültig stillgelegt"
detail = {
    'stand': df['DatumDownload'].iloc[0].strftime('%Y-%m-%d'),
    'order': DETAIL_ORDER,
    'dims': {},
}
for name, kategorie in detail_kategorien.items():
    kategorie_nr = kategorie.map({k: i for i, k in enumerate(DETAIL_ORDER[name])})
    zeilen = []
    # Zeile: [Jahr, Monat, Segment, Kategorie, Anzahl, kW]; Stilllegungen mit negativem Vorzeichen
    for vorzeichen, datum, maske in ((1, df_detail['Inbetriebnahmedatum'], slice(None)),
                                     (-1, df_detail['DatumEndgueltigeStilllegung'], ist_stillgelegt)):
        ereignisse = pd.DataFrame({
            'Jahr': datum.dt.year.clip(lower=DETAIL_MIN_YEAR),
            'Monat': datum.dt.month,
            'Segment': df_detail['Segment'],
            'Kategorie': kategorie_nr,
            'kW': df_detail['Bruttoleistung'],
        })[maske].dropna(subset=['Jahr'])
        gruppen = ereignisse.groupby(['Jahr', 'Monat', 'Segment', 'Kategorie']).agg(
            Anzahl=('kW', 'count'), kW=('kW', 'sum')).reset_index()
        zeilen += [[int(g.Jahr), int(g.Monat), int(g.Segment), int(g.Kategorie),
                    vorzeichen * int(g.Anzahl), round(vorzeichen * g.kW, 1)] for g in gruppen.itertuples()]
    detail['dims'][name] = zeilen

DETAIL_FILE = 'solar_berlin_detail.json'
with open(DETAIL_FILE, 'w', encoding='utf-8') as f:
    json.dump(detail, f, ensure_ascii=False, separators=(',', ':'))

print(f"Export erfolgreich: Die Datei '{DETAIL_FILE}' wurde erstellt.")
