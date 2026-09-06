import streamlit as st
import pandas as pd

# Konfigurasi Halaman Dashboard SPBU
st.set_page_config(
    page_title="Dashboard Monitoring SPBU",
    page_icon="⛽",
    layout="wide"
)

# Area Unggah File
uploaded_file = st.file_uploader(
    "Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk pilih file",
    type=["csv", "xlsx"]
)
st.caption("Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi (Pertamax dll.) diabaikan. Plat diambil dari kolom Payment.")

st.markdown("---")

# Penjelasan Cara Kerja Penilaian (Expander / Box Info)
with st.expander("Cara kerja penilaian & pengaturan ambang batas kuota", expanded=True):
    st.write(
        "Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, "
        "dan isi ulang beruntun. **Perkiraan jenis** dari angka plat (`ESTIMASI PLAT`) hanya jadi **lead 'cek plat palsu'** "
        "bila janggal — mis. angka plat = motor tapi mengisi Solar. Foto CCTV per baris (kamera HP atau upload file di PC) "
        "menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir."
    )

# Baris Metrik Utama (Angka Ringkasan)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Plat melewati kuota harian", value="0")
with col2:
    st.metric(label="Transaksi subsidi tanpa nopol", value="1")
with col3:
    st.metric(label="Angka plat tak cocok konsumsi (lead)", value="0")

col4, col5, col6, col7 = st.columns(4)
with col4:
    st.metric(label="Transaksi JBT", value="4")
with col5:
    st.metric(label="Sangat mencurigakan", value="0")
with col6:
    st.metric(label="Perlu diperiksa", value="4")
with col7:
    st.metric(label="Normal", value="0")

st.markdown("")

# Tombol Tab Kategori Produk
tab1, tab2 = st.tabs(["JBT • Solar  4", "JBKP • Pertalite  4"])

with tab1:
    # Filter & Aksi di dalam Tab JBT
    c_search, c_btn1, c_btn2, c_btn3 = st.columns([3, 1, 2, 2])
    with c_search:
        search_plat = st.text_input("Cari plat nomor...", label_visibility="collapsed", placeholder="Cari plat nomor...")
    with c_btn1:
        st.button("Analisis ulang", use_container_width=True)
    with c_btn2:
        st.button("Unduh tindak lanjut (Excel)", use_container_width=True)
    with c_btn3:
        st.button("Unduh transaksi + foto (Excel)", use_container_width=True, type="primary")

    st.markdown("### Rekap per Plat (Harian) — Solar/JBT")
    st.caption("Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT.")

    # Data Dummy Tabel Rekap Harian
    df_rekap = pd.DataFrame({
        "PLAT": ["H1460UW"],
        "PERKIRAAN JENIS (DARI PLAT)": ["≈ Mobil penumpang (ESTIMASI PLAT)"],
        "ISI": ["3x"],
        "TOTAL VS KUOTA HARIAN": ["81 L / 299 L (batas terlonggar)"],
        "STATUS": ["Perlu Diperiksa"]
    })
    st.dataframe(df_rekap, use_container_width=True)

    st.markdown("### Detail Transaksi & Bukti CCTV")
    df_detail = pd.DataFrame({
        "BUKTI CCTV": ["[Lihat Kamera]"],
        "ID": ["2305873"],
        "WAKTU": ["31/08/2026, 05:45:36"],
        "PRODUCT / NOZZLE": ["BIO_SOLAR (P3/H1)"],
        "PLAT": ["H1460UW"],
        "VOLUME": ["34.35L"],
        "PERKIRAAN JENIS": ["≈ Mobil penumpang"],
        "STATUS": ["Perlu Diperiksa"],
        "ALASAN TEMUAN": ["Total harian 81.4L > jatah mobil pribadi (50L) — ..."]
    })
    st.dataframe(df_detail, use_container_width=True)

with tab2:
    st.info("Data untuk JBKP • Pertalite belum ditampilkan.")

# Footer Sederhana
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>Analisis berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun.</p>",
    unsafe_allow_html=True,
)
