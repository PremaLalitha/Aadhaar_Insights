import pandas as pd
import os

# -----------------------------
# STEP 1: PATH SETUP
# -----------------------------
DATA_DIR = "data"          # enrolment CSV files location
OUTPUT_DIR = "output"      # merged file destination

# Create output folder if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------
# STEP 2: LOAD ENROLMENT FILES
# -----------------------------
df1 = pd.read_csv(os.path.join(DATA_DIR, "enrolment1.csv"))
df2 = pd.read_csv(os.path.join(DATA_DIR, "enrolment2.csv"))
df3 = pd.read_csv(os.path.join(DATA_DIR, "enrolment3.csv"))

# -----------------------------
# STEP 3: MERGE DATA
# -----------------------------
final_df = pd.concat([df1, df2, df3], ignore_index=True)

# -----------------------------
# STEP 4: SAVE MERGED DATA
# -----------------------------
output_path = os.path.join(OUTPUT_DIR, "Aadhar_enrolment.csv")
final_df.to_csv(output_path, index=False)

# -----------------------------
# STEP 5: CONFIRMATION
# -----------------------------
print("Enrolment files merged successfully!")
print("Saved at:", output_path)
print(final_df.head())
