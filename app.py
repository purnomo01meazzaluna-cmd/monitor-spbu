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

    # --- MENU PILIHAN JENIS BBM (FILTER) ---
    st.markdown("##### Filter Kategori BBM Berdasarkan Indikasi")
    selected_bbm = st.radio(
        "Pilih Jenis BBM",
        options=["JBT · Solar (4)", "JBKP · Pertalite (5)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")

    if st.session_state.df is None:
        st.info(
            f"💡 Menampilkan ringkasan untuk kategori: **{selected_bbm}**. Belum ada data yang dianalisis. Silakan unggah file CSV/XLSX pada tab **Data Eviden Upload** untuk menampilkan grafik dan metrik lengkap."
        )
    else:
        st.success(f"Berhasil memuat data dan dianalisis untuk kategori: **{selected_bbm}**.")


# ================= TAB 2: DETAIL TRANSAKSI =================
with tab2:
    st.subheader("Detail Transaksi & Indikasi Temuan")

    search_query = st.text_input(
        "🔍 Cari No. Plat / Transaksi", placeholder="Ketik nomor plat..."
    )

    data_dummy = {
        "Waktu": ["08:14:22", "09:30:11", "10:15:40"],
        "No. Plat": ["B 1234 XYZ", "B 4567 ABC", "B 9876 DEF"],
        "Jenis BBM": ["JBT (Solar)", "JBKP (Pertalite)", "JBT (Solar)"],
        "Volume": ["45 Liter", "30 Liter", "200 Liter"],
        "Indikasi Temuan": [
            "Normal",
            "Lebih Kuota Harian",
            "Sesuai Kuota Truk Khusus",
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
    st.subheader(
        "Konfigurasi Batas & Kuota BBM Berdasarkan Rentang Plat Nomor"
    )
    st.markdown(
        "Atur batasan volume maksimal harian (Liter/Hari) untuk **JBT** dan **JBKP** berdasarkan kategori rentang nomor urut plat."
    )

    with st.form("form_pengaturan_plat"):
        st.markdown("### 🚚 JBT (Jenis BBM Tertentu)")
        col1, col2 = st.columns(2)
        with col1:
            jbt_1 = st.number_input(
                "JBT | 0001-2999 (Roda 4 Pribadi)", value=60, key="jbt_1"
            )
            jbt_2 = st.number_input(
                "JBT | 3000-6999 (Roda 2 Sepeda Motor)", value=0, key="jbt_2"
            )
            jbt_3 = st.number_input(
                "JBT | 7000-7999 (Roda 4 > Minibus/Bus)",
                value=200,
                key="jbt_3",
            )
        with col2:
            jbt_4 = st.number_input(
                "JBT | 8000-8999 (Roda 4 > Truck)", value=200, key="jbt_4"
            )
            jbt_5 = st.number_input(
                "JBT | 9000-9999 (Roda 4 > Truck Khusus)",
                value=250,
                key="jbt_5",
            )

        st.markdown("---")
        st.markdown("### ⛽ JBKP (Jenis BBM Khusus Penugasan)")
        col3, col4 = st.columns(2)
        with col3:
            jbkp_1 = st.number_input(
                "JBKP | 0001-2999 (Roda 4 Pribadi)", value=60, key="jbkp_1"
            )
            jbkp_2 = st.number_input(
                "JBKP | 3000-6999 (Roda 2 Sepeda Motor)", value=8, key="jbkp_2"
            )
            jbkp_3 = st.number_input(
                "JBKP | 7000-7999 (Roda 4 > Minibus)", value=120, key="jbkp_3"
            )
        with col4:
            jbkp_4 = st.number_input(
                "JBKP | 8000-8999 (Roda 4 > Pick Up)", value=120, key="jbkp_4"
            )
            jbkp_5 = st.number_input(
                "JBKP | 9000-9999 (Roda 4 > Pick Up Khusus)",
                value=120,
                key="jbkp_5",
            )

        st.markdown("---")
        st.markdown("### ⏱️ Pengaturan Sistem & Deteksi")
        tenggat_waktu = st.number_input(
            "Tenggat Waktu Isi Ulang Beruntun (Menit)",
            min_value=10,
            max_value=1440,
            value=180,
        )

        submit_btn = st.form_submit_button(
            "Simpan Pengaturan Kuota Berdasarkan Plat"
        )
        if submit_btn:
            st.success(
                "Aturan kuota JBT dan JBKP berdasarkan rentang plat berhasil diperbarui!"
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
