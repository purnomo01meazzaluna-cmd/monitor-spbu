import streamlit as st
import pandas as pd
import numpy as np

# Konfigurasi Halaman
st.set_page_config(
    page_title="Monitoring SPBU",
    page_icon="⛽",
    layout="wide"
)

# Judul Aplikasi
st.title("⛽ Dashboard Monitoring SPBU")
st.markdown("---")

# Sidebar untuk navigasi atau filter
st.sidebar.header("Filter Data")
pilihan_menu = st.sidebar.selectbox(
    "Pilih Menu",
    ["Ringkasan Transaksi", "Monitoring CCTV", "Pengaturan"]
)

# Konten Utama Berdasarkan Menu
if pilihan_menu == "Ringkasan Transaksi":
    st.subheader("Data Transaksi & Volume Penjualan")
    
    # Contoh data dummy untuk tabel monitoring
    data_dummy = {
        "KODE": ["K001", "K002", "K003"],
        "JENIS": ["Roda 4 Pribadi (JBT)", "Roda 2", "Kendaraan Umum"],
        "VOLUME": ["45.35L", "10.0L", "25.5L"],
        "STATUS": ["Aman", "Perlu Perhatian", "Aman"]
    }
    df = pd.DataFrame(data_dummy)
    st.dataframe(df, use_container_width=True)

elif pilihan_menu == "Monitoring CCTV":
    st.subheader("Live Feed CCTV Area Pompa & Dispenser")
    col1, col2 = st.columns(2)
    with col1:
        st.info("Kamera 1 - Jalur Roda 4")
        st.write("[Feed CCTV Aktif]")
    with col2:
        st.info("Kamera 2 - Jalur Motor")
        st.write("[Feed CCTV Aktif]")

else:
    st.subheader("Pengaturan Sistem")
    st.write("Konfigurasi parameter ambang batas dan koneksi database.")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>Analisis berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun.</p>",
    unsafe_allow_html=True,
)
