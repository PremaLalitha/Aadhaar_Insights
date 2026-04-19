import pandas as pd
df = pd.read_csv('FE/Master_Cleaned_Dataset.csv')
print("New Enrolments:", df[['age_0_5', 'age_5_17', 'age_18_greater']].sum().sum())
print("Demographic Updates:", df[['demo_age_5_17', 'demo_age_17_']].sum().sum())
print("Biometric Updates:", df[['bio_age_5_17', 'bio_age_17_']].sum().sum())
print("Est. Voters:", df['age_18_greater'].sum())
