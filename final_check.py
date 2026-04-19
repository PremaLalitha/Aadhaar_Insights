
import pandas as pd
df = pd.read_csv('Final_Processed_Dataset.csv')
enrolment_total = df['total_population'].sum()
demographic_total = df['demo_age_5_17'].sum() + df['demo_age_17_'].sum()
biometric_total = df['bio_age_5_17'].sum() + df['bio_age_17_'].sum()

print(f"TOTAL_ENROLMENT: {int(enrolment_total)}")
print(f"TOTAL_DEMOGRAPHIC: {int(demographic_total)}")
print(f"TOTAL_BIOMETRIC: {int(biometric_total)}")
