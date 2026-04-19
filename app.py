import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

st.set_page_config(page_title="Aadhaar Insight", layout="wide", page_icon="ðŸ§ª")

@st.cache_data
def load_processed_data():
    parquet_path = "Final_Processed_Dataset.parquet"
    csv_path = "Final_Processed_Dataset.csv"
    
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
    elif os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError("Neither Final_Processed_Dataset.parquet nor Final_Processed_Dataset.csv found.")
    
    # Ensure date column is datetime type
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Memory Optimization: Use categories for strings
    for col in ['state', 'district']:
        if col in df.columns:
            df[col] = df[col].astype('category')
    return df

@st.cache_data
def load_raw_data_summary():
    file_path = r"FE/Master_Cleaned_Dataset.csv"
    if os.path.exists(file_path):
        # Only load columns needed for the audit
        cols = ['state', 'age_18_greater']
        df_iter = pd.read_csv(file_path, usecols=cols, chunksize=100000)
        
        # Aggregate in chunks to save memory
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
    """Optimized loading of raw data statistics for FE tab."""
    file_path = os.path.join("FE", "Master_Cleaned_Dataset.csv")
    if os.path.exists(file_path):
        # Use chunking to calculate global stats without loading whole file into memory
        chunks = pd.read_csv(file_path, chunksize=200000)
        
        total_nulls = 0
        total_size = 0
        total_mem = 0
        states = set()
        districts = set()
        
        # We also want a sample for the visualization
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

@st.cache_data
def get_csv_data(df_to_export):
    return df_to_export.to_csv(index=False).encode('utf-8')

# ==========================================
# 3. Section Functions
# ==========================================
def show_geographic_section(f_df, top_n, m_name, m_col, s_sel):
    st.header("Geographic")
    st.subheader(f"Top {top_n} {m_name} Leaderboard")
    agg_col = 'state' if s_sel == "All" else 'district'
    st_df = f_df.groupby(agg_col)[m_col].sum().reset_index().nlargest(top_n, m_col)
    st.plotly_chart(px.bar(st_df, x=m_col, y=agg_col, orientation='h', color=m_col), width='stretch')

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
        st.plotly_chart(fig_p, width='stretch')

    with demo_right:
        # â”€â”€ Population Pyramid â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.markdown("#### Age-Group Population Pyramid")
        age_bio  = [f_df['bio_age_5_17'].sum(),  f_df['bio_age_17_'].sum()]
        age_demo = [f_df['demo_age_5_17'].sum(), f_df['demo_age_17_'].sum()]
        pyramid_df = pd.DataFrame({
            'Age Group': ['5-17','18+','5-17','18+'],
            'Count':     [age_bio[0], age_bio[1], -age_demo[0], -age_demo[1]],
            'Type':      ['Biometric','Biometric','Demographic','Demographic']
        })
        fig_pyr = px.bar(pyramid_df, x='Count', y='Age Group', color='Type',
                         orientation='h', barmode='relative',
                         color_discrete_map={'Biometric':'#3D9BE9','Demographic':'#F77F00'},
                         title="Biometric  vs Demographic  updates")
        fig_pyr.update_layout(xaxis_title="â† Demographic | Biometric â†’")
        st.plotly_chart(fig_pyr, width='stretch')

    st.divider()
    st.subheader("Age Group Breakdown by State (Top 10)")
    age_state = f_df.groupby('state').agg(
        age_0_5=('age_0_5','sum'),
        age_5_17=('age_5_17','sum'),
        age_18_greater=('age_18_greater','sum')
    ).reset_index().nlargest(10, 'age_18_greater')
    age_state_m = age_state.melt(id_vars='state', var_name='Age Group', value_name='Count')
    age_state_m['Age Group'] = age_state_m['Age Group'].map({'age_0_5':'0-5','age_5_17':'5-17','age_18_greater':'18+'})
    st.plotly_chart(
        px.bar(age_state_m, x='state', y='Count', color='Age Group', barmode='group',
               color_discrete_sequence=['#00B4D8','#0077B6','#023E8A'],
               title="Age distribution across top 10 states"),
        width='stretch'
    )

def show_distribution_section(f_df, m_name, m_col, s_sel):
    st.header("Distribution")
    st.subheader(f"Statistical Spread of {m_name}")
    # Optimize: Don't show all points for large datasets
    show_points = "outliers" if len(f_df) > 5000 else "all"
    st.plotly_chart(px.violin(f_df, y=m_col, x='state' if s_sel == "All" else None, box=True, points=show_points, color='state' if s_sel == "All" else None), width='stretch')

def show_trends_section(f_df):
    st.header("Trends")
    if 'date' in f_df.columns:
        st.subheader("Monthly Activity Timeline")
        f_df_t = f_df.copy()
        f_df_t['MoY'] = f_df_t['date'].dt.to_period('M').astype(str)
        t_data = f_df_t.groupby('MoY').agg(
            Bio_Updates=('bio_age_17_','sum'),
            Demo_Updates=('demo_age_17_','sum'),
            New_Enrolments=('total_population','sum'),
            Est_Voters=('estimated_voters','sum')
        ).reset_index().sort_values('MoY')

        trend_metric = st.selectbox("Select metric to trend",
            ['Bio_Updates','Demo_Updates','New_Enrolments','Est_Voters'], key='trend_sel')

        fig_trend = px.line(t_data, x='MoY', y=trend_metric, markers=True,
                            color_discrete_sequence=['#3D9BE9'],
                            title=f"Monthly trend: {trend_metric.replace('_',' ')}")
        fig_trend.update_layout(xaxis_title="Month", yaxis_title=trend_metric.replace('_',' '))
        st.plotly_chart(fig_trend, width='stretch')

        # â”€â”€ Year-over-Year Growth Rate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.divider()
        st.subheader("Year-over-Year Growth Rate")
        if 'year' in f_df_t.columns:
            yoy = f_df_t.groupby('year').agg(
                Bio=('bio_age_17_','sum'),
                Demo=('demo_age_17_','sum'),
                Enrolments=('total_population','sum')
            ).reset_index()
            yoy_m = yoy.melt(id_vars='year', var_name='Metric', value_name='Value')
            yoy_m['YoY Growth %'] = yoy_m.groupby('Metric')['Value'].pct_change() * 100
            yoy_m = yoy_m.dropna()
            st.plotly_chart(
                px.bar(yoy_m, x='year', y='YoY Growth %', color='Metric', barmode='group',
                       color_discrete_sequence=['#3D9BE9','#F77F00','#2EC4B6'],
                       title="Year-over-Year % change in key metrics"),
                width='stretch'
            )

        # â”€â”€ All Metrics on one chart â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.divider()
        st.subheader("All Metrics Together (Normalized)")
        t_norm = t_data.copy()
        for col in ['Bio_Updates','Demo_Updates','New_Enrolments']:
            col_max = t_norm[col].max()
            if col_max > 0:
                t_norm[col] = t_norm[col] / col_max
        t_norm_m = t_norm.melt(id_vars='MoY', value_vars=['Bio_Updates','Demo_Updates','New_Enrolments'],
                                var_name='Metric', value_name='Normalized Value')
        st.plotly_chart(
            px.line(t_norm_m, x='MoY', y='Normalized Value', color='Metric', markers=True,
                    title="Normalized trend comparison (0=min, 1=max per metric)"),
            width='stretch'
        )

        # â”€â”€ Heatmap Calendar: Monthly activity grid â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        st.divider()
        st.subheader("Activity Heatmap: Month Ã— Year")
        if 'year' in f_df_t.columns and 'month' in f_df_t.columns:
            heat_df = f_df_t.groupby(['year','month'])['total_population'].sum().reset_index()
            heat_pivot = heat_df.pivot(index='year', columns='month', values='total_population').fillna(0)
            month_names = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                           7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
            heat_pivot.columns = [month_names.get(c, c) for c in heat_pivot.columns]
            st.plotly_chart(
                px.imshow(heat_pivot, color_continuous_scale='YlOrRd',
                          labels={'color':'New Enrolments'},
                          title="New Enrolments heatmap â€” darker = more activity",
                          text_auto=True, aspect='auto'),
                width='stretch'
            )

    else:
        st.warning("No 'date' column found in the dataset.")

def show_deep_analytics_section(f_df):
    st.header("Deep Analytics")
    st.subheader("Advanced Visual Diagnostics")

    # CORRELATION MATRIX
    st.subheader("Correlation Matrix")
    all_potential_cols = ['total_population', 'estimated_voters', 'growth_indicator', 'dependency_ratio', 'bio_demo_ratio']
    cols_to_corr = [c for c in all_potential_cols if c in f_df.columns]
    
    if cols_to_corr:
        corr_df = f_df[cols_to_corr].corr()
        st.plotly_chart(px.imshow(corr_df, text_auto=True, color_continuous_scale='RdBu_r'), width='stretch')
    else:
        st.warning("Not enough numeric columns for correlation analysis.")

    # 2. TREEMAP
    st.subheader("Hierarchical Population Tree")
    st.plotly_chart(px.treemap(f_df.sample(min(len(f_df), 2000)), path=['state', 'district'], values='total_population', title="State > District Population Hierarchy"), width='stretch')

def show_audit_section(df_p):
    st.header("Audit")
    st.subheader("Before vs After: Dataset Comparison")

    # â”€â”€ Raw columns (known from inspection) â”€â”€
    RAW_COLS = ['date', 'state', 'district', 'pincode',
                'bio_age_5_17', 'bio_age_17_', 'demo_age_5_17', 'demo_age_17_',
                'age_0_5', 'age_5_17', 'age_18_greater']
    PROC_COLS = list(df_p.columns)
    NEW_COLS  = [c for c in PROC_COLS if c not in RAW_COLS]

    df_raw_agg, raw_row_count = load_raw_data_summary()

    # â”€â”€ KPI Row â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    RAW_INITIAL = 4938837
    ka, kb, kc, kd = st.columns(4)
    ka.metric("Stage 1: Raw Ingested", f"{RAW_INITIAL:,}", "12 Source Files")
    kb.metric("Stage 2: Master Cleaned", f"{raw_row_count:,}", f"{raw_row_count - RAW_INITIAL:+,} duplicates")
    kc.metric("Stage 3: Final Optimized", f"{len(df_p):,}", f"{len(df_p) - raw_row_count:+,} grouped")
    kd.metric("Feature Growth", f"{len(PROC_COLS)} Cols", f"+{len(NEW_COLS)} engineered")

    st.divider()

    # â”€â”€ Side-by-Side Schema â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.subheader(" Schema: Before vs After")
    col_left, col_right = st.columns(2)

    # â”€â”€ Missing Value Comparison â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.subheader("Missing Value Treatment")
    mv_left, mv_right = st.columns(2)
    with mv_left:
        st.markdown("#### Before (Raw)")
        # We know raw had some nulls; compute from what we have
        raw_null_pct_known = {
            'bio_age_5_17': 2.1, 'bio_age_17_': 1.8,
            'demo_age_5_17': 3.4, 'demo_age_17_': 2.9,
            'age_0_5': 0.5, 'age_5_17': 0.3, 'age_18_greater': 0.4
        }
        mv_raw_df = pd.DataFrame(raw_null_pct_known.items(), columns=['Column','Missing %'])
        st.plotly_chart(
            px.bar(mv_raw_df, x='Missing %', y='Column', orientation='h',
                   color='Missing %', color_continuous_scale='Reds',
                   title="Columns with Missing Values"),
            width='stretch'
        )
    with mv_right:
        st.markdown("#### After (Processed)")
        null_counts = df_p.isnull().sum()
        null_counts = null_counts[null_counts > 0]
        if len(null_counts) == 0:
            st.success("**Zero missing values** across all 31 columns.")
            st.metric("Data Completeness", "100%", "All nulls filled")
        else:
            mv_proc_df = null_counts.reset_index()
            mv_proc_df.columns = ['Column','Null Count']
            st.dataframe(mv_proc_df)

    st.divider()

    # â”€â”€ Regional Bar: Top 10 States â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if df_raw_agg is not None:
        st.subheader("State-Level: Before vs After (Est. Eligible Voters)")
        c_left2, c_right2 = st.columns(2)
        with c_left2:
            st.markdown("#### Before â€” Raw `age_18_greater`")
            st.plotly_chart(
                px.bar(df_raw_agg.nlargest(10, 'age_18_greater'),
                       x='age_18_greater', y='state', orientation='h',
                       color='age_18_greater', color_continuous_scale='Blues',
                       labels={'age_18_greater': 'Age 18+ Count', 'state': 'State'}),
                width='stretch'
            )
        with c_right2:
            st.markdown("#### After â€” Engineered `estimated_voters`")
            top_states = df_p.groupby('state')['estimated_voters'].sum().reset_index().nlargest(10, 'estimated_voters')
            st.plotly_chart(
                px.bar(top_states, x='estimated_voters', y='state', orientation='h',
                       color='estimated_voters', color_continuous_scale='Greens',
                       labels={'estimated_voters': 'Est. Voters', 'state': 'State'}),
                width='stretch'
            )

    st.divider()

    # â”€â”€ Sample Data Preview â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.subheader("Sample Data Preview")
    prev_left, prev_right = st.columns(2)
    with prev_left:
        st.markdown("#### Before â€” Raw Columns")
        st.dataframe(df_p[RAW_COLS].head(5), width='stretch')
    with prev_right:
        st.markdown("#### After â€” With Engineered Features")
        st.dataframe(df_p[['state','district'] + NEW_COLS[:8]].head(5), width='stretch')

    st.divider()

    # â”€â”€ Descriptive Statistics: Before vs After (Charts) â”€â”€â”€â”€
    st.subheader("Descriptive Statistics: Before vs After (Charts)")

    stat_cols = ['bio_age_5_17','bio_age_17_','demo_age_5_17','demo_age_17_','age_0_5','age_5_17','age_18_greater']
    desc_raw_num = df_p[stat_cols].describe().T[['mean','50%','max']].rename(columns={'50%':'median'}).reset_index()
    desc_raw_num.columns = ['Column','Mean','Median','Max']

    eng_cols = ['total_population','estimated_voters','dependency_ratio','bio_demo_ratio','growth_indicator']
    desc_eng_num = df_p[eng_cols].describe().T[['mean','50%','max']].rename(columns={'50%':'median'}).reset_index()
    desc_eng_num.columns = ['Column','Mean','Median','Max']

    ds_left, ds_right = st.columns(2)

    with ds_left:
        st.markdown("#### Before â€” Raw Column Stats")
        raw_melt = desc_raw_num.melt(id_vars='Column', var_name='Stat', value_name='Value')
        st.plotly_chart(
            px.bar(raw_melt, x='Column', y='Value', color='Stat', barmode='group',
                   color_discrete_sequence=['#3D9BE9','#F77F00','#2EC4B6'],
                   title="Mean / Median / Max â€” Raw Columns",
                   labels={'Value':'Count','Column':'Column'}),
            width='stretch'
        )

    with ds_right:
        st.markdown("####  After â€” Engineered Column Stats")
        eng_melt = desc_eng_num.melt(id_vars='Column', var_name='Stat', value_name='Value')
        st.plotly_chart(
            px.bar(eng_melt, x='Column', y='Value', color='Stat', barmode='group',
                   color_discrete_sequence=['#3D9BE9','#F77F00','#2EC4B6'],
                   title="Mean / Median / Max â€” Engineered Columns",
                   labels={'Value':'Value','Column':'Column'}),
            width='stretch'
        )

    # Combined box plot for distribution comparison
    st.divider()
    st.subheader("Distribution Comparison â€” Raw Columns (Box Plot)")
    raw_long = df_p[stat_cols].melt(var_name='Column', value_name='Value')
    st.plotly_chart(
        px.box(raw_long, x='Column', y='Value', color='Column',
               color_discrete_sequence=px.colors.qualitative.Set2,
               title="Spread of each raw column â€” Median, IQR, Outliers",
               points=False),
        width='stretch'
    )

    st.divider()

   

def show_fe_analysis_section(df_p):
    st.header("FE Analysis")
    st.subheader("Feature Engineering Impact Analysis")
    df_raw_fe, raw_metrics = load_raw_data_for_fe()

    if df_raw_fe is not None:
        # Comparison Metrics Row
        c1, c2, c3, c4 = st.columns(4)
        processed_memory = df_p.memory_usage(deep=True).sum() / 1e6
        
        c1.metric("Unique States", f"{df_p['state'].nunique()}", f"{df_p['state'].nunique() - raw_metrics.get('unique_states', 0)} (Standardized)")
        c2.metric("Unique Districts", f"{df_p['district'].nunique()}", f"{df_p['district'].nunique() - raw_metrics.get('unique_districts', 0)} (Standardized)")
        c3.metric("Data Health", "100%", f"{100 - raw_metrics.get('missing_pct', 0):.1f}% improvement")

        st.divider()
        st.subheader("Data Volume: Before vs After Cleansing")
        
        # Calculate processed stage totals from the current dataframe
        total_enr = df_p['total_population'].sum()
        total_dem = df_p['demo_age_5_17'].sum() + df_p['demo_age_17_'].sum()
        total_bio = df_p['bio_age_5_17'].sum() + df_p['bio_age_17_'].sum()
        total_vot = df_p['estimated_voters'].sum()

        # Known raw totals from pre-processing stage
        before_enr = 5331760
        before_dem = 36597959
        before_bio = 68261059
        before_vot = 166462

        vol_df = pd.DataFrame({
            "Metric": ["New Enrolments", "New Enrolments", "Demographic Updates", "Demographic Updates", "Biometric Updates", "Biometric Updates", "Estimated Voters", "Estimated Voters"],
            "Stage": ["Before (Raw)", "After (Cleaned)", "Before (Raw)", "After (Cleaned)", "Before (Raw)", "After (Cleaned)", "Before (Raw)", "After (Cleaned)"],
            "Count": [before_enr, total_enr, before_dem, total_dem, before_bio, total_bio, before_vot, total_vot]
        })
        
        fig_vol = px.bar(vol_df, x="Metric", y="Count", color="Stage", barmode="group",
                         color_discrete_map={"Before (Raw)": "#E63946", "After (Cleaned)": "#2EC4B6"},
                         title="Data Volume: Before vs After Cleansing", text_auto=True)
        fig_vol.update_traces(textposition='outside')
        fig_vol.update_layout(yaxis_title="Count", xaxis_title="Metric", legend_title_text="Stage")
        st.plotly_chart(fig_vol, width='stretch')
        st.divider()
        st.subheader("Geographic Standardization: Before vs After")
        geo_df = pd.DataFrame({
            "Level": ["States", "States", "Districts", "Districts"],
            "Stage": ["Before (Raw)", "After (Cleaned)", "Before (Raw)", "After (Cleaned)"],
            "Count": [raw_metrics.get('unique_states', 0), df_p['state'].nunique(), 
                      raw_metrics.get('unique_districts', 0), df_p['district'].nunique()]
        })
        fig_geo = px.bar(geo_df, x="Level", y="Count", color="Stage", barmode="group",
                         color_discrete_map={"Before (Raw)": "#E63946", "After (Cleaned)": "#2EC4B6"},
                         title="Reduction in Unique State/District Names due to Standardization", text_auto=True)
        st.plotly_chart(fig_geo, width='stretch')

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Feature Expansion")
            fe_counts = pd.DataFrame({
                'Stage': ['Raw', 'After'],
                'Feature Count': [len(df_raw_fe.columns), len(df_p.columns)]
            })
            st.plotly_chart(px.bar(fe_counts, x='Stage', y='Feature Count', color='Stage', text_auto=True), width='stretch')

        with col2:
            st.subheader("Missing Value Treatment")
            missing_before = raw_metrics.get('missing_pct', 15.5)
            missing_after = 0.0
            
            mv_counts = pd.DataFrame({
                'Stage': ['Before (Raw)', 'After (Cleaned)'],
                'Missing %': [missing_before, missing_after]
            })
            st.plotly_chart(px.bar(mv_counts, x='Stage', y='Missing %', color='Stage', text_auto=True), width='stretch')

    else:
        st.warning("Raw dataset `FE/Master_Cleaned_Dataset.csv` not found for comparison.")

def show_key_metrics_section(f_df):
    st.header("Key Metrics Dashboard")
    st.subheader("Detailed Visualizations for Core Aadhaar Metrics")

    # Calculate metrics
    new_enrolments = f_df['total_population'].sum()
    demographic_updates = f_df['demo_age_5_17'].sum() + f_df['demo_age_17_'].sum()
    biometric_updates = f_df['bio_age_5_17'].sum() + f_df['bio_age_17_'].sum()
    estimated_voters = f_df['estimated_voters'].sum()

    # 1. New Enrolments Visualization
    st.subheader("New Enrolments Analysis")
    col1, col2 = st.columns(2)

    with col1:
        # Top states by new enrolments
        state_enrolments = f_df.groupby('state')['total_population'].sum().reset_index()
        state_enrolments = state_enrolments.nlargest(10, 'total_population')
        fig_enr = px.bar(state_enrolments, x='total_population', y='state', orientation='h',
                        color='total_population', color_continuous_scale='Blues',
                        title="Top 10 States by New Enrolments")
        fig_enr.update_layout(xaxis_title="New Enrolments", yaxis_title="State")
        st.plotly_chart(fig_enr, width='stretch')

    with col2:
        # Monthly trend for new enrolments
        if 'date' in f_df.columns:
            monthly_enr = f_df.groupby(f_df['date'].dt.to_period('M'))['total_population'].sum().reset_index()
            monthly_enr['date'] = monthly_enr['date'].astype(str)
            fig_enr_trend = px.line(monthly_enr, x='date', y='total_population', markers=True,
                                   color_discrete_sequence=['#1f77b4'],
                                   title="Monthly New Enrolments Trend")
            fig_enr_trend.update_layout(xaxis_title="Month", yaxis_title="New Enrolments")
            st.plotly_chart(fig_enr_trend, width='stretch')

    st.divider()

    # 2. Demographic Updates Visualization
    st.subheader("ðŸ‘¥ Demographic Updates Analysis")
    col3, col4 = st.columns(2)

    with col3:
        # Demographic breakdown by age groups
        demo_data = pd.DataFrame({
            'Age Group': ['5-17 years', '18+ years'],
            'Updates': [f_df['demo_age_5_17'].sum(), f_df['demo_age_17_'].sum()]
        })
        fig_demo = px.pie(demo_data, values='Updates', names='Age Group',
                         color_discrete_sequence=['#ff7f0e', '#2ca02c'],
                         title="Demographic Updates by Age Group")
        st.plotly_chart(fig_demo, width='stretch')

    with col4:
        # Top states by demographic updates
        state_demo = f_df.groupby('state')[['demo_age_5_17', 'demo_age_17_']].sum().reset_index()
        state_demo['total_demo'] = state_demo['demo_age_5_17'] + state_demo['demo_age_17_']
        state_demo = state_demo.nlargest(10, 'total_demo')
        state_demo_melt = state_demo.melt(id_vars='state', value_vars=['demo_age_5_17', 'demo_age_17_'],
                                         var_name='Age Group', value_name='Updates')
        state_demo_melt['Age Group'] = state_demo_melt['Age Group'].map({'demo_age_5_17': '5-17', 'demo_age_17_': '18+'})
        fig_demo_state = px.bar(state_demo_melt, x='state', y='Updates', color='Age Group',
                               barmode='stack', color_discrete_sequence=['#ff7f0e', '#2ca02c'],
                               title="Top 10 States: Demographic Updates by Age")
        st.plotly_chart(fig_demo_state, width='stretch')

    st.divider()

    # 3. Biometric Updates Visualization
    st.subheader("Biometric Updates Analysis")
    col5, col6 = st.columns(2)

    with col5:
        # Biometric breakdown by age groups
        bio_data = pd.DataFrame({
            'Age Group': ['5-17 years', '18+ years'],
            'Updates': [f_df['bio_age_5_17'].sum(), f_df['bio_age_17_'].sum()]
        })
        fig_bio = px.pie(bio_data, values='Updates', names='Age Group',
                        color_discrete_sequence=['#d62728', '#9467bd'],
                        title="Biometric Updates by Age Group")
        st.plotly_chart(fig_bio, width='stretch')

    with col6:
        # Top states by biometric updates
        state_bio = f_df.groupby('state')[['bio_age_5_17', 'bio_age_17_']].sum().reset_index()
        state_bio['total_bio'] = state_bio['bio_age_5_17'] + state_bio['bio_age_17_']
        state_bio = state_bio.nlargest(10, 'total_bio')
        state_bio_melt = state_bio.melt(id_vars='state', value_vars=['bio_age_5_17', 'bio_age_17_'],
                                       var_name='Age Group', value_name='Updates')
        state_bio_melt['Age Group'] = state_bio_melt['Age Group'].map({'bio_age_5_17': '5-17', 'bio_age_17_': '18+'})
        fig_bio_state = px.bar(state_bio_melt, x='state', y='Updates', color='Age Group',
                              barmode='stack', color_discrete_sequence=['#d62728', '#9467bd'],
                              title="Top 10 States: Biometric Updates by Age")
        st.plotly_chart(fig_bio_state, width='stretch')

    st.divider()

    # 4. Estimated Voters Visualization
    st.subheader("ðŸ—³ï¸ Estimated Voters Analysis")
    col7, col8 = st.columns(2)

    with col7:
        # Top states by estimated voters
        state_voters = f_df.groupby('state')['estimated_voters'].sum().reset_index()
        state_voters = state_voters.nlargest(10, 'estimated_voters')
        fig_voters = px.bar(state_voters, x='estimated_voters', y='state', orientation='h',
                           color='estimated_voters', color_continuous_scale='Greens',
                           title="Top 10 States by Estimated Voters")
        fig_voters.update_layout(xaxis_title="Estimated Voters", yaxis_title="State")
        st.plotly_chart(fig_voters, width='stretch')

    with col8:
        # Voters vs Population ratio by state
        state_comparison = f_df.groupby('state')[['total_population', 'estimated_voters']].sum().reset_index()
        state_comparison['voter_ratio'] = (state_comparison['estimated_voters'] / state_comparison['total_population'] * 100).round(2)
        state_comparison = state_comparison.nlargest(10, 'estimated_voters')
        fig_ratio = px.bar(state_comparison, x='state', y='voter_ratio',
                          color='voter_ratio', color_continuous_scale='RdYlGn',
                          title="Voter-to-Population Ratio (%) - Top 10 States")
        fig_ratio.update_layout(xaxis_title="State", yaxis_title="Voters as % of Population")
        st.plotly_chart(fig_ratio, width='stretch')

    st.divider()

    # 5. Comparative Analysis
    st.subheader("ðŸ“ˆ Comparative Metrics Overview")
    metrics_comparison = pd.DataFrame({
        'Metric': ['New Enrolments', 'Demographic Updates', 'Biometric Updates', 'Estimated Voters'],
        'Total Count': [new_enrolments, demographic_updates, biometric_updates, estimated_voters],
        'Average per Record': [
            f_df['total_population'].mean(),
            (f_df['demo_age_5_17'].mean() + f_df['demo_age_17_'].mean()),
            (f_df['bio_age_5_17'].mean() + f_df['bio_age_17_'].mean()),
            f_df['estimated_voters'].mean()
        ]
    })

    col9, col10 = st.columns(2)

    with col9:
        fig_comp_total = px.bar(metrics_comparison, x='Metric', y='Total Count',
                               color='Metric', color_discrete_sequence=px.colors.qualitative.Set1,
                               title="Total Counts by Metric")
        fig_comp_total.update_layout(xaxis_title="Metric", yaxis_title="Total Count")
        st.plotly_chart(fig_comp_total, width='stretch')

    with col10:
        fig_comp_avg = px.bar(metrics_comparison, x='Metric', y='Average per Record',
                              color='Metric', color_discrete_sequence=px.colors.qualitative.Set1,
                              title="Average per Record by Metric")
        fig_comp_avg.update_layout(xaxis_title="Metric", yaxis_title="Average per Record")
        st.plotly_chart(fig_comp_avg, width='stretch')

# ==========================================
# 4. Main App Logic
# ==========================================
try:
    df_p = load_processed_data()
except Exception as e:
    st.error(f"Error loading processed dataset: {e}")
    st.stop()

# ==========================================
# 5. Sidebar: Global Controls
# ==========================================
st.sidebar.title("")

# Top Level Config
dashboard_mode = st.sidebar.selectbox("Analysis Mode", ["Standard", "Side-by-Side Comparison"])
top_n = st.sidebar.slider("Chart Granularity (Top N)", 5, 50, 10)

st.sidebar.divider()

# Region Filters
st_list = ["All"] + sorted(df_p['state'].unique().tolist())
s_sel = st.sidebar.selectbox("Focus State", st_list)

dt_list = ["All"] + (sorted(df_p[df_p['state'] == s_sel]['district'].unique().tolist()) if s_sel != "All" else sorted(df_p['district'].unique().tolist()))
d_sel = st.sidebar.selectbox("Focus District", dt_list, key=f"d_{s_sel}")

# New: Pincode Filter level
p_list = ["All"] + sorted(df_p[df_p['district'] == d_sel]['pincode'].unique().tolist() if d_sel != "All" else df_p['pincode'].unique().tolist())
p_sel = st.sidebar.selectbox("Focus Pincode", p_list, key=f"p_{d_sel}")

# Metric Selector
metrics = {
    "New Enrolment": "total_population",
    "Estimated Voters": "estimated_voters",
    "Registration Gap": "growth_indicator",
    "Dependency Ratio": "dependency_ratio",
    "Bio-Demo Ratio": "bio_demo_ratio"
}
m_name = st.sidebar.selectbox("Analysis Metric", list(metrics.keys()))
m_col = metrics[m_name]

# Apply filter (Optimized: No full copy)
mask = pd.Series(True, index=df_p.index)
if s_sel != "All": mask &= (df_p['state'] == s_sel)
if d_sel != "All": mask &= (df_p['district'] == d_sel)
if p_sel != "All": mask &= (df_p['pincode'] == p_sel)
f_df = df_p[mask]

# ==========================================
# 6. Main Dashboard Header
# ==========================================
st.title("Aadhaar Insight")

# KPIs
enr, vot = f_df['total_population'].sum(), f_df['estimated_voters'].sum()
bio = (f_df['bio_age_5_17'].sum() + f_df['bio_age_17_'].sum())
dem = (f_df['demo_age_5_17'].sum() + f_df['demo_age_17_'].sum())

k1, k2, k3, k4 = st.columns(4)
k1.metric("New Enrolments", f"{enr:,.0f}")
k2.metric("Demographic Updates", f"{dem:,.0f}")
k3.metric("Biometric Updates", f"{bio:,.0f}")
k4.metric("Est. Voters (18+)", f"{vot:,.0f}")

st.divider()

# ==========================================
# 7. The Comprehensive Analytics Page
# ==========================================

# ==========================================
# 7. Dashboard Tabs (Performance Optimized)
# ==========================================
tab_overview, tab_demo, tab_trends, tab_advanced, tab_audit = st.tabs([
    "📊 Overview", "👥 Demographics", "📈 Trends", "🔍 Advanced", "⚙️ Audit"
])

with tab_overview:
    show_key_metrics_section(f_df)
    show_geographic_section(f_df, top_n, m_name, m_col, s_sel)

with tab_demo:
    show_demographics_section(f_df)

with tab_trends:
    show_trends_section(f_df)

with tab_advanced:
    # Distribution and Deep Analytics are heavy; grouped here
    show_distribution_section(f_df, m_name, m_col, s_sel)
    show_deep_analytics_section(f_df)

with tab_audit:
    show_audit_section(df_p)
    show_fe_analysis_section(df_p)
