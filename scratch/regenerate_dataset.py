import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler
import os

# 1. Load the original raw dataset (Standardized in previous step)
raw_file = r"C:\Users\Bala murukan\Desktop\Aadhaar_Insight\Aadhaar_Dataset.csv"
print(f"Loading raw data from {raw_file}...")
df = pd.read_csv(raw_file)

# 2. Basic Feature Engineering
print("Performing feature engineering...")
df['total_population'] = df['age_0_5'] + df['age_5_17'] + df['age_18_greater']
df['estimated_voters'] = df['age_18_greater']
df['dependency_ratio'] = np.where(df['age_18_greater'] == 0, 0, (df['age_0_5'] + df['age_5_17']) / df['age_18_greater'])
df['children_ratio'] = np.where(df['total_population'] == 0, 0, (df['age_0_5'] + df['age_5_17']) / df['total_population'])
df['adult_ratio'] = np.where(df['total_population'] == 0, 0, df['age_18_greater'] / df['total_population'])
df['growth_indicator'] = df['bio_age_17_'] - df['demo_age_17_']

# 3. Advanced Features
df['youth_ratio'] = np.where(df['total_population'] == 0, 0, df['age_5_17'] / df['total_population'])
df['aging_index'] = np.where(df['age_0_5'] == 0, 0, df['age_18_greater'] / df['age_0_5'])
df['bio_demo_ratio'] = np.where(df['demo_age_17_'] == 0, 0, df['bio_age_17_'] / df['demo_age_17_'])
# NOTE: future_voters REMOVED as per plan

# 4. Cleansing
df.replace([np.inf, -np.inf], 0, inplace=True)
df.fillna(0, inplace=True)

# 5. Encoding & Scaling
print("Encoding states and districts...")
le_state = LabelEncoder()
df['state_encoded'] = le_state.fit_transform(df['state'].astype(str))
le_district = LabelEncoder()
df['district_encoded'] = le_district.fit_transform(df['district'].astype(str))

# 6. Save final dataset
output_file = "Final_Processed_Dataset.csv"
df.to_csv(output_file, index=False)
print(f"SUCCESS: {output_file} generated with {len(df):,} records and {len(df.columns)} columns.")
print(f"Columns: {list(df.columns)}")
