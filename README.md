# Aadhaar Pro Intelligence: Advanced Data Analytics Dashboard

An automated intelligence platform designed to transform fragmented Aadhaar registration records into actionable geographic and demographic insights.

## 🚀 Key Features
- **Multi-Level Data Merging**: Hierarchical integration of Enrolment, Biometric, and Demographic datasets.
- **Data Pipeline Audit**: Verified tracking of **4.9 Million+ rows** from raw ingestion to final optimized output.
- **Health Assessment (A-F Grading)**: Automated audit system based on Bio-Demo registration ratios.
- **Geographic Intelligence**: Real-time State and District-level leaderboards.
- **Electoral Forecasting**: Predicted eligible voter bases across all districts in India.
- **Performance Optimized**: Final dataset consolidated into **~994k strategic records**.

## ⚙️ Setup & Deployment
1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Aadhaar_Insight
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Dashboard**:
   ```bash
   streamlit run app.py
   ```

## 📂 Project Structure
- `app.py`: Main Streamlit dashboard code (Optimized).
- `dataset.ipynb`: Data Cleaning & Standardization pipeline.
- `Master_Cleaned_Dataset.csv`: Unified dataset after deduplication (**2,330,468 records**).
- `Final_Processed_Dataset.csv`: The optimized, engineered dataset (**994,402 records**).
- `requirements.txt`: Python dependencies.

---

## 📊 Data Pipeline Audit (Verified Counts)
| Stage | Description | Row Count |
| :--- | :--- | :--- |
| **Stage 1: Raw Ingestion** | 12 Source Files (Enrolment, Bio, Demo) | **4,938,837** |
| **Stage 2: Master Cleaned** | After Deduplication & Merging | **2,330,468** |
| **Stage 3: Final Optimized** | After FE & Grouping (Main Dashboard) | **994,402** |

---

### 📊 **Total Human Activity (Final Dataset)**
- **Total Enrolments Happened:** **2,622,180**
- **Total Demographic Updates Happened:** **23,662,875**
- **Total Biometric Updates Happened:** **54,811,336**

## 📊 Technical Stack
- **Python 3.10**
- **Pandas & NumPy** (Data processing)
- **Plotly Express** (Interactive Viz)
- **Streamlit** (Web Framework)

---
Developed by [Your Name] | Aadhaar Insights Project
