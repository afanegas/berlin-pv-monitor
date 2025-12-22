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
__version__     = "1.0"
__date__        = "2025-12-22"

# %%
from datetime import date
import glob
import shutil
import os
import pandas as pd
from open_mastr import Mastr
os.environ["OUTPUT_PATH"] = "open_mastr"
os.environ['NUMBER_OF_PROCESSES'] = "3"

#If fol multiprocessing:
if __name__ == "__main__":
  
    # %%
    
    # Initialize the Mastr object
    db = Mastr()
    
    print("Starting parallelized download on ...")
    #db.download(data=["solar"])    
    print("Converting to CSV...")
    db.to_csv(tables=["solar"], chunksize=50000)
    
    print("Success! Data is ready.")
    
    
    # %% [markdown]
    # ### Import Berlin Units from the CSV, export to new CSV
    
    # %%
    today = date.today().isoformat()
    file_path = f"open_mastr/data/dataversion-{today}/bnetza_mastr_solar_raw.csv"
    output_file = "solar_berlin.csv"
    output_file_cleaned = 'solar_berlin_cleaned.csv'
    
    # %%
    
    # 1. Clear the output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # 2. Use Chunking 
    reader = pd.read_csv(file_path, chunksize=100000, low_memory=False)
    
    print("Starting the filtering process... This will take a moment")
    
    for i, chunk in enumerate(reader):
        # Filter for Berlin
        berlin_chunk = chunk[chunk['Bundesland'] == 'Berlin']
        
        # Append to the small file
        if not berlin_chunk.empty:
            berlin_chunk.to_csv(output_file, mode='a', index=False, header=not os.path.exists(output_file))
        
        # Progress update
        if i % 5 == 0:
            print(f"Read {i * 100000} rows...")
    
    print(f"Finished! Your Berlin-only data is saved in {output_file}")
    
    # %% [markdown]
    # ### Read Berlin-CSV, Create Cleaned-Berlin-CSV
    
    # %%
    df_berlin = pd.read_csv(output_file, low_memory=False)
    
    # %%
    print(f"Shape: {df_berlin.shape}")
    df_berlin.info()
    list(df_berlin.columns)
    
    # %% [markdown]
    # * Delete Columns that are empty
    
    # %%
    # 1. Create the clean copy
    # axis=1: look at columns
    # how='all': only drop if every single value in the column is NaN
    df_berlin_clean = df_berlin.dropna(axis=1, how='all').copy()
    
    # 2. Print a summary of what happened
    original_cols = df_berlin.shape[1]
    remaining_cols = df_berlin_clean.shape[1]
    removed_cols = original_cols - remaining_cols
    
    print("Clean-up finished!")
    print(f"Columns before: {original_cols}")
    print(f"Columns removed: {removed_cols} (these were 100% empty)")
    print(f"Columns remaining: {remaining_cols}")
    
    print("Remaining Columns: ",list(df_berlin_clean.columns))
    
    # 3. View the result
    df_berlin_clean.head()
    
    # %% [markdown]
    # * Cleaning Rows with address outside Berlin
    
    # %%
    print("Unique values in Landkreis:")
    print(df_berlin_clean['Landkreis'].unique())
    
    print("\nUnique values in Gemeinde:")
    print(df_berlin_clean['Gemeinde'].unique())
    
    # Overwriting the current dataframe with the filtered version
    print(f"Rows before cleaning: {len(df_berlin_clean)}")
    df_berlin_clean = df_berlin_clean[
        (df_berlin_clean['Landkreis'] == 'Berlin') & 
        (df_berlin_clean['Gemeinde'] == 'Berlin')
    ].copy()
    
    print(f"Filter applied. Remaining rows: {len(df_berlin_clean)}")
    
    # %%
    # Save the cleaned dataframe
    # index=False prevents pandas from adding an extra 'unnamed: 0' column
    df_berlin_clean.to_csv(output_file_cleaned, index=False, encoding='utf-8-sig')
    print(f"Successfully exported: {output_file_cleaned}")
    
    ### Clean old files
    data_path = "open_MaStR/data"
    # 1. Delete the heavy ZIP files
    zip_path = os.path.join(data_path, "xml_download")
    if os.path.exists(zip_path):
        shutil.rmtree(zip_path)
        os.makedirs(zip_path) # Leave empty folder for next run
        print("Cleared raw ZIPs.")
    # 2. Delete old CSV export folders (dataversion-...)
    old_exports = glob.glob(os.path.join(data_path, "dataversion-*"))
    for folder in old_exports:
        shutil.rmtree(folder)
        print(f"Deleted old export: {folder}")