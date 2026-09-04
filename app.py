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
        # Membaca file berdasarkan formatnya secara aman
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Validasi kolom dasar
        st.success("File berhasil dimuat!")
        
        # Contoh pemrosesan tanggal & filter (disesuaikan dengan struktur data Anda)
        # Pastikan kolom tanggal terdeteksi dengan benar di sini
        st.write("Preview Data:", df_raw.head())
        
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
else:
    st.info("Silakan unggah file transaksi Excel (.xlsx) atau CSV melalui panel di sebelah kiri untuk mulai menganalisis data.")
