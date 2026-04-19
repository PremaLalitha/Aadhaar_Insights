import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

st.set_page_config(page_title="Aadhaar Insight", layout="wide", page_icon="🧪")

@st.cache_data
def load_processed_data():
    file_path = "Final_Processed_Dataset.parquet"
    if os.path.exists(file_path):
        df = pd.read_parquet(file_path)
    else:
        # Fallback to CSV if parquet doesn't exist locally
        df = pd.read_csv("Final_Processed_Dataset.csv")
        df.to_parquet(file_path)
    
    # 1. Memory Optimization: Downcast numeric types
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')
    for col in df.select_dtypes(include=['int64']).columns:
        if df[col].max() < 32767 and df[col].min() > -32768:
            df[col] = df[col].astype('int16')
        else:
            df[col] = df[col].astype('int32')
            
    # 2. Date parsing (once in cache)
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # 3. Categorical optimization for strings
    for col in ['state', 'district']:
        if col in df.columns:
            df[col] = df[col].astype('category')
            
    return df

@st.cache_data
def load_raw_data_summary():
    file_path = r"FE/Master_Cleaned_Dataset.csv"
    if os.path.exists(file_path):
        cols = ['state', 'age_18_greater']
        df_iter = pd.read_csv(file_path, usecols=cols, chunksize=100000)
        partial_results = []
        total_rows = 0
        for chunk in df_iter:
            total_rows += len(chunk)
            chunk['age_18_greater'] = pd.to_numeric(chunk['age_18_greater'], errors='coerce').fillna(0)
            partial_results.append(chunk.groupby('state')['age_18_greater'].sum())
        agg_raw = pd.concat(partial_results).groupby(level=0).sum().reset_index()
        return agg_raw, total_rows
    return None, 0

@st.cache_data
def load_raw_data_for_fe():
    file_path = os.path.join("FE", "Master_Cleaned_Dataset.csv")
    if os.path.exists(file_path):
        chunks = pd.read_csv(file_path, chunksize=200000)
        total_nulls = 0
        total_size = 0
        total_mem = 0
        states = set()
        districts = set()
        sample_df = None
        for chunk in chunks:
            total_nulls += chunk.isnull().sum().sum()
            total_size += chunk.size
            total_mem += chunk.memory_usage(deep=True).sum()
            if 'state' in chunk.columns: states.update(chunk['state'].dropna().unique())
            if 'district' in chunk.columns: districts.update(chunk['district'].dropna().unique())
            if sample_df is None:
                sample_df = chunk.sample(min(len(chunk), 5000))
        raw_stats = {
            'unique_states': len(states),
            'unique_districts': len(districts),
            'memory_mb': total_mem / 1e6,
            'missing_pct': (total_nulls / total_size) * 100 if total_size > 0 else 0
        }
        return sample_df, raw_stats
    return None, {}

def show_geographic_section(f_df, top_n, m_name, m_col, s_sel):
    st.header("Geographic")
    st.subheader(f"Top {top_n} {m_name} Leaderboard")
    agg_col = 'state' if s_sel == "All" else 'district'
    st_df = f_df.groupby(agg_col)[m_col].sum().reset_index().nlargest(top_n, m_col)
    st.plotly_chart(px.bar(st_df, x=m_col, y=agg_col, orientation='h', color=m_col), use_container_width=True)

def show_demographics_section(f_df):
    st.header("Demographics")
    st.subheader("Population Profile")
    demo_left, demo_right = st.columns(2)
    with demo_left:
        fig_p = px.pie(
            pd.DataFrame({'Group':['0-5','5-17','18+'],
                          'Count':[f_df['age_0_5'].sum(), f_df['age_5_17'].sum(), f_df['age_18_greater'].sum()]}),
            values='Count', names='Group', hole=0.5,
            color_discrete_sequence=px.colors.sequential.Teal
        )
        fig_p.update_layout(title="Age Group Share")
        st.plotly_chart(fig_p, use_container_width=True)
    with demo_right:
        st.markdown("#### Age-Group Population Pyramid")
        age_bio  = [f_df['bio_age_5_17'].sum(),  f_df['bio_age_17_'].sum()]
        age_demo = [f_df['demo_age_5_17'].sum(), f_df['demo_age_17_'].sum()]
        pyramid_df = pd.DataFrame({
            'Age Group': ['5-17','18+','5-17','18+'],
            'Count':     [age_bio[0], age_bio[1], -age_demo[0], -age_demo[1]],
            'Type':      ['Biometric','Biometric','Demographic','Demographic']
        })
        fig_pyr = px.bar(pyramid_df, x='Count', y='Age Group', color='Type', orientation='h', barmode='relative',
                         color_discrete_map={'Biometric':'#3D9BE9','Demographic':'#F77F00'},
                         title="Biometric vs Demographic Updates")
        fig_pyr.update_layout(xaxis_title="← Demographic | Biometric →")
        st.plotly_chart(fig_pyr, use_container_width=True)

def show_distribution_section(f_df, m_name, m_col, s_sel):
    st.header("Distribution")
    st.subheader(f"Statistical Spread of {m_name}")
    plot_df = f_df
    if len(f_df) > 50000:
        plot_df = f_df.sample(50000, random_state=42)
        st.info("💡 Showing representative sample of 50,000 for performance.")
    show_points = "outliers" if len(plot_df) > 5000 else "all"
    fig = px.violin(plot_df, y=m_col, x='state' if s_sel == "All" else None, box=True, points=show_points, color='state' if s_sel == "All" else None)
    st.plotly_chart(fig, use_container_width=True)

def show_trends_section(f_df):
    st.header("Trends")
    if 'date' in f_df.columns:
        f_df_t = f_df.copy()
        f_df_t['MoY'] = f_df_t['date'].dt.to_period('M').astype(str)
        t_data = f_df_t.groupby('MoY').agg(
            Bio_Updates=('bio_age_17_','sum'),
            Demo_Updates=('demo_age_17_','sum'),
            New_Enrolments=('total_population','sum')
        ).reset_index().sort_values('MoY')
        trend_metric = st.selectbox("Select metric", ['Bio_Updates','Demo_Updates','New_Enrolments'])
        st.plotly_chart(px.line(t_data, x='MoY', y=trend_metric, markers=True, title=f"Monthly Trend"), use_container_width=True)
    else:
        st.warning("No trend data available.")

def show_deep_analytics_section(f_df):
    st.header("Deep Analytics")
    cols_to_corr = ['total_population', 'estimated_voters', 'dependency_ratio', 'bio_demo_ratio']
    corr_df = f_df[cols_to_corr].corr()
    st.plotly_chart(px.imshow(corr_df, text_auto=True), use_container_width=True)

def show_audit_section(df_p):
    st.header("Data Audit")
    raw_agg, raw_rows = load_raw_data_summary()
    k1, k2, k3 = st.columns(3)
    k1.metric("Raw Rows", f"{raw_rows:,}")
    k2.metric("Final Rows", f"{len(df_p):,}")
    k3.metric("Cleaning Efficiency", f"{100-(len(df_p)/raw_rows*100):.1f}% reduction")

def show_fe_analysis_section(df_p):
    st.header("Feature Engineering Analysis")
    sample_df, raw_stats = load_raw_data_for_fe()
    if raw_stats:
        st.write(f"Raw Features: {raw_stats.get('memory_mb', 0):.1f} MB in RAM")

def show_ml_performance_section():
    st.header("🤖 Machine Learning Performance")
    m1, m2, m3 = st.columns(3)
    m1.metric("Best Model", "Random Forest")
    m2.metric("Accuracy", "100%")
    m3.metric("Data Size", "1M Records")
    perf_plot = "voter_eligibility_model_performance.png"
    if os.path.exists(perf_plot):
        st.image(perf_plot, use_container_width=True)

def show_key_metrics_section(f_df):
    st.header("Key Highlights")
    st.subheader("Summary Charts")
    state_enr = f_df.groupby('state')['total_population'].sum().reset_index().nlargest(10, 'total_population')
    st.plotly_chart(px.bar(state_enr, x='total_population', y='state', orientation='h', title="Top 10 States"), use_container_width=True)

# Main Execution Logic
try:
    df_p = load_processed_data()
except Exception as e:
    st.error(f"Error loading system: {e}")
    st.stop()

# Sidebar
st.sidebar.title("Aadhaar Filter")
s_sel = st.sidebar.selectbox("State", ["All"] + sorted(df_p['state'].unique().tolist()))
f_df = df_p if s_sel == "All" else df_p[df_p['state'] == s_sel]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "🤖 Machine Learning", "🔍 Audit", "⚙️ FE"])

with tab1:
    show_key_metrics_section(f_df)
    show_geographic_section(f_df, 10, "Population", "total_population", s_sel)
    show_demographics_section(f_df)
    show_distribution_section(f_df, "Population", "total_population", s_sel)
    show_trends_section(f_df)

with tab2:
    show_ml_performance_section()

with tab3:
    show_audit_section(df_p)

with tab4:
    show_fe_analysis_section(df_p)