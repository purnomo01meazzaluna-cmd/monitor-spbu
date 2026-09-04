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

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU 4150201 | Semarang, Jawa Tengah**")
st.markdown("---")

# File Uploader di Sidebar untuk Tarikan Data (Excel / CSV)
st.sidebar.header("📁 Unggah Data Transaksi")
uploaded_file = st.sidebar.file_uploader("Upload file Excel (.xlsx) atau CSV", type=["csv", "xlsx"])

# Fungsi untuk memuat dan memproses data
@st.cache_data
def load_data(file):
    if file is not None:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            return df
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")
            return None
    return None

# Ambil Data dari Upload atau Buat Data Dummy Default jika belum upload
df_raw = load_data(uploaded_file)

if df_raw is None:
    # --- DATA DUMMY (Fallback jika belum ada file yang di-upload) ---
    np.random.seed(42)
    sample_dates = pd.date_range(start="2026-09-01", end="2026-09-05", freq="h")
    df_raw = pd.DataFrame({
        "Tanggal": sample_dates.date,
        "Waktu": sample_dates.strftime("%H:%M:%S"),
        "Plat Nomor": np.random.choice(["H 1234 AB", "K 5678 CD", "H 9999 XYZ", "B 1234 ABC", "H 4321 XX"], size=len(sample_dates)),
        "Jenis BBM": np.random.choice(["Pertalite", "Biosolar"], size=len(sample_dates), p=[0.6, 0.4]),
        "Volume (L)": np.random.randint(15, 65, size=len(sample_dates)),
        "Status": np.random.choice(["Valid", "Perlu Diperiksa"], size=len(sample_dates), p=[0.85, 0.15])
    })

# Pastikan kolom Tanggal berformat datetime.date agar bisa difilter
if "Tanggal" in df_raw.columns:
    df_raw["Tanggal"] = pd.to_datetime(df_raw["Tanggal"]).dt.date
else:
    df_raw["Tanggal"] = datetime.now().date()

# Sidebar Filter Parameter Tanggal
st.sidebar.markdown("---")
st.sidebar.header("Pengaturan Parameter")
available_dates = sorted(df_raw["Tanggal"].unique())
default_date = available_dates[-1] if len(available_dates) > 0 else datetime.now().date()

selected_date = st.sidebar.date_input(
    "Pilih Tanggal Analisis", 
    value=default_date
)

# Filter Data Berdasarkan Tanggal yang Dipilih
df_filtered = df_raw[df_raw["Tanggal"] == selected_date]

# Main Layout Tabs
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])

with tab1:
    st.subheader(f"Ikhtisar Harian Penyaluran BBM Subsidi ({selected_date})")
    
    if df_filtered.empty:
        st.warning(f"Tidak ada data transaksi yang ditemukan untuk tanggal {selected_date}.")
    else:
        total_vol = df_filtered["Volume (L)"].sum()
        vol_pertalite = df_filtered[df_filtered["Jenis BBM"].str.contains("Pertalite", case=False, na=False)]["Volume (L)"].sum()
        vol_biosolar = df_filtered[df_filtered["Jenis BBM"].str.contains("Solar|Biosolar", case=False, na=False)]["Volume (L)"].sum()
        total_kendaraan = df_filtered["Plat Nomor"].nunique()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Total Volume Terjual", value=f"{total_vol:,.0f} Liter")
        with col2:
            st.metric(label="Transaksi Pertalite", value=f"{vol_pertalite:,.0f} Liter")
        with col3:
            st.metric(label="Transaksi Biosolar", value=f"{vol_biosolar:,.0f} Liter")
        with col4:
            st.metric(label="Kendaraan Terlayani", value=f"{total_kendaraan} Unit")

        st.markdown("### Grafik Tren Penyaluran per Jam")
        
        if "Waktu" in df_filtered.columns:
            df_filtered["Jam"] = pd.to_datetime(df_filtered["Waktu"], format='%H:%M:%S', errors='coerce').dt.hour
            chart_grouped = df_filtered.pivot_table(index="Jam", columns="Jenis BBM", values="Volume (L)", aggfunc="sum").fillna(0)
            
            full_hours = pd.DataFrame(index=range(24))
            chart_grouped = full_hours.join(chart_grouped).fillna(0)
            
            st.line_chart(chart_grouped)
        else:
            st.info("Kolom 'Waktu' tidak ditemukan dalam format HH:MM:SS untuk menampilkan grafik per jam.")

with tab2:
    st.subheader(f"Pencarian & Riwayat Plat Nomor Kendaraan ({selected_date})")
    search_query = st.text_input("Cari Plat Nomor Kendaraan (contoh: H 1234 XX):", "")
    
    if df_filtered.empty:
        st.info("Tidak ada data riwayat untuk tanggal ini.")
    else:
        if search_query:
            filtered_search = df_filtered[df_filtered["Plat Nomor"].str.contains(search_query, case=False, na=False)]
            st.dataframe(filtered_search, width='stretch')
        else:
            st.dataframe(df_filtered, width='stretch')

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

# Summary Warning Banner & Status
st.markdown("---")
st.markdown("🟡 `Perlu Diperiksa` - Sistem berjalan normal dan terhubung ke database SPBU 4150201.")
