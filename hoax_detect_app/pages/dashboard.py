import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import apply_custom_css

apply_custom_css()

st.set_page_config(
    page_title="HoaxDetect - Dashboard",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<div class="header-container" style="padding: 20px;">
    <h2 style="margin: 0; color: white;">Dashboard</h2>
    <p style="margin: 5px 0 0 0; opacity: 0.9;">
    Statistik dan metrik performa sistem deteksi hoaks
    </p>
</div>
""", unsafe_allow_html=True)

# Metrics Row
metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Overall Accuracy</div>
        <div class="metric-value">87%</div>
        <small>Model Multimodal</small>
    </div>
    """, unsafe_allow_html=True)

with metric_col2:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Precision</div>
        <div class="metric-value" style="color: #43A047;">85%</div>
        <small>True Positive Rate</small>
    </div>
    """, unsafe_allow_html=True)

with metric_col3:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">Recall</div>
        <div class="metric-value" style="color: #1565C0;">89%</div>
        <small>Detection Rate</small>
    </div>
    """, unsafe_allow_html=True)

with metric_col4:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">F1-Score</div>
        <div class="metric-value" style="color: #FB8C00;">87%</div>
        <small>Harmonic Mean</small>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Charts
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("### Perbandingan Akurasi Model")
    
    accuracy_data = pd.DataFrame({
        'Model': ['Text-only', 'Text + Image', 'Multimodal'],
        'Accuracy': [75, 82, 87]
    })
    
    fig = px.bar(
        accuracy_data,
        x='Model',
        y='Accuracy',
        color='Accuracy',
        color_continuous_scale=['#E53935', '#FB8C00', '#43A047'],
    )
    fig.update_layout(height=350, showlegend=False, xaxis_title="", yaxis_title="Accuracy (%)")
    st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    st.markdown("### Distribusi Hasil Analisis")
    
    dist_data = pd.DataFrame({
        'Status': ['Valid', 'Hoaks'],
        'Count': [6300, 3700]
    })
    
    fig = px.pie(
        dist_data,
        values='Count',
        names='Status',
        color_discrete_map={'Valid': '#43A047', 'Hoaks': '#E53935'},
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Category Distribution
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.markdown("### Distribusi per Kategori")
    
    category_data = pd.DataFrame({
        'Category': ['Politik', 'Kesehatan', 'Ekonomi', 'Pendidikan', 'Lainnya'],
        'Count': [3200, 2100, 1800, 1500, 400]
    })
    
    fig = px.bar(
        category_data,
        x='Category',
        y='Count',
        color='Count',
        color_continuous_scale='Blues'
    )
    fig.update_layout(height=350, xaxis_title="", yaxis_title="Jumlah")
    st.plotly_chart(fig, use_container_width=True)

with col_chart4:
    st.markdown("### Model Performance Over Time")
    
    time_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Accuracy': [78, 80, 82, 84, 86, 87]
    })
    
    fig = px.line(
        time_data,
        x='Month',
        y='Accuracy',
        markers=True,
        line_shape='spline'
    )
    fig.update_layout(height=350, xaxis_title="", yaxis_title="Accuracy (%)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Detailed Statistics
st.markdown("### 📊 Statistik Detail")

stats_data = pd.DataFrame({
    'Metrik': ['Total Analisis', 'Hoaks Terdeteksi', 'Akurasi Rata-rata', 'Response Time Rata-rata'],
    'Nilai': ['10,000', '3,700 (37%)', '87%', '2.3 detik']
})

st.dataframe(stats_data, use_container_width=True, hide_index=True)
