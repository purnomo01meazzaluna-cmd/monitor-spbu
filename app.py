import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU 4150201",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("Tepat Guna")
st.markdown("**SPBU 4150201 | Semarang, Jawa Tengah**")
st.markdown("---")

# Sidebar / Upload Section
st.sidebar.header("Unggah Data Transaksi")
uploaded_file = st.sidebar.file_uploader("Upload file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])

# Main Application Logic
if uploaded_file is not None:
    try:
        # Membaca file Excel secara aman dengan openpyxl
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.success("File berhasil dimuat!")
        
        # Filter Tanggal & Ringkasan Transaksi
        st.subheader(f"Ikhtisar Harian Penyaluran BBM Subsidi ({datetime.now().strftime('%Y-%m-%d')})")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Volume Terjual", "49 Liter")
        with col2:
            st.metric("Transaksi Pertalite", "49 Liter")
        with col3:
            st.metric("Transaksi Biosolar", "0 Liter")
        with col4:
            st.metric("Kendaraan Terlayani", "1 Unit")
            
        st.markdown("---")
        st.subheader("Grafik Tren Penyaluran per Jam")
        
        # Placeholder grafik tren
        chart_data = pd.DataFrame(
            np.random.randn(20, 2),
            columns=['Pertalite', 'Biosolar']
        )
        st.line_chart(chart_data)

    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
else:
    st.info("Silakan unggah file transaksi Excel (.xlsx) atau CSV melalui panel di sebelah kiri.")
