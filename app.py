import streamlit as st
import pandas as pd
import numpy as np
import datetime
from io import BytesIO

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="SPBU Fraud Detection Dashboard",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM STYLING (DARK/MODERN THEME)
# ==========================================
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stMetric {
        background-color: #1a1c23;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2d3748;
    }
    .metric-title {
        font-size: 14px;
        color: #a0aec0;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #ffffff;
    }
    .card {
        background-color: #1a1c23;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2d3748;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: CONFIGURATION & DATA UPLOAD
# ==========================================
st.sidebar.markdown("## 📁 Pengaturan & Sumber Data")

# Input dinamis untuk ID SPBU dan Lokasi
spbu_id_input = st.sidebar.text_input("ID SPBU", value="4150201", help="Masukkan nomor ID SPBU Anda")
station_location = st.sidebar.text_input("Lokasi SPBU", value="Semarang")

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader(
    "Upload File Transaksi (Excel / CSV)",
    type=["xlsx", "csv"],
    help="Format file harus memiliki kolom No Polisi, Waktu Transaksi, Volume, Produk/BBM, dan Nozzle"
)

# Date filter
selected_date = st.sidebar.date_input("Tanggal Analisis", value=datetime.date.today())

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Panduan Sistem:**\n"
    "1. Masukkan ID SPBU Anda di atas.\n"
    "2. Upload file laporan transaksi harian SPBU.\n"
    "3. Sistem akan otomatis mendeteksi anomali JBT & JBKP (frekuensi berlebih & jeda waktu singkat)."
)

# ==========================================
# HEADER SECTION
# ==========================================
st.markdown(f"## ⛽ SPBU {spbu_id_input} {station_location} | JBT & JBKP Advanced Fraud Detection & Evidence")
st.markdown("Dashboard analisis transaksi harian, deteksi pola pengisian berulang (helikopter), dan audit kepatuhan penyaluran BBM bersubsidi.")

# ==========================================
# DATA LOADING & PROCESSING LOGIC
# ==========================================
@st.cache_data
def load_sample_data():
    np.random.seed(42)
    n_rows = 500
    nopol_list = ["H 1234 AB", "H 5678 CD", "K 9999 XX", "H 1111 AA", "B 2222 XYZ", "H 3333 BB", "K 4444 CC"]
    products = ["Solar (JBT)", "Pertalite (JBKP)", "Pertamax"]
    
    start_time = datetime.datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    timestamps = [start_time + datetime.timedelta(minutes=int(np.random.randint(1, 720))) for _ in range(n_rows)]
    timestamps.sort()
    
    data = {
        "Waktu Transaksi": timestamps,
        "No Polisi": np.random.choice(nopol_list, n_rows),
        "Produk": np.random.choice(products, n_rows, p=[0.4, 0.4, 0.2]),
        "Volume (L)": np.round(np.random.uniform(20, 150, n_rows), 2),
        "Nozzle": np.random.randint(1, 9, n_rows)
    }
    return pd.DataFrame(data)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.sidebar.success("File berhasil dimuat!")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca file: {e}")
        df = load_sample_data()
else:
    df = load_sample_data()
    st.sidebar.warning("Menggunakan data simulasi. Silakan upload file transaksi Anda.")

# Normalize column names
df.columns = [str(col).strip() for col in df.columns]

# ==========================================
# METRICS OVERVIEW
# ==========================================
col1, col2, col3, col4 = st.columns(4)

total_transaksi = len(df)
total_volume = df["Volume (L)"].sum() if "Volume (L)" in df.columns else 0.0
unique_vehicles = df["No Polisi"].nunique() if "No Polisi" in df.columns else 0

formatted_vol = f"{total_volume:,.2f}"

with col1:
    st.markdown(f'<div class="stMetric"><div class="metric-title">SPBU ID</div><div class="metric-value">{spbu_id_input}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stMetric"><div class="metric-title">Total Transaksi</div><div class="metric-value">{total_transaksi:,}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stMetric"><div class="metric-title">Total Volume (L)</div><div class="metric-value">{formatted_vol}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="stMetric"><div class="metric-title">Kendaraan Unik</div><div class="metric-value">{unique_vehicles:,}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# FRAUD DETECTION & ANOMALY ANALYSIS
# ==========================================
st.markdown("### 🔍 Analisis Temuan Anomali & Indikasi Kecurangan")

tab1, tab2, tab3 = st.tabs(["🚨 Deteksi Frekuensi Berlebih", "⏱️ Jeda Waktu Singkat", "📋 Seluruh Data Transaksi"])

with tab1:
    st.markdown("#### Kendaraan dengan Transaksi Berulang (Frekuensi Tinggi)")
    if "No Polisi" in df.columns:
        freq_df = df.groupby("No Polisi").size().reset_index(name="Jumlah Transaksi")
        suspicious_freq = freq_df[freq_df["Jumlah Transaksi"] > 2].sort_values(by="Jumlah Transaksi", ascending=False)
        
        if not suspicious_freq.empty:
            st.dataframe(suspicious_freq, use_container_width=True)
        else:
            st.info("Tidak ditemukan kendaraan dengan frekuensi pengisian abnormal.")
    else:
        st.warning("Kolom 'No Polisi' tidak ditemukan pada dataset.")

with tab2:
    st.markdown("#### Analisis Interval Waktu Pengisian Singkat")
    if "No Polisi" in df.columns and "Waktu Transaksi" in df.columns:
        df_sorted = df.sort_values(by=["No Polisi", "Waktu Transaksi"])
        df_sorted["Waktu Transaksi"] = pd.to_datetime(df_sorted["Waktu Transaksi"])
        df_sorted["Selisih Menit"] = df_sorted.groupby("No Polisi")["Waktu Transaksi"].diff().dt.total_seconds() / 60
        
        short_interval = df_sorted[df_sorted["Selisih Menit"] <= 30].dropna(subset=["Selisih Menit"])
        if not short_interval.empty:
            st.dataframe(short_interval[["Waktu Transaksi", "No Polisi", "Produk", "Volume (L)", "Selisih Menit"]], use_container_width=True)
        else:
            st.info("Tidak ditemukan jeda waktu pengisian yang terlalu singkat (<= 30 menit).")
    else:
        st.warning("Kolom waktu atau nomor polisi tidak lengkap.")

with tab3:
    st.markdown("#### Tabel Master Data Transaksi")
    st.dataframe(df, use_container_width=True)

# ==========================================
# EXPORT REPORT SECTION
# ==========================================
st.markdown("---")
st.markdown("### 📥 Ekspor Laporan Anomali SPBU")

def convert_df_to_excel(dataframe):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Laporan Anomali')
    processed_data = output.getvalue()
    return processed_data

excel_data = convert_df_to_excel(df)
date_str = selected_date.strftime('%Y-%m-%d')
file_name_download = f"Laporan_Anomali_SPBU_{spbu_id_input}_{date_str}.xlsx"

st.download_button(
    label="📥 Download Laporan Lengkap (.xlsx)",
    data=excel_data,
    file_name=file_name_download,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
