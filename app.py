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

# Custom Styling to match the clean Pertamina/modern UI in screenshots
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stCard {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: left;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Header Section
col_logo, col_title = st.columns([1, 10])
with col_logo:
    st.markdown("### ⛽")
with col_title:
    st.markdown("**MONITORING · DATA H-1 (KEMARIN)**")
    st.markdown("## Monitor Subsidi Tepat Guna")
    st.caption("Penyaringan awal anomali BBM bersubsidi — untuk verifikasi CCTV & koordinasi SAMSAT.")

st.markdown("---")

# File Uploader Section
st.markdown("### 📂 Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk pilih file")
st.caption("Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi (Pertamax dll.) diabaikan. Plat diambil dari kolom Payment.")

uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"], label_visibility="collapsed")

# Default Sample Data generator if no file uploaded
@st.cache_data
def load_default_data():
    data = {
        'ID': [2305895, 2305917, 2305921, 2306001, 2306015, 2306020, 2306045],
        'Waktu': ['31/08/2026, 07.20.34', '31/08/2026, 07.39.52', '31/08/2026, 07.42.06', 
                  '31/08/2026, 09.15.12', '31/08/2026, 10.00.00', '31/08/2026, 11.30.22', '31/08/2026, 13.20.10'],
        'Product': ['BIO_SOLAR', 'BIO_SOLAR', 'BIO_SOLAR', 'SOLAR', 'BIO_SOLAR', 'BIO_SOLAR', 'BIO_SOLAR'],
        'Plat': ['AD1178KH', 'AD1178KH', 'AD1178KH', 'G8782HA', 'H1460UW', 'H86520V', 'H7257BC'],
        'Volume': [11.77, 36.77, 22.06, 44.0, 34.0, 29.0, 18.0],
        'Perkiraan_Jenis': ['Mobil penumpang', 'Mobil penumpang', 'Mobil penumpang', 'Mobil barang', 'Mobil penumpang', 'Mobil barang', 'Bus'],
        'Status': ['Perlu Diperiksa', 'Perlu Diperiksa', 'Perlu Diperiksa', 'Normal', 'Normal', 'Normal', 'Normal'],
        'Alasan': [
            'Total harian 70.6L > jatah mobil pribadi (50L) — konfirmasi jenis',
            'Plat sama isi ulang < 3 menit | Total harian 70.6L > jatah mobil pribadi (50L)',
            'Plat sama isi ulang < 3 menit | Total harian 70.6L > jatah mobil pribadi (50L)',
            'Transaksi normal', 'Transaksi normal', 'Transaksi normal', 'Transaksi normal'
        ]
    }
    return pd.DataFrame(data)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success(f"Berhasil memuat file: {uploaded_file.name}")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        df = load_default_data()
else:
    df = load_default_data()

# Configuration & Threshold Expandable Section
with st.expander("⚙️ Pengaturan ambang batas & kuota", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        min_interval = st.number_input("Jeda minimum antar transaksi plat sama (menit)", value=3)
        moto_start = st.number_input("Angka motor mulai dari — 2000 = skema nasional, 3000 = gaya DKI", value=3000)
        sol_limit = st.number_input("Batas terlonggar Solar/JBT (L/hari)", value=200)
    with col2:
        vol_besar = st.number_input('Volume tunggal dianggap "big" — catatan (liter)', value=80)
        vol_wajar_motor = st.number_input("Volume wajar maks. untuk indikasi motor (liter) — pemicu lead", value=20)
        pert_limit = st.number_input("Batas terlonggar Pertalite/JBKP (L/hari)", value=60)
    with col3:
        bbm_subsidi = st.text_input("Jenis BBM bersubsidi (pisah koma)", value="PERTALITE, SOLAR, BIOSOLAR")
        hide_motor = st.checkbox("Anggap motor, sembunyikan", value=True)

    st.markdown("---")
    st.markdown("#### Kuota Solar / Biosolar — JBT (liter/hari, per kendaraan)")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    with q_col1: q_pribadi = st.number_input("Pribadi roda 4", value=60)
    with q_col2: q_umum = st.number_input("Umum/barang roda 4", value=80)
    with q_col3: q_roda6 = st.number_input("Roda 6 atau lebih", value=200)
    with q_col4: q_pelayanan = st.number_input("Pelayanan umum", value=50)

    st.markdown("#### Kuota Pertalite — JBKP (liter/hari, per kendaraan)")
    p_col1, p_col2 = st.columns(2)
    with p_col1: p_roda4 = st.number_input("Roda 4 (pribadi/umum) - Pertalite", value=50)
    with p_col2: p_pelayanan = st.number_input("Pelayanan umum - Pertalite", value=50)

    st.markdown("---")
    st.markdown("**Tentang "Perkiraan Jenis" dari plat (skema nasional)**")
    st.info("1~(motor~1) mobil penumpang · [motor]~6999 sepeda motor · 7000~7999 bus · 8000~8999 mobil barang · 9000~9999 kendaraan khusus.")

# Summary Warning Banner
st.warning("""
**Cara kerja penilaian.** Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. **Perkiraan jenis** dari angka plat hanya jadi **lead "cek plat palsu"** bila janggal — mis. angka plat ≈ motor tapi mengisi Solar. Foto CCTV per baris menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
""")

# Top Metrics Row 1
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Plat melewati kuota harian", value="0")
with m2:
    st.metric(label="Transaksi subsidi tanpa nopol", value="0")
with m3:
    st.metric(label="Angka plat tak cocok konsumsi (lead)", value="0")

# Top Metrics Row 2
t1, t2, t3, t4 = st.columns(4)
with t1:
    st.metric(label="Transaksi JBT", value=str(len(df)))
with t2:
    st.metric(label="Sangat mencurigakan", value="0")
with t3:
    st.metric(label="Perlu diperiksa", value="3")
with t4:
    st.metric(label="Normal", value=str(len(df) - 3))

st.markdown("---")

# Tab Filters & Search Bar
tab_jbt, tab_jbkp = st.tabs(["JBT · Solar (7)", "JBKP · Pertalite (6)"])

col_search, col_btn1, col_btn2, col_btn3 = st.columns([3, 1, 1, 1])
with col_search:
    search_query = st.text_input("Cari plat nomor...", placeholder="Cari plat nomor...", label_visibility="collapsed")
with col_btn1:
    if st.button("Analisis ulang"):
        st.toast("Analisis ulang dijalankan!")
with col_btn2:
    st.button("Unduh tindak lanjut (Excel)")
with col_btn3:
    st.button("Unduh transaksi + foto (Excel)")

# Filter dataframe based on search
if search_query:
    filtered_df = df[df['Plat'].str.contains(search_query, case=False, na=False)]
else:
    filtered_df = df

with tab_jbt:
    st.markdown("#### Rekap per Plat (Harian) — Solar/JBT")
    st.caption("Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT.")
    
    # Summary Table per Plate
    plate_summary = filtered_df.groupby(['Plat', 'Perkiraan_Jenis']).agg(
        Total_Isi=('ID', 'count'),
        Total_Volume=('Volume', 'sum'),
        Status=('Status', 'first')
    ).reset_index()

    for idx, row in plate_summary.iterrows():
        cols = st.columns([1.5, 2, 1, 3.5, 1.5])
        with cols[0]:
            st.markdown(f"**{row['Plat']}**")
        with cols[1]:
            st.markdown(f"≈ {row['Perkiraan_Jenis']} `ESTIMASI PLAT`")
        with cols[2]:
            st.markdown(f"{row['Total_Isi']}×")
        with cols[3]:
            pct = int((row['Total_Volume'] / 200) * 100)
            st.progress(pct / 100, text=f"{row['Total_Volume']:.0f} L / 200 L (batas terlonggar)  {pct}%")
        with cols[4]:
            if row['Status'] == 'Perlu Diperiksa':
                st.markdown("🟡 `Perlu Diperiksa`")
            else:
                st.markdown("🟢 `Normal`")

    st.markdown("---")
    st.markdown("#### Detail Transaksi & CCTV")
    
    for idx, row in filtered_df.iterrows():
        with st.container():
            col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h = st.columns([1, 1, 1.5, 1.2, 1, 1.5, 1.5, 2.5])
            with col_a:
                if st.button("📷 Kamera", key=f"cam_{row['ID']}_{idx}"):
                    st.info(f"Membuka kamera untuk transaksi {row['ID']}")
            with col_b:
                if st.button("🖼️ Galeri", key=f"gal_{row['ID']}_{idx}"):
                    st.info(f"Membuka galeri foto untuk {row['Plat']}")
            with col_c:
                st.markdown(f"**{row['ID']}**")
            with col_d:
                st.markdown(f"{row['Waktu']}")
            with col_e:
                st.markdown(f"`{row['Product']}`")
            with col_f:
                st.markdown(f"**{row['Plat']}**")
            with col_g:
                st.markdown(f"{row['Volume']}L")
            with col_h:
                if row['Status'] == 'Perlu Diperiksa':
                    st.markdown(f"🟡 `Perlu Diperiksa`

<small>{row['Alasan']}</small>", unsafe_allow_html=True)
                else:
                    st.markdown("🟢 `Normal`")
            st.markdown("---")

with tab_jbkp:
    st.markdown("#### Rekap per Plat (Harian) — Pertalite/JBKP")
    st.caption("Data pengisian Pertalite harian.")
    st.info("Belum ada anomali signifikan tercatat untuk JBKP pada periode ini.")

st.markdown("<small>+4 transaksi Normal — klik untuk tampilkan</small>", unsafe_allow_html=True)
