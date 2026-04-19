#!/usr/bin/env python
"""
Manual Step-by-Step Voter Classification - No Visualizations
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score

print("\n" + "="*80)
print("🔍 MANUAL STEP-BY-STEP CLASSIFICATION VERIFICATION (No Visualizations)")
print("="*80)

# ==========================================
# STEP 1: LOAD DATA
# ==========================================
print("\n[STEP 1] LOAD DATA")
print("-" * 80)
df = pd.read_csv('Final_Processed_Dataset.csv')
print(f"Dataset Shape: {df.shape}")
print(f"Columns: {list(df.columns)[:10]}... (showing first 10)")
print(f"\nFirst 3 rows:")
print(df.head(3))

# ==========================================
# STEP 2: DATA PREPROCESSING
# ==========================================
print("\n[STEP 2] DATA PREPROCESSING")
print("-" * 80)
df_clean = df.copy()
df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')

df_clean['has_biometric'] = (df_clean['bio_age_17_'] > 0).astype(int)
df_clean['has_demographic'] = (df_clean['demo_age_17_'] > 0).astype(int)
df_clean['age_18_plus'] = (df_clean['age_18_greater'] > 0).astype(int)
df_clean['eligible_voter'] = (
    (df_clean['age_18_plus'] == 1) &
    ((df_clean['has_biometric'] == 1) | (df_clean['has_demographic'] == 1))
).astype(int)

print(f"✓ Eligible Voters: {df_clean['eligible_voter'].sum():,} ({df_clean['eligible_voter'].mean()*100:.2f}%)")
print(f"✓ Not Eligible: {(1-df_clean['eligible_voter']).sum():,} ({(1-df_clean['eligible_voter']).mean()*100:.2f}%)")
print(f"✓ Total Dataset: {len(df_clean):,} records")

# ==========================================
# STEP 3: PREPARE FEATURES & SPLIT DATA (80-20)
# ==========================================
print("\n[STEP 3] PREPARE FEATURES & SPLIT DATA (80-20)")
print("-" * 80)

features = [
    'bio_age_5_17', 'bio_age_17_', 'demo_age_5_17', 'demo_age_17_',
    'age_0_5', 'age_5_17', 'age_18_greater',
    'dependency_ratio', 'children_ratio', 'adult_ratio', 'youth_ratio',
    'aging_index', 'bio_demo_ratio',
    'state_encoded', 'district_encoded',
    'month', 'year'
]

X = df_clean[features].fillna(0)
y = df_clean['eligible_voter']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"✓ Features: {len(features)} selected")
print(f"✓ Training Set: {len(X_train):,} records ({len(X_train)/len(X)*100:.1f}%)")
print(f"✓ Testing Set: {len(X_test):,} records ({len(X_test)/len(X)*100:.1f}%)")
print(f"✓ Features scaled using StandardScaler")

# ==========================================
# STEP 4: TRAIN CLASSIFICATION MODELS
# ==========================================
print("\n[STEP 4] TRAIN CLASSIFICATION MODELS")
print("-" * 80)

# Model 1: Logistic Regression
print("\n[4.1] Logistic Regression")
lr_model = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
lr_model.fit(X_train_scaled, y_train)
y_pred_lr = lr_model.predict(X_test_scaled)

lr_acc = accuracy_score(y_test, y_pred_lr)
lr_prec = precision_score(y_test, y_pred_lr)
lr_rec = recall_score(y_test, y_pred_lr)
lr_f1 = f1_score(y_test, y_pred_lr)
lr_auc = roc_auc_score(y_test, lr_model.predict_proba(X_test_scaled)[:, 1])

print(f"   Accuracy:  {lr_acc:.6f}")
print(f"   Precision: {lr_prec:.6f}")
print(f"   Recall:    {lr_rec:.6f}")
print(f"   F1-Score:  {lr_f1:.6f}")
print(f"   ROC-AUC:   {lr_auc:.6f}")

# Model 2: Random Forest
print("\n[4.2] Random Forest Classifier")
rf_model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
rf_model.fit(X_train_scaled, y_train)
y_pred_rf = rf_model.predict(X_test_scaled)

rf_acc = accuracy_score(y_test, y_pred_rf)
rf_prec = precision_score(y_test, y_pred_rf)
rf_rec = recall_score(y_test, y_pred_rf)
rf_f1 = f1_score(y_test, y_pred_rf)
rf_auc = roc_auc_score(y_test, rf_model.predict_proba(X_test_scaled)[:, 1])

print(f"   Accuracy:  {rf_acc:.6f}")
print(f"   Precision: {rf_prec:.6f}")
print(f"   Recall:    {rf_rec:.6f}")
print(f"   F1-Score:  {rf_f1:.6f}")
print(f"   ROC-AUC:   {rf_auc:.6f}")

# ==========================================
# STEP 5: MODEL COMPARISON
# ==========================================
print("\n[STEP 5] MODEL COMPARISON")
print("-" * 80)

comparison = pd.DataFrame({
    'Model': ['Logistic Regression', 'Random Forest'],
    'Accuracy': [lr_acc, rf_acc],
    'Precision': [lr_prec, rf_prec],
    'Recall': [lr_rec, rf_rec],
    'F1-Score': [lr_f1, rf_f1],
    'ROC-AUC': [lr_auc, rf_auc]
})

print("\n" + comparison.to_string(index=False))

best_idx = comparison['Accuracy'].idxmax()
best_name = comparison.loc[best_idx, 'Model']
best_acc = comparison.loc[best_idx, 'Accuracy']

print(f"\n✅ BEST MODEL: {best_name} (Accuracy: {best_acc:.6f})")

# ==========================================
# STEP 6: CONFUSION MATRIX
# ==========================================
print("\n[STEP 6] CONFUSION MATRIX - BEST MODEL")
print("-" * 80)

if best_idx == 0:
    y_pred_best = y_pred_lr
else:
    y_pred_best = y_pred_rf

cm = confusion_matrix(y_test, y_pred_best)

print(f"\n                  Predicted Negative  Predicted Positive")
print(f"Actual Negative:  {cm[0,0]:>19,}  {cm[0,1]:>19,}")
print(f"Actual Positive:  {cm[1,0]:>19,}  {cm[1,1]:>19,}")

tn, fp, fn, tp = cm.ravel()
specificity = tn / (tn + fp)
sensitivity = tp / (tp + fn)
print(f"\n✓ True Negatives:  {tn:,}")
print(f"✓ False Positives: {fp:,}")
print(f"✓ False Negatives: {fn:,}")
print(f"✓ True Positives:  {tp:,}")
print(f"✓ Sensitivity (Recall): {sensitivity:.6f}")
print(f"✓ Specificity: {specificity:.6f}")

# ==========================================
# FINAL SUMMARY
# ==========================================
print("\n" + "="*80)
print("📋 CLASSIFICATION MODEL SUMMARY")
print("="*80)

print(f"""
✅ VOTER ELIGIBILITY CLASSIFICATION
   Best Model: {best_name}
   Accuracy: {best_acc*100:.2f}%
   Precision: {comparison.loc[best_idx, 'Precision']:.6f}
   Recall: {comparison.loc[best_idx, 'Recall']:.6f}
   F1-Score: {comparison.loc[best_idx, 'F1-Score']:.6f}
   ROC-AUC: {comparison.loc[best_idx, 'ROC-AUC']:.6f}

✅ KEY METRICS:
   Eligible Voters: {df_clean['eligible_voter'].sum():,}
   Training Records: {len(X_train):,}
   Test Records: {len(X_test):,}
   Polling Stations: {int(df_clean['eligible_voter'].sum() / 500):,}

📊 VERIFICATION COMPLETE - Classification model checked manually!
""")

print("="*80 + "\n")