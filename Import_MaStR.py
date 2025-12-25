"""
Import_MaStR.py: Downloads and filters German solar data for Berlin.

This script automates the retrieval of the Marktstammdatenregister (MaStR) 
bulk data, converts the massive XML/JSON structure into a CSV format, 
and extracts only the records relevant to Berlin to save memory and 
processing time for downstream analysis.

Main Steps:
1. Download solar data from MaStR (Multiprocess enabled).
2. Export raw data to a local CSV using memory-safe chunking.
3. Filter the global dataset specifically for Berlin-based units.
4. Clean the Berlin data by removing empty columns and non-local records.

Inputs: MaStR Bulk Download (External API/Bulk)
Outputs: solar_berlin.csv, solar_berlin_cleaned.csv
"""

__author__      = "afanegas"
__version__     = "1.1"
__date__        = "2025-12-24"

# %%
from datetime import date
import glob
import shutil
import os
import pandas as pd
os.environ["OUTPUT_PATH"] = "open_mastr"
os.environ['NUMBER_OF_PROCESSES'] = "1"
import sqlalchemy
from open_mastr import Mastr
from open_mastr.utils import orm
from open_mastr.utils.helpers import create_db_query, db_query_to_csv, reverse_fill_basic_units


#If fol multiprocessing:
if __name__ == "__main__":
  
    # Initialize the Mastr object
    db = Mastr()
    print(f"DEBUG: Process count set to: {os.environ.get('NUMBER_OF_PROCESSES')}")
    
    print("Starting parallelized download on ...")
    db.download(data=["solar"])    
    print("Converting to CSV...")
    
    #Importing the whole solar-table with the standard open-mastr-fucntion (to_csv) takes a lot of time, alternativ method is used
    #db.to_csv(tables=["solar"], chunksize=50000)
    
    ################
    #Alternativ method, exportin only Berlin
    #Manually create the directory because we bypassed db.to_csv()
    today_str = date.today().strftime("%Y-%m-%d")
    export_dir = os.path.join("open_mastr", "data", f"dataversion-{today_str}")
    os.makedirs(export_dir, exist_ok=True)
    print(f"Created export directory: {export_dir}")
    #Building Master List & Query for Berlin
    reverse_fill_basic_units(technology=["solar"], engine=db.engine) # Rebuilds Master List, part of the original to_csv function
    solar_query = create_db_query(tech="solar", engine=db.engine)
    solar_query = solar_query.filter(sqlalchemy.text("Bundesland = 'Berlin'"))
    db_query_to_csv(
        db_query=solar_query, 
        data_table="solar", 
        chunksize=10000 
    )
    #################
    print("Success! Data is ready.")
    
    #Path setting
    base_path = 'open_mastr/data/dataversion-*/bnetza_mastr_solar_raw.csv'
    file_path = sorted(glob.glob(base_path))[-1]
    output_file_cleaned = 'solar_berlin_cleaned.csv'
    
    # Import file CSV for cleaning
    df_berlin = pd.read_csv(file_path, low_memory=False)
    #print(f"Shape: {df_berlin.shape}")
    #df_berlin.info()
    #list(df_berlin.columns)
    
    # Delete Columns that are empty
    df_berlin_clean = df_berlin.dropna(axis=1, how='all').copy()
    
    # Print a summary of what happened
    original_cols = df_berlin.shape[1]
    remaining_cols = df_berlin_clean.shape[1]
    removed_cols = original_cols - remaining_cols  
    print("Clean-up finished!")
    print(f"Columns before: {original_cols}")
    print(f"Columns removed: {removed_cols} (these were 100% empty)")
    print(f"Columns remaining: {remaining_cols}")

    
    #Cleaning Rows with address outside Berlin
    print("Unique values in Landkreis:")
    print(df_berlin_clean['Landkreis'].unique())  
    print("\nUnique values in Gemeinde:")
    print(df_berlin_clean['Gemeinde'].unique())
    print(f"Rows before cleaning: {len(df_berlin_clean)}")
    df_berlin_clean = df_berlin_clean[
        (df_berlin_clean['Landkreis'] == 'Berlin') & 
        (df_berlin_clean['Gemeinde'] == 'Berlin')
    ].copy()    
    print(f"Filter applied. Remaining rows: {len(df_berlin_clean)}")
    # Save the cleaned dataframe
    df_berlin_clean.to_csv(output_file_cleaned, index=False, encoding='utf-8-sig')
    print(f"Successfully exported: {output_file_cleaned}")
    
    ### Clean old files
    data_path = "open_mastr/data"
    # Delete the heavy ZIP files
    zip_path = os.path.join(data_path, "xml_download")
    if os.path.exists(zip_path):
        shutil.rmtree(zip_path)
        os.makedirs(zip_path) # Leave empty folder for next run
        print("Cleared raw ZIPs.")
    # Delete old CSV export folders (dataversion-...)
    old_exports = glob.glob(os.path.join(data_path, "dataversion-*"))
    for folder in old_exports:
        shutil.rmtree(folder)
        print(f"Deleted old export: {folder}")