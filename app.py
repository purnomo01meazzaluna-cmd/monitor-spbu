import pandas as pd
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="SPBU Monitoring & Fraud Prevention",
    page_icon="⛽",
    layout="wide",
)

# Inisialisasi Session State untuk menyimpan data simulasi
if "df" not in st.session_state:
    st.session_state.df = None

# --- HEADER UTAMA ---
st.markdown(
    """
    <div style="background-color: #2563eb; color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin:0; font-size: 24px;"><i class="fa-solid fa-gas-pump"></i> SPBU Monitoring & Fraud Prevention Dashboard</h2>
        <p style="margin:4px 0 0 0; font-size: 14px; opacity: 0.9;">Pantau transaksi harian, deteksi indikasi kecurangan subsidi, dan kelola kuota BBM secara transparan.</p>
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

# --- SISTEM TABS ---
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Ringkasan",
        "📋 Detail Transaksi",
        "⚙️ Pengaturan Batas & Kuota",
        "📁 Data Eviden Upload",
    ]
)

# ================= TAB 1: RINGKASAN =================
with tab1:
    st.subheader("Ringkasan & Metrik Pemantauan Subsidi")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total Transaksi Dianalisis",
            value="1,428"
            if st.session_state.df is not None
            else "0",
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

    st.markdown("---")
    if st.session_state.df is None:
        st.info(
            "💡 Belum ada data yang dianalisis. Silakan unggah file CSV/XLSX pada tab **Data Eviden Upload** untuk menampilkan grafik dan metrik lengkap."
        )
    else:
        st.success("Data berhasil dimuat dan dianalisis.")


# ================= TAB 2: DETAIL TRANSAKSI =================
with tab2:
    st.subheader("Detail Transaksi & Indikasi Temuan")

    search_query = st.text_input(
        "🔍 Cari No. Plat / Transaksi", placeholder="Ketik nomor plat..."
    )

    # Data Dummy untuk Tampilan Detail
    data_dummy = {
        "Waktu": ["08:14:22", "09:30:11", "10:15:40"],
        "No. Plat": ["B 4567 XYZ", "H 1234 ABC", "D 9999 XX"],
        "Jenis BBM": ["Solar Subsidi", "Pertalite", "Solar Subsidi"],
        "Volume": ["45 Liter", "30 Liter", "60 Liter"],
        "Indikasi Temuan": [
            "Plat Palsu / Mismatch",
            "Lebih Kuota Harian",
            "Isi Ulang Beruntun",
        ],
        "Status Verifikasi": ["Belum Dicek", "Belum Dicek", "Tervalidasi CCTV"],
    }
    df_detail = pd.DataFrame(data_dummy)

    if search_query:
        df_detail = df_detail[
            df_detail["No. Plat"]
            .str.contains(search_query, case=False, na=False)
        ]

    st.dataframe(df_detail, use_container_width=True)


# ================= TAB 3: PENGATURAN BATAS & KUOTA =================
with tab3:
    st.subheader("Konfigurasi Batas & Kuota BBM (JBT & JBK)")
    st.markdown(
        "Atur batasan volume maksimal harian berdasarkan aturan **JBT** (Solar) dan **JBK** (Pertalite) yang dikelompokkan menurut jenis kendaraan/plat."
    )

    with st.form("form_pengaturan_jbt_jbk"):
        st.markdown("### 🚚 Pengaturan JBT (Jenis BBM Tertentu - Solar)")
        col1, col2 = st.columns(2)
        with col1:
            jbt_r4_pribadi = st.number_input(
                "Roda 4 Pribadi (Liter/Hari)",
                min_value=0,
                max_value=200,
                value=60,
                key="jbt_r4_pribadi",
            )
            jbt_r4_umum = st.number_input(
                "Angkutan Umum / Barang Roda 4 (Liter/Hari)",
                min_value=0,
                max_value=300,
                value=80,
                key="jbt_r4_umum",
            )
        with col2:
            jbt_r6_lebih = st.number_input(
                "Truk / Bus Roda 6 atau Lebih (Liter/Hari)",
                min_value=0,
                max_value=500,
                value=200,
                key="jbt_r6_lebih",
            )

        st.markdown("---")
        st.markdown("### ⛽ Pengaturan JBK (Jenis BBM Khusus Penugasan - Pertalite)")
        col3, col4 = st.columns(2)
        with col3:
            jbk_r4_pribadi = st.number_input(
                "Roda 4 Pribadi / Umum (Liter/Hari)",
                min_value=0,
                max_value=300,
                value=120,
                key="jbk_r4_pribadi",
            )
        with col4:
            jbk_roda_2 = st.number_input(
                "Kendaraan Roda 2 / Motor (Liter/Hari)",
                min_value=0,
                max_value=50,
                value=10,
                key="jbk_roda_2",
            )

        st.markdown("---")
        st.markdown("### ⏱️ Pengaturan Sistem & Deteksi")
        tenggat_waktu = st.number_input(
            "Tenggat Waktu Isi Ulang Beruntun (Menit)",
            min_value=10,
            max_value=1440,
            value=180,
            help="Batas waktu jeda minimum antar pengisian agar tidak terdeteksi sebagai isi ulang beruntun yang mencurigakan.",
        )

        submit_btn = st.form_submit_button("Simpan Pengaturan JBT & JBK")
        if submit_btn:
            st.success(
                "Aturan batas kuota JBT, JBK, dan parameter plat berhasil diperbarui!"
            )


# ================= TAB 4: DATA EVIDEN UPLOAD =================
with tab4:
    st.subheader("Sumber Data Transaksi (Hose Delivery)")
    st.write(
        "Unggah file laporan penjualan harian (Excel / CSV) untuk memulai proses monitoring otomatis."
    )

    uploaded_file = st.file_uploader(
        "Pilih file CSV atau XLSX", type=["csv", "xlsx"]
    )

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
            <div style="border: 2px dashed #cbd5e1; padding: 40px; text-align: center; border-radius: 8px; background-color: #f8fafc;">
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
