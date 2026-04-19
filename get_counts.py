
import os
import pandas as pd
from glob import glob

def get_row_count(file_path):
    try:
        # Just read the first column to get the count quickly
        return len(pd.read_csv(file_path, usecols=[0]))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

base_dir = r"c:\Users\Bala murukan\Desktop\Aadhaar_Insights"
folders = {
    "Enrolment": os.path.join(base_dir, "Enrolment"),
    "Biometric": os.path.join(base_dir, "biometric"),
    "Demographic": os.path.join(base_dir, "Demographic")
}

print("--- STEP 1: INITIAL COLLECTION (RAW STORAGE) ---")
total_initial = 0
for name, folder in folders.items():
    files = glob(os.path.join(folder, "*.csv"))
    print(f"Folder: {name} | Files: {len(files)}")
    folder_total = 0
    for f in files:
        count = get_row_count(f)
        folder_total += count
    print(f"  -> Total Rows in {name}: {folder_total:,}")
    total_initial += folder_total

print(f"\n[SUMMARY] TOTAL INITIAL ROWS (Unprocessed): {total_initial:,}")

print("\n--- STEP 2: DATA MERGING & CLEANING (GLOBAL MASTER) ---")
master_path = os.path.join(base_dir, "Aadhaar_Insight", "FE", "Master_Cleaned_Dataset.csv")
if os.path.exists(master_path):
    master_count = get_row_count(master_path)
    print(f"Rows in Master_Cleaned_Dataset.csv: {master_count:,}")
    print(f"Data Rescued/Cleaned: {total_initial - master_count:,} duplicates/noise removed.")
else:
    print("Master_Cleaned_Dataset.csv not found.")

print("\n--- STEP 3: FINAL OUTPUT (ENGINEERED DATASET) ---")
final_path = os.path.join(base_dir, "Aadhaar_Insight", "Final_Processed_Dataset.csv")
if os.path.exists(final_path):
    final_count = get_row_count(final_path)
    print(f"Rows in Final_Processed_Dataset.csv: {final_count:,}")
    print(f"Final Gain/Shrink (Grouping for Dashboard): {master_count - final_count:,} records grouped by (State/Date/Pincode).")
else:
    print("Final_Processed_Dataset.csv not found.")
