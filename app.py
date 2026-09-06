import streamlit as st
import pandas as pd

# Konfigurasi Halaman Dashboard SPBU
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna",
    page_icon="⛽",
    layout="wide"
)

# Header Bagian Atas
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.caption("MONITORING · DATA H-1 (KEMARIN)")
    st.markdown("## **Monitor Subsidi Tepat Guna**")
    st.markdown("Penyaringan awal anomali BBM bersubsidi — untuk verifikasi CCTV & koordinasi SAMSAT.")
with col_logo:
    st.markdown("<div style='text-align: right; font-weight: bold; color: #cc0000; font-size: 18px;'>PERTAMINA RETAIL</div>", unsafe_allow_html=True)

st.markdown("---")

# Area Unggah File
uploaded_file = st.file_uploader(
    "Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk pilih file",
    type=["csv", "xlsx"]
)
st.caption("Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi (Pertamax dll.) diabaikan. Plat diambil dari kolom Payment.")

# Expander Pengaturan ambang batas & kuota
with st.expander("Pengaturan ambang batas & kuota", expanded=False):
    st.write("Konfigurasi parameter batas kuota harian dan aturan deteksi anomali.")

# Box Cara Kerja Penilaian
st.markdown(
    """
    <div style="background-color: #fff8f0; border-left: 5px solid #ff8c00; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
        <span style="font-weight: bold;">Cara kerja penilaian.</span> Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. <b>Perkiraan jenis</b> dari angka plat (<code>ESTIMASI PLAT</code>) hanya jadi <b>lead "cek plat palsu"</b> bila janggal — mis. angka plat = motor tapi mengisi Solar. Foto CCTV per baris (kamera HP atau upload file di PC) menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
    </div>
    """,
    unsafe_allow_html=True
)

# Baris Kartu Metrik Atas (3 Kolom)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Plat melewati kuota harian", value="0")
with col2:
    st.metric(label="Transaksi subsidi tanpa nopol", value="1")
with col3:
    st.metric(label="Angka plat tak cocok konsumsi (lead)", value="0")

# Baris Kartu Metrik Bawah (4 Kolom)
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

# Tab Kategori Produk (JBT & JBKP)
tab1, tab2 = st.tabs(["JBT • Solar  4", "JBKP • Pertalite  4"])

with tab1:
    # Filter & Tombol Aksi
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

    # Tabel Rekap per Plat
    df_rekap = pd.DataFrame({
        "PLAT": ["H1460UW"],
        "PERKIRAAN JENIS (DARI PLAT)": ["≈ Mobil penumpang (ESTIMASI PLAT)"],
        "ISI": ["3x"],
        "TOTAL VS KUOTA HARIAN": ["81 L / 299 L (batas terlonggar)"],
        "STATUS": ["Perlu Diperiksa"]
    })
    st.dataframe(df_rekap, use_container_width=True)

    st.markdown("### Detail Transaksi & Bukti CCTV")
    
    # Menampilkan baris detail transaksi lengkap dengan tombol aksi kamera/galeri di kolom pertama
    data_detail = [
        {
            "BUKTI CCTV": "📷 Kamera  📁 Galeri",
            "ID": "2305873",
            "WAKTU": "31/08/2026, 05:45:36",
            "PRODUCT / NOZZLE": "BIO_SOLAR (P3/H1)",
            "PLAT": "H1460UW",
            "VOLUME": "34.35L",
            "PERKIRAAN JENIS": "≈ Mobil penumpang (ESTIMASI PLAT)",
            "STATUS": "Perlu Diperiksa",
            "ALASAN TEMUAN": "Total harian 81.4L > jatah mobil pribadi (50L) — konfirmasi jenis"
        },
        {
            "BUKTI CCTV": "📷 Kamera  📁 Galeri",
            "ID": "2305876",
            "WAKTU": "31/08/2026, 05:48:55",
            "PRODUCT / NOZZLE": "BIO_SOLAR (P3/H1)",
            "PLAT": "H1460UW",
            "VOLUME": "17.65L",
            "PERKIRAAN JENIS": "≈ Mobil penumpang (ESTIMASI PLAT)",
            "STATUS": "Perlu Diperiksa",
            "ALASAN TEMUAN": "Total harian 81.4L > jatah mobil pribadi (50L) — konfirmasi jenis"
        }
    ]
    df_detail = pd.DataFrame(data_detail)
    st.dataframe(df_detail, use_container_width=True)

with tab2:
    st.info("Data untuk JBKP • Pertalite belum ditampilkan.")

# Footer Informasi Privasi & Pembuat
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>"
    "Analisis & foto berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun. Foto hilang bila halaman dimuat ulang.<br>"
    "Alat bantu penyaringan awal; setiap temuan wajib dikonfirmasi CCTV/SAMSAT sebelum tindakan."
    "</p>",
    unsafe_allow_html=True,
)

st.markdown(
    "<p style='text-align: center; font-size: 13px; font-weight: bold; margin-top: 15px;'>Made by Antoni - Area Business Head NTT</p>",
    unsafe_allow_html=True,
)
