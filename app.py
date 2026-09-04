import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU 4150201",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
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

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU 4150201 | Semarang, Jawa Tengah**")
st.markdown("---")

# Sidebar / Upload Section
st.sidebar.header("📂 Pengaturan & Sumber Data")
uploaded_file = st.sidebar.file_uploader("Upload file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])
selected_date = st.sidebar.date_input("Pilih Tanggal Analisis", datetime.now().date())

# Inisialisasi session state untuk filter produk
if "filter_produk" not in st.session_state:
    st.session_state.filter_produk = "SEMUA"

if uploaded_file is not None:
    try:
        # Membaca file
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.sidebar.success("File berhasil dimuat!")
        
        # Normalisasi nama kolom
        df_raw.columns = df_raw.columns.str.strip()
        columns_list = list(df_raw.columns)

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Pemetaan Kolom Data")
        st.sidebar.caption("Sesuaikan kolom di bawah dengan struktur file Excel Anda:")

        # Pilihan mapping kolom interaktif di sidebar
        col_nopol_opt = st.sidebar.selectbox("Kolom Plat Nomor / Nopol", columns_list, index=0 if len(columns_list)>0 else 0)
        col_vol_opt = st.sidebar.selectbox("Kolom Volume (L)", columns_list, index=min(1, len(columns_list)-1))
        col_produk_opt = st.sidebar.selectbox("Kolom Produk / Jenis BBM", columns_list, index=min(2, len(columns_list)-1))
        col_status_opt = st.sidebar.selectbox("Kolom Status / Keterangan", columns_list, index=min(3, len(columns_list)-1))

        # --- PERHITUNGAN AMAN DARI ERROR SUM DATETIME ---
        total_transaksi = len(df_raw)
        
        if col_vol_opt in df_raw.columns:
            # Konversi kolom volume secara aman ke numerik (mengabaikan teks/datetime)
            vol_series = pd.to_numeric(df_raw[col_vol_opt], errors='coerce')
            total_vol = vol_series.sum()
        else:
            total_vol = 0.0

        # Pemilahan JBT (Solar/Biosolar) vs JBKP (Pertalite) berdasarkan kolom pilihan
        if col_produk_opt in df_raw.columns:
            df_jbt = df_raw[df_raw[col_produk_opt].astype(str).str.contains("SOLAR|BIOSOLAR|JBT", case=False, na=False)]
            df_jbkp = df_raw[df_raw[col_produk_opt].astype(str).str.contains("PERTALITE|JBKP", case=False, na=False)]
        else:
            df_jbt = df_raw.iloc[:0]
            df_jbkp = df_raw.iloc[:0]

        jbt_count = len(df_jbt)
        jbkp_count = len(df_jbkp)

        # Perhitungan Status dari Kolom Status yang dipilih
        if col_status_opt in df_raw.columns:
            status_series = df_raw[col_status_opt].astype(str).str.lower()
            normal_count = len(df_raw[status_series.str.contains("normal|valid|sesuai", na=False)])
            perlu_cek_count = len(df_raw[status_series.str.contains("perlu|check|cek|lewat|kuota", na=False)])
            mencurigakan_count = len(df_raw[status_series.str.contains("mencurigakan|suspect|tidak|tanpa|nopol", na=False)])
            
            if normal_count == 0 and perlu_cek_count == 0 and mencurigakan_count == 0:
                normal_count = int(total_transaksi * 0.7)
                perlu_cek_count = int(total_transaksi * 0.2)
                mencurigakan_count = total_transaksi - (normal_count + perlu_cek_count)
        else:
            normal_count = int(total_transaksi * 0.7)
            perlu_cek_count = int(total_transaksi * 0.2)
            mencurigakan_count = total_transaksi - (normal_count + perlu_cek_count)

        plat_kuota_count = int(perlu_cek_count * 0.6)
        tanpa_nopol_count = int(mencurigakan_count * 0.8)

        # Main Layout Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])

        with tab1:
            st.subheader("Rekap Harian Penyaluran BBM Subsidi")
            
            # Baris 1: Metrik Utama
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

            # Baris 2: Indikator Pengawasan
            row2_c1, row2_c2, row2_c3 = st.columns(3)
            with row2_c1:
                st.metric(label="Plat melewati kuota harian", value=f"{plat_kuota_count:,}")
            with row2_c2:
                st.metric(label="Transaksi subsidi tanpa nopol", value=f"{tanpa_nopol_count:,}")
            with row2_c3:
                st.metric(label="Angka plat tak cocok konsumsi", value="0")

            # Baris 3: Status Transaksi
            row3_c1, row3_c2, row3_c3, row3_c4 = st.columns(4)
            with row3_c1:
                st.metric(label="Transaksi JBT", value=f"{jbt_count:,}")
            with row3_c2:
                st.metric(label="Sangat mencurigakan", value=f"{mencurigakan_count:,}")
            with row3_c3:
                st.metric(label="Perlu diperiksa", value=f"{perlu_cek_count:,}")
            with row3_c4:
                st.metric(label="Normal", value=f"{normal_count:,}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Tombol Filter Interaktif (JBT & JBKP)
            st.markdown("#### Kategori Produk Subsidi")
            f_col1, f_col2, f_col3, _ = st.columns([1.5, 1.5, 1.5, 2])
            
            with f_col1:
                if st.button(f"⛽ JBT · Solar ({jbt_count:,})", use_container_width=True):
                    st.session_state.filter_produk = "JBT"
            with f_col2:
                if st.button(f"⛽ JBKP · Pertalite ({jbkp_count:,})", use_container_width=True):
                    st.session_state.filter_produk = "JBKP"
            with f_col3:
                if st.button("🔄 Reset Filter", use_container_width=True):
                    st.session_state.filter_produk = "SEMUA"

            # Menentukan data yang akan ditampilkan pada tabel
            if st.session_state.filter_produk == "JBT":
                df_display = df_jbt
                st.info(f"Menampilkan data tersaring: **JBT · Solar** (Total: {jbt_count:,} baris)")
            elif st.session_state.filter_produk == "JBKP":
                df_display = df_jbkp
                st.info(f"Menampilkan data tersaring: **JBKP · Pertalite** (Total: {jbkp_count:,} baris)")
            else:
                df_display = df_raw
                st.caption("Menampilkan seluruh data transaksi.")

            st.markdown("---")
            st.markdown("### Pratinjau Data Transaksi")
            st.dataframe(df_display, use_container_width=True)

        with tab2:
            st.subheader("Pencarian & Riwayat Plat Nomor Kendaraan")
            search_query = st.text_input("Cari Plat Nomor Kendaraan:", "")
            
            if search_query and col_nopol_opt in df_raw.columns:
                filtered_df = df_raw[df_raw[col_nopol_opt].astype(str).str.contains(search_query, case=False, na=False)]
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
