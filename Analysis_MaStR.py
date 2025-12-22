
"""
Analysis_MaStR.py: Processes cleaned Berlin MaStR data into yearly statistics.

This script takes the filtered Berlin solar dataset and calculates:
1. Annual Gross Additions (Zubau) in terms of capacity (kW) and unit count.
2. Annual Decommissioning (Abbau) in terms of capacity (kW) and unit count.
3. Cumulative Net Capacity and Total Units currently in operation.
4. Export of the time-series data for visualization or further reporting.

Input:  solar_berlin_cleaned.csv
Output: solar_berlin_yearly.csv
"""

__author__      = "afanegas"
__version__     = "1.0"
__date__        = "2025-12-22"

# %%
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

# --- 2. ZUBAU ("In Betrieb") ---
df_year_zubau = df[df['EinheitBetriebsstatus'] == "In Betrieb"].copy()
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
