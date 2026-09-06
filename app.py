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

# Kondisi Default (Belum ada data yang dianalisis)
if uploaded_file is None:
    st.markdown(
        """
        <div style="border: 2px dashed #d6d8db; border-radius: 10px; padding: 40px; text-align: center; color: #6c757d; margin: 20px 0;">
            <h3>📋</h3>
            <p style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">Belum ada data yang dianalisis</p>
            <p style="font-size: 14px;">Upload satu file CSV/XLSX hose delivery (data kemarin) untuk mulai monitoring.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # Logika pembacaan file jika sudah diunggah
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"File '{uploaded_file.name}' berhasil dimuat!")
    st.dataframe(df, use_container_width=True)

# Footer Informasi Privasi & Alat Bantu
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>"
    "Analisis & foto berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun. Foto hilang bila halaman dimuat ulang.<br>"
    "Alat bantu penyaringan awal; setiap temuan wajib dikonfirmasi CCTV/SAMSAT sebelum tindakan."
    "</p>",
    unsafe_allow_html=True,
)

# Pembuat Aplikasi
st.markdown(
    "<p style='text-align: center; font-size: 13px; font-weight: bold; margin-top: 15px;'>Made by Antoni - Area Business Head NTT</p>",
    unsafe_allow_html=True,
)
