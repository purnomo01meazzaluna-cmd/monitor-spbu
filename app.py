import pandas as pd
import streamlit as st

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Analisis Transaksi Subsidi SPBU",
    layout="wide",
)

# Styling CSS tambahan agar menyerupai tampilan modern di gambar
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- BAGIAN 1: UPLOAD FILE ---
st.markdown("### Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk pilih file")
st.caption(
    "Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi (Pertalite dll.) diabaikan. Plat diambil dari kolom Payment."
)

uploaded_file = st.file_uploader(
    "Pilih file CSV atau XLSX", type=["csv", "xlsx"], label_visibility="collapsed"
)

# Contoh chip file aktif jika sudah diupload
if uploaded_file:
    st.info(f"📂 1 - {uploaded_file.name} (Aktif)")
else:
    # Simulasi tampilan statis sesuai gambar jika belum ada file baru
    st.markdown(
        """<span style="background-color: #f3f4f6; padding: 4px 12px; border-radius: 16px; font-size: 14px; border: 1px solid #d1d5db;">📄 1 - Copy.xlsx ✕</span>""",
        unsafe_allow_html=True,
    )

with st.expander("▶ Pengaturan ambang batas & kuota"):
    st.write(
        "Pengaturan kuota harian kendaraan, batasan volume, dan parameter validasi plat nomor."
    )

# --- BAGIAN 2: CARA KERJA PENILAIAN ---
st.markdown(
    """
    <div style="background-color: #fffbeb; border: 1px solid #fef3c7; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; color: #92400e;">
        <b>Cara kerja penilaian.</b> Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
        <b>Perkiraan jenis</b> dari angka plat (<code style="background:#fef08a; padding:2px 4px; border-radius:4px;">ESTIMASI PLAT</code>) hanya jadi <b>lead "cek plat palsu"</b> bila janggal — mis. angka plat = motor tapi mengisi Solar. 
        Foto CCTV per baris (kamera HP atau upload file di PC) menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
    </div>
    """,
    unsafe_allow_html=True,
)

# --- BAGIAN 3: Kartu Ringkasan Metrik (KPI Cards) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="metric-card">
            <span style="font-size: 24px;">⛽</span> <b style="font-size: 20px;">0</b>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 14px;">Plat melewati kuota harian</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="metric-card">
            <span style="font-size: 24px;">🚫</span> <b style="font-size: 20px;">1</b>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 14px;">Transaksi subsidi tanpa nopol</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="metric-card">
            <span style="font-size: 24px;">🔍</span> <b style="font-size: 20px;">0</b>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 14px;">Angka plat tak cocok konsumsi (lead)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")  # Spasi

col4, col5, col6, col7 = st.columns(4)

with col4:
    st.markdown(
        """
        <div class="metric-card">
            <b style="font-size: 24px;">4</b>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 14px;">Transaksi JBT</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col5:
    st.markdown(
        """
        <div class="metric-card">
            <b style="font-size: 24px; color: #dc2626;">0</b>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 14px;">Sangat mencurigakan</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col6:
    st.markdown(
        """
        <div class="metric-card">
            <b style="font-size: 24px; color: #d97706;">4</b>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 14px;">Perlu diperiksa</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col7:
    st.markdown(
        """
        <div class="metric-card">
            <b style="font-size: 24px; color: #16a34a;">0</b>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 14px;">Normal</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# --- BAGIAN 4: TAB & FILTER ---
tab_jbt, tab_jbkp = st.tabs(["JBT · Solar  4", "JBKP · Pertalite  4"])

with tab_jbt:
    # Baris Filter & Tombol Aksi
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1.5, 1.5, 1.5])
    with f_col1:
        search_plat = st.text_input(
            "Cari", placeholder="Cari plat nomor...", label_visibility="collapsed"
        )
    with f_col2:
        st.button("Analisis ulang", use_container_width=True)
    with f_col3:
        st.button("Unduh tindak lanjut (Excel)", use_container_width=True)
    with f_col4:
        st.button(
            "Unduh transaksi + foto (Excel)",
            type="primary",
            use_container_width=True,
        )

    # Tabel 1: Rekap per Plat (Harian)
    st.markdown("### Rekap per Plat (Harian) — Solar/JBT")
    st.caption(
        "Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT."
    )

    rekap_data = {
        "PLAT": ["H1460UW"],
        "PERKIRAAN JENIS (DARI PLAT)": ["≈ Mobil penumpang [ESTIMASI PLAT]"],
        "ISI": ["3×"],
        "TOTAL VS KUOTA HARIAN": [
            "81 L / 200 L (batas terlonggar)                  41%"
        ],
        "STATUS": ["🟡 Perlu Diperiksa"],
    }
    st.dataframe(pd.DataFrame(rekap_data), use_container_width=True, hide_index=True)

    # Tabel 2: Detail Transaksi & Bukti CCTV
    st.markdown("### Detail Transaksi & Bukti CCTV")
    detail_data = {
        "BUKTI CCTV": ["[Kamera] [Galeri]"],
        "ID": ["2305873"],
        "WAKTU": ["31/08/2026, 05.45.36"],
        "PRODUCT / NOZZLE": ["BIO_SOLAR (P3/H1)"],
        "PLAT": ["H1460UW"],
        "VOLUME": ["34.35L"],
        "PERKIRAAN JENIS": ["≈ Mobil penumpang [ESTIMASI PLAT]"],
        "STATUS": ["🟡 Perlu Diperiksa"],
        "ALASAN TEMUAN": [
            "Total harian 81.4L > jatah mobil pribadi (50L) — konfirmasi jenis"
        ],
    }
    st.dataframe(
        pd.DataFrame(detail_data), use_container_width=True, hide_index=True
    )

with tab_jbkp:
    st.info("Data tab JBKP (Pertalite) akan tampil di sini.")
