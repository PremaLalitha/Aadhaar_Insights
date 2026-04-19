
import os
import pandas as pd
from glob import glob

def get_row_count(file_path):
    try:
        # Just read the first column to get the count quickly
        return len(pd.read_csv(file_path, usecols=[0]))
    except Exception as e:
        return 0

base_dir = r"c:\Users\Bala murukan\Desktop\Aadhaar_Insights"
folders = {
    "Enrolment": os.path.join(base_dir, "Enrolment", "original_DB"),
    "Biometric": os.path.join(base_dir, "biometric", "original_DB"),
    "Demographic": os.path.join(base_dir, "Demographic", "original_DB")
}

initial_counts = {}
total_initial = 0
for name, folder in folders.items():
    files = glob(os.path.join(folder, "*.csv"))
    f_total = 0
    for f in files:
        f_total += get_row_count(f)
    initial_counts[name] = (len(files), f_total)
    total_initial += f_total

master_path = os.path.join(base_dir, "Aadhaar_Insight", "FE", "Master_Cleaned_Dataset.csv")
master_count = get_row_count(master_path) if os.path.exists(master_path) else 0

final_path = os.path.join(base_dir, "Aadhaar_Insight", "Final_Processed_Dataset.csv")
final_count = get_row_count(final_path) if os.path.exists(final_path) else 0

report = f"""
# Data Pipeline Row Counts

### 📂 Stage 1: Initial Collection (Raw Folders)
- **Enrolment Folder:** {initial_counts['Enrolment'][0]} Files | {initial_counts['Enrolment'][1]:,} Rows
- **Biometric Folder:** {initial_counts['Biometric'][0]} Files | {initial_counts['Biometric'][1]:,} Rows
- **Demographic Folder:** {initial_counts['Demographic'][0]} Files | {initial_counts['Demographic'][1]:,} Rows
- **TOTAL INITIAL ROWS:** **{total_initial:,}**

### 🧹 Stage 2: After Merging & Cleaning
- **Master Cleaned Dataset:** **{master_count:,}** Rows
- **Rows Removed (Duplicates/Noise):** **{total_initial - master_count:,}**

### ✨ Stage 3: By the End (Final Processed)
- **Final Processed Dataset:** **{final_count:,}** Rows
- **Total Optimization (Grouping for Dashboard):** **{master_count - final_count:,}** records consolidated.
"""

with open("data_report.md", "w", encoding='utf-8') as f:
    f.write(report)
print("Report generated: data_report.md")
