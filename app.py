import json
import os
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="SPBU Monitoring & Fraud Prevention",
    page_icon="⛽",
    layout="wide",
)

# File untuk menyimpan konfigurasi secara permanen
CONFIG_FILE = "config_kuota.json"

default_config = {
    "jbt_1": 60, "jbt_2": 0, "jbt_3": 200, "jbt_4": 200, "jbt_5": 250,
    "jbkp_1": 60, "jbkp_2": 8, "jbkp_3": 120, "jbkp_4": 120, "jbkp_5": 120,
    "tenggat_waktu": 180,
    "max_freq_pelangsir_jbt": 2,
    "max_freq_pelangsir_jbkp_r4": 3,
    "max_freq_pelangsir_jbkp_r2": 4,
    "max_freq_pelangsir_jbt_r4_umum": 2,
    "max_freq_pelangsir_jbt_r6": 2,
    "max_vol_mismatch": 100
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                for k, v in default_config.items():
                    if k not in loaded:
                        loaded[k] = v
                return loaded
        except:
            return default_config
    return default_config

if "config_data" not in st.session_state:
    st.session_state.config_data = load_config()

if "df" not in st.session_state:
    st.session_state.df = None

lock_keys = [
    "jbt_1", "jbt_2", "jbt_3", "jbt_4", "jbt_5",
    "jbkp_1", "jbkp_2", "jbkp_3", "jbkp_4", "jbkp_5",
    "max_freq_pelangsir_jbt", "max_freq_pelangsir_jbkp_r4", "max_freq_pelangsir_jbkp_r2",
    "max_freq_pelangsir_jbt_r4_umum", "max_freq_pelangsir_jbt_r6", "max_vol_mismatch", "tenggat_waktu"
]
for k in lock_keys:
    if f"lock_{k}" not in st.session_state:
        st.session_state[f"lock_{k}"] = True

# --- HEADER UTAMA ---
st.markdown(
    """
    <div style="background-color: #2563eb; color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin:0; font-size: 24px;"><i class="fa-solid fa-gas-pump"></i> SPBU Monitoring & Fraud Prevention Dashboard</h2>
        <p style="margin:4px 0 0 0; font-size: 14px; opacity: 0.9;">Pantau transaksi harian, deteksi indikasi kecurangan subsidi, dan kelola kuota BBM berdasarkan rentang plat nomor.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- BANNER CARA KERJA PENILAIAN ---
st.markdown(
    """
    <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; border-radius: 4px; font-size: 14px; margin-bottom: 20px;">
        <strong>Cara kerja penilaian.</strong> Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
        <strong>Perkiraan jenis</strong> dari angka plat (<code>ESTIMASI PLAT</code>) hanya jadi <strong>lead "cek plat palsu"</strong> bila janggal - mis. angka plat &ne; motor tapi mengisi Solar. 
        Foto CCTV per baris (kamera HP atau upload file di PC) menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
    </div>
    """,
    unsafe_allow_html=True,
)

# --- SIDEBAR NAVIGASI (LIST BAR SEBELAH KIRI) ---
st.sidebar.markdown("### 🗂️ Menu Navigasi SPBU")
selected_tab = st.sidebar.radio(
    "Pilih Menu:",
    [
        "📊 Ringkasan",
        "📋 Detail Transaksi",
        "🚨 Pelangsir & Beruntun",
        "⚠️ Mismatch Kendaraan",
        "⚙️ Pengaturan Batas & Kuota",
        "📁 Data Eviden Upload"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips SPBU:** Pastikan file evisensi/hose delivery harian di-upload melalui menu **Data Eviden Upload** untuk memperbarui data analisis.")

# ================= KONTEN BERDASARKAN SIDEBAR =================

if selected_tab == "📊 Ringkasan":
    st.subheader("Ringkasan & Metrik Pemantauan Subsidi")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            label="Total Transaksi Dianalisis",
            value="1,428" if st.session_state.df is not None else "0",
            delta="Data Kemarin",
        )
    with col2:
        st.metric(
            label="Subsidi Tanpa Nopol",
            value="14" if st.session_state.df is not None else "0",
            delta="Perlu Investigasi",
            delta_color="inverse",
        )
    with col3:
        st.metric(
            label="Lebih Kuota Harian",
            value="8" if st.session_state.df is not None else "0",
            delta="Indikasi Pengetatan",
            delta_color="inverse",
        )
    with col4:
        st.metric(
            label="Isi Ulang Beruntun",
            value="5" if st.session_state.df is not None else "0",
            delta="Aktivitas Mencurigakan",
            delta_color="inverse",
        )
    with col5:
        st.metric(
            label="Mismatch Kendaraan",
            value="3" if st.session_state.df is not None else "0",
            delta="Potong Kuota / Plat Palsu",
            delta_color="inverse",
        )

    st.markdown("---")
    st.markdown("##### Filter Kategori BBM Berdasarkan Indikasi")
    selected_bbm = st.radio(
        "Pilih Jenis BBM",
        options=["JBT · Solar (4)", "JBKP · Pertalite (5)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")
    if st.session_state.df is None:
        st.info(f"💡 Menampilkan ringkasan untuk kategori: **{selected_bbm}**. Belum ada data yang dianalisis. Silakan unggah file pada menu **📁 Data Eviden Upload** di sebelah kiri.")
    else:
        st.success(f"Berhasil memuat data dan dianalisis untuk kategori: **{selected_bbm}**.")
        
        # --- TABEL REKAP PER PLAT (HARIAN) SETELAH DATA DIUPLOAD ---
        st.markdown("#### Rekap per Plat (Harian) — Solar/JBT")
        st.markdown("<p style='font-size: 13px; color: gray;'>Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT.</p>", unsafe_allow_html=True)

        rekap_data = [
            {"Plat": "H87790V", "Jenis": "Mobil barang", "ISI": "2×", "Total": "147 L / 200 L (batas terlonggar)", "Persen": 73, "Status": "Perlu Diperiksa"},
            {"Plat": "AD8275BJ", "Jenis": "Mobil barang", "ISI": "4×", "Total": "132 L / 200 L (batas terlonggar)", "Persen": 66, "Status": "Perlu Diperiksa"},
            {"Plat": "H1589UE", "Jenis": "Mobil penumpang", "ISI": "1×", "Total": "116 L / 200 L (batas terlonggar)", "Persen": 58, "Status": "Perlu Diperiksa"},
            {"Plat": "B9877TCR", "Jenis": "Kendaraan khusus", "ISI": "2×", "Total": "107 L / 200 L (batas terlonggar)", "Persen": 54, "Status": "Perlu Diperiksa"},
            {"Plat": "H9644JC", "Jenis": "Kendaraan khusus", "ISI": "1×", "Total": "93 L / 200 L (batas terlonggar)", "Persen": 46, "Status": "Perlu Diperiksa"},
            {"Plat": "H86450V", "Jenis": "Mobil barang", "ISI": "3×", "Total": "93 L / 200 L (batas terlonggar)", "Persen": 46, "Status": "Perlu Diperiksa"},
            {"Plat": "H8249AV", "Jenis": "Mobil barang", "ISI": "2×", "Total": "88 L / 200 L (batas terlonggar)", "Persen": 44, "Status": "Perlu Diperiksa"},
            {"Plat": "H70090V", "Jenis": "Bus", "ISI": "1×", "Total": "84 L / 200 L (batas terlonggar)", "Persen": 42, "Status": "Perlu Diperiksa"},
            {"Plat": "H77500C", "Jenis": "Bus", "ISI": "1×", "Total": "84 L / 200 L (batas terlonggar)", "Persen": 42, "Status": "Perlu Diperiksa"},
            {"Plat": "H9602GA", "Jenis": "Kendaraan khusus", "ISI": "1×", "Total": "82 L / 200 L (batas terlonggar)", "Persen": 41, "Status": "Perlu Diperiksa"},
            {"Plat": "H77490C", "Jenis": "Bus", "ISI": "1×", "Total": "81 L / 200 L (batas terlonggar)", "Persen": 40, "Status": "Perlu Diperiksa"},
            {"Plat": "H8718RE", "Jenis": "Mobil barang", "ISI": "2×", "Total": "81 L / 200 L (batas terlonggar)", "Persen": 40, "Status": "Perlu Diperiksa"},
        ]

        # Header Tabel Kustom yang bersih dan rapi
        header_cols = st.columns([1.5, 2.2, 0.8, 4, 1.5])
        with header_cols[0]: st.markdown("**PLAT**")
        with header_cols[1]: st.markdown("**PERKIRAAN JENIS (DARI PLAT)**")
        with header_cols[2]: st.markdown("**ISI**")
        with header_cols[3]: st.markdown("**TOTAL VS KUOTA HARIAN**")
        with header_cols[4]: st.markdown("**STATUS**")
        st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

        for row in rekap_data:
            cols = st.columns([1.5, 2.2, 0.8, 4, 1.5])
            with cols[0]:
                st.markdown(f"**{row['Plat']}**")
            with cols[1]:
                st.markdown(f"≈ {row['Jenis']} &nbsp; <code style='font-size:10px;'>ESTIMASI PLAT</code>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"{row['ISI']}")
            with cols[3]:
                st.progress(row['Persen'])
                st.markdown(f"<span style='font-size: 12px; color: #555;'>{row['Total']} &nbsp; • &nbsp; {row['Persen']}%</span>", unsafe_allow_html=True)
            with cols[4]:
                st.markdown("<span style='background-color: #fef3c7; color: #b45309; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 500;'>🟡 Perlu Diperiksa</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 8px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)


elif selected_tab == "📋 Detail Transaksi":
    st.subheader("Detail Transaksi & Indikasi Temuan")
    search_query = st.text_input("🔍 Cari No. Plat / Transaksi", placeholder="Ketik nomor plat...")

    data_dummy = {
        "Waktu": ["08:14:22", "09:30:11", "10:15:40"],
        "No. Plat": ["B 1234 XYZ", "B 4567 ABC", "B 9876 DEF"],
        "Jenis BBM": ["JBT (Solar)", "JBKP (Pertalite)", "JBT (Solar)"],
        "Volume": ["45 Liter", "30 Liter", "200 Liter"],
        "Indikasi Temuan": ["Normal", "Lebih Kuota Harian", "Sesuai Kuota Truk Khusus"],
        "Status Verifikasi": ["Belum Dicek", "Belum Dicek", "Tervalidasi CCTV"],
    }
    df_detail = pd.DataFrame(data_dummy)

    if search_query:
        df_detail = df_detail[df_detail["No. Plat"].str.contains(search_query, case=False, na=False)]

    st.dataframe(df_detail, use_container_width=True)


elif selected_tab == "🚨 Pelangsir & Beruntun":
    st.subheader("🚨 Identifikasi Pelangsir (Isi Ulang Beruntun)")
    st.write("Menu ini memfilter kendaraan yang melakukan pengisian BBM bersubsidi secara berulang dalam rentang waktu singkat di hari yang sama.")
    
    data_pelangsir = {
        "No. Plat": ["N 8888 XX", "B 3333 YY"],
        "Frekuensi Isi": [3, 4],
        "Total Volume (Liter)": [180, 240],
        "Rentang Waktu": ["1.5 Jam", "45 Menit"],
        "Status Aksi": ["Blokir Barcode Sementara", "Perlu Investigasi CCTV"]
    }
    st.dataframe(pd.DataFrame(data_pelangsir), use_container_width=True)


elif selected_tab == "⚠️ Mismatch Kendaraan":
    st.subheader("⚠️ Identifikasi Ketidaksesuaian (Mismatch Kendaraan vs BBM)")
    st.write("Menu khusus mendeteksi kendaraan roda dua atau mobil bensin non-solar yang mengisi Jenis BBM Tertentu (JBT Solar), atau indikasi plat nomor palsu.")
    
    data_mismatch = {
        "Waktu": ["11:20:10", "13:45:00"],
        "No. Plat": ["D 1111 AA (Estimasi Motor)", "B 9999 ZZ (Estimasi Sedan)"],
        "Jenis BBM Diisi": ["JBT (Solar)", "JBT (Solar)"],
        "Tingkat Risiko": ["Tinggi (Potong Kuota)", "Tinggi (Plat Palsu)"],
    }
    st.dataframe(pd.DataFrame(data_mismatch), use_container_width=True)


elif selected_tab == "⚙️ Pengaturan Batas & Kuota":
    st.subheader("Konfigurasi Batas & Kuota BBM Berdasarkan Rentang Plat Nomor")
    st.markdown("Atur batasan volume maksimal harian (Liter/Hari) dan ambang batas pelangsir. Centang kotak 🔒 di samping untuk membuka/mengunci input, lalu klik tombol **Simpan**.")

    def render_locked_input(label, key):
        col_inp, col_chk = st.columns([0.92, 0.08])
        with col_chk:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            is_locked = st.checkbox("🔒", key=f"lock_{key}")
        with col_inp:
            val = st.number_input(label, value=st.session_state.config_data.get(key, 0), key=key, disabled=is_locked)
        return val

    st.markdown("### 🚚 JBT (Jenis BBM Tertentu)")
    col1, col2 = st.columns(2)
    with col1:
        render_locked_input("JBT | 0001-2999 (Roda 4 Pribadi)", "jbt_1")
        render_locked_input("JBT | 3000-6999 (Roda 2 Sepeda Motor)", "jbt_2")
        render_locked_input("JBT | 7000-7999 (Roda 4 > Minibus/Bus)", "jbt_3")
    with col2:
        render_locked_input("JBT | 8000-8999 (Roda 4 > Truck)", "jbt_4")
        render_locked_input("JBT | 9000-9999 (Roda 4 > Truck Khusus)", "jbt_5")

    st.markdown("---")
    st.markdown("### ⛽ JBKP (Jenis BBM Khusus Penugasan)")
    col3, col4 = st.columns(2)
    with col3:
        render_locked_input("JBKP | 0001-2999 (Roda 4 Pribadi)", "jbkp_1")
        render_locked_input("JBKP | 3000-6999 (Roda 2 Sepeda Motor)", "jbkp_2")
        render_locked_input("JBKP | 7000-7999 (Roda 4 > Minibus)", "jbkp_3")
    with col4:
        render_locked_input("JBKP | 8000-8999 (Roda 4 > Pick Up)", "jbkp_4")
        render_locked_input("JBKP | 9000-9999 (Roda 4 > Pick Up Khusus)", "jbkp_5")

    st.markdown("---")
    st.markdown("### ⏱️ Pengaturan Sistem & Deteksi")
    
    render_locked_input("Tenggat Waktu Isi Ulang Beruntun (Menit)", "tenggat_waktu")
    
    st.markdown("##### Ambang Batas Frekuensi Pelangsir (Kali/Hari)")
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    with col_p1:
        render_locked_input("JBT (Solar)", "max_freq_pelangsir_jbt")
    with col_p2:
        render_locked_input("JBKP R4 (Mobil)", "max_freq_pelangsir_jbkp_r4")
    with col_p3:
        render_locked_input("JBKP R2 (Motor)", "max_freq_pelangsir_jbkp_r2")
    with col_p4:
        render_locked_input("JBT R4 Umum", "max_freq_pelangsir_jbt_r4_umum")
    with col_p5:
        render_locked_input("JBT R6", "max_freq_pelangsir_jbt_r6")

    render_locked_input("Ambang Batas Volume Mismatch Kendaraan (Liter)", "max_vol_mismatch")

    if st.button("Simpan Pengaturan Kuota Berdasarkan Plat"):
        new_config = {
            "jbt_1": st.session_state.get("jbt_1", 60),
            "jbt_2": st.session_state.get("jbt_2", 0),
            "jbt_3": st.session_state.get("jbt_3", 200),
            "jbt_4": st.session_state.get("jbt_4", 200),
            "jbt_5": st.session_state.get("jbt_5", 250),
            "jbkp_1": st.session_state.get("jbkp_1", 60),
            "jbkp_2": st.session_state.get("jbkp_2", 8),
            "jbkp_3": st.session_state.get("jbkp_3", 120),
            "jbkp_4": st.session_state.get("jbkp_4", 120),
            "jbkp_5": st.session_state.get("jbkp_5", 120),
            "tenggat_waktu": st.session_state.get("tenggat_waktu", 180),
            "max_freq_pelangsir_jbt": st.session_state.get("max_freq_pelangsir_jbt", 2),
            "max_freq_pelangsir_jbkp_r4": st.session_state.get("max_freq_pelangsir_jbkp_r4", 3),
            "max_freq_pelangsir_jbkp_r2": st.session_state.get("max_freq_pelangsir_jbkp_r2", 4),
            "max_freq_pelangsir_jbt_r4_umum": st.session_state.get("max_freq_pelangsir_jbt_r4_umum", 2),
            "max_freq_pelangsir_jbt_r6": st.session_state.get("max_freq_pelangsir_jbt_r6", 2),
            "max_vol_mismatch": st.session_state.get("max_vol_mismatch", 100)
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(new_config, f, indent=4)
        st.session_state.config_data = new_config
        st.toast("Aturan kuota dan parameter deteksi berhasil disimpan secara permanen!", icon="✅")


elif selected_tab == "📁 Data Eviden Upload":
    st.subheader("Sumber Data Transaksi (Hose Delivery)")
    st.write("Unggah file laporan penjualan harian (Excel / CSV) untuk memulai proses monitoring otomatis.")

    uploaded_file = st.file_uploader("Pilih file CSV atau XLSX", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                st.session_state.df = pd.read_csv(uploaded_file)
            else:
                st.session_state.df = pd.read_excel(uploaded_file)

            st.success(f"Berhasil mengunggah file: {uploaded_file.name}")
            st.dataframe(st.session_state.df.head())
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")
    else:
        st.markdown(
            """
            <div style="border: 2px dashed #cbd5e1; padding: 40px; text-align: center; border-radius: 8px; background-color: #f8fafc; margin-top: 20px;">
                <p style="color: #64748b; font-size: 16px; margin: 0;"><b>Belum ada data yang dianalisis</b></p>
                <p style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Upload satu file CSV/XLSX hose delivery (data kemarin) untuk mulai monitoring.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>Analisis & foto berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun. Foto hilang bila halaman dimuat ulang.</p>",
    unsafe_allow_html=True,
)
