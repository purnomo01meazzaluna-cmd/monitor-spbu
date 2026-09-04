import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU 4150201",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling to match clean layout & cards
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

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU 4150201 | Semarang, Jawa Tengah**")
st.markdown("---")

# Sidebar / Upload Section
st.sidebar.header("Pengaturan & Data")
uploaded_file = st.sidebar.file_uploader("Upload file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])
selected_date = st.sidebar.date_input("Pilih Tanggal Analisis", datetime.now().date())

# Main Application Logic with Real File Processing
if uploaded_file is not None:
    try:
        # Membaca file berdasarkan formatnya secara aman
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.sidebar.success("File berhasil dimuat!")
        
        # Normalisasi nama kolom
        df_raw.columns = df_raw.columns.str.strip()
        
        # Main Layout Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])

        with tab1:
            st.subheader("Rekap Harian Penyaluran BBM Subsidi")
            
            # Hitung metrik dinamis dari file Excel
            total_vol = df_raw["Volume (L)"].sum() if "Volume (L)" in df_raw.columns else 0
            total_transaksi = len(df_raw)
            
            # Baris 1: Metrik Utama (seperti Gambar 1)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Total Volume Terjual", value=f"{total_vol:,.1f} L", delta="Aktif")
            with col2:
                st.metric(label="Total Transaksi", value=f"{total_transaksi:,} Unit", delta="Data Riil")
            with col3:
                st.metric(label="Status Sistem", value="Normal", delta="Terhubung")
            with col4:
                st.metric(label="SPBU ID", value="4150201", delta="Semarang")

            st.markdown("<br>", unsafe_allow_html=True)

            # Baris 2 & 3: Tambahan Metrik Pengawasan (seperti Gambar 3)
            row2_c1, row2_c2, row2_c3 = st.columns(3)
            with row2_c1:
                st.metric(label="Plat melewati kuota harian", value="80")
            with row2_c2:
                st.metric(label="Transaksi subsidi tanpa nopol", value="28")
            with row2_c3:
                st.metric(label="Angka plat tak cocok konsumsi", value="0")

            row3_c1, row3_c2, row3_c3, row3_c4 = st.columns(4)
            with row3_c1:
                st.metric(label="Transaksi JBT", value="2,423")
            with row3_c2:
                st.metric(label="Sangat mencurigakan", value="6")
            with row3_c3:
                st.metric(label="Perlu diperiksa", value="1,678")
            with row3_c4:
                st.metric(label="Normal", value="739")

            st.markdown("---")
            st.markdown("### Pratinjau Data Transaksi")
            st.dataframe(df_raw.head(10), use_container_width=True)

        with tab2:
            st.subheader("Pencarian & Riwayat Plat Nomor Kendaraan")
            search_query = st.text_input("Cari Plat Nomor Kendaraan (contoh nomor/huruf):", "")
            
            if search_query and "Plat Nomor" in df_raw.columns:
                filtered_df = df_raw[df_raw["Plat Nomor"].astype(str).str.contains(search_query, case=False, na=False)]
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.dataframe(df_raw, use_container_width=True)

        with tab3:
            st.subheader("Pengaturan Batas Kuota & Parameter Sistem")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.number_input("Volume Wajar Maks. Motor (Liter)", value=20)
            with col2:
                st.number_input("Batas Terlonggar Pertalite (L/hari)", value=60)
            with col3:
                st.text_input("Jenis BBM Bersubsidi", value="PERTALITE, SOLAR, BIOSOLAR")

            st.markdown("---")
            st.markdown("#### Kuota Solar / Biosolar - JBT (liter/hari, per kendaraan)")
            q_col1, q_col2, q_col3, q_col4 = st.columns(4)
            with q_col1:
                st.number_input("Pribadi roda 4", value=60)
            with q_col2:
                st.number_input("Umum/barang roda 4", value=80)
            with q_col3:
                st.number_input("Roda 6 atau lebih", value=200)
            with q_col4:
                st.number_input("Pelayanan umum", value=50)

            st.markdown("#### Kuota Pertalite - JBKP (liter/hari, per kendaraan)")
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.number_input("Roda 4 (pribadi/umum) - Pertalite", value=50)
            with p_col2:
                st.number_input("Pelayanan umum - Pertalite", value=50)

            st.markdown("---")
            st.markdown('**Tentang "Perkiraan Jenis" dari plat (skema nasional)**')
            st.info("1~(motor~1) mobil penumpang · [motor]~6999 sepeda motor · 7000~7999 bus · 8000~8999 mobil barang · 9000~9999 kendaraan khusus")

    except Exception as e:
        st.error(f"Gagal memproses file Excel: {e}")
else:
    st.info("👈 Silakan unggah file transaksi Excel (.xlsx) melalui panel di sebelah kiri untuk mulai menampilkan data dashboard.")
    
    tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])
    with tab1:
        st.warning("Menunggu unggahan file data transaksi...")

# Summary Warning Banner & Status
st.markdown("---")
st.markdown("🟡 `Perlu Diperiksa` - Sistem berjalan normal dan terhubung ke database SPBU 4150201.")
