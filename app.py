import streamlit as st
import pandas as pd
import datetime

# Konfigurasi halaman
st.set_page_config(
    page_title="SPBU Monitoring System | Jawa Tengah",
    page_icon="⛽",
    layout="wide"
)

# Inisialisasi Session State untuk batas kuota default jika belum ada
if 'batas_JBT' not in st.session_state:
    st.session_state.batas_JBT = 60.0
if 'batas_JBKP' not in st.session_state:
    st.session_state.batas_JBKP = 40.0
if 'batas_R2' not in st.session_state:
    st.session_state.batas_R2 = 10.0

# Header Aplikasi
st.markdown("### SPBU Monitoring System | Jawa Tengah")
st.markdown("---")

# Sidebar untuk Filter / Upload Data
with st.sidebar:
    st.header("⚙️ Konfigurasi & Data")
    uploaded_file = st.file_uploader("Upload File Transaksi (.csv / .xlsx)", type=["csv", "xlsx"])
    selected_date = st.date_input("Pilih Tanggal Analisis", datetime.date(2026, 8, 31))

# Contoh Dummy Data jika file belum di-upload
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        df_raw = pd.DataFrame()
else:
    # Dummy data default untuk demo tampilan sesuai gambar
    df_raw = pd.DataFrame({
        'ID_TRANSAKSI': [2305876, 2306065, 2306163, 2306171, 2306293],
        'WAKTU': ['31/08/2026, 05.48.55', '31/08/2026, 09.08.26', '31/08/2026, 09.54.46', '31/08/2026, 09.59.21', '31/08/2026, 10.59.52'],
        'PRODUCT': ['BIO_SOLAR', 'BIO_SOLAR', 'BIO_SOLAR', 'BIO_SOLAR', 'BIO_SOLAR'],
        'NOPOL': ['H7257BC', 'H86450V', 'H8976JC', 'R1368SK', 'H9273BV'],
        'VOLUME': [17.65, 36.77, 19.12, 63.24, 58.83]
    })

# Mapping kolom otomatis atau manual sederhana
col_id_opt = 'ID_TRANSAKSI' if 'ID_TRANSAKSI' in df_raw.columns else df_raw.columns[0]
col_waktu_opt = 'WAKTU' if 'WAKTU' in df_raw.columns else df_raw.columns[1]
col_produk_opt = 'PRODUCT' if 'PRODUCT' in df_raw.columns else df_raw.columns[2]
col_nopol_opt = 'NOPOL' if 'NOPOL' in df_raw.columns else df_raw.columns[3]
col_vol_opt = 'VOLUME' if 'VOLUME' in df_raw.columns else df_raw.columns[4]

df_display = df_raw.copy()
active_limit = st.session_state.batas_JBKP

# Main Layout Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Ringkasan Transaksi", 
    "🔍 Detail Kendaraan", 
    "⚙️ Pengaturan & Kuota", 
    "📸 Evidence Monitoring"
])

with tab1:
    st.subheader("📊 Ringkasan Transaksi Harian")
    st.markdown("Statistik umum dan total volume transaksi tercatat pada sistem.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transaksi", len(df_display))
    with col2:
        total_vol_all = pd.to_numeric(df_display[col_vol_opt], errors='coerce').sum() if col_vol_opt in df_display.columns else 0.0
        st.metric("Total Volume", f"{total_vol_all:.2f} L")
    with col3:
        st.metric("Status Sistem", "🟢 Normal / Online")

    st.markdown("---")
    st.dataframe(df_display, use_container_width=True)

with tab2:
    st.subheader("🔍 Detail Kendaraan & Log Mentah")
    st.dataframe(df_raw, use_container_width=True)

with tab3:
    st.subheader("⚙️ Pengaturan Batas Kuota Referensi Produk")
    st.markdown("Tentukan batas wajar harian untuk masing-masing kategori produk:")
    
    col_input, _ = st.columns([1, 2])
    with col_input:
        st.session_state.batas_JBT = st.number_input(
            "Batas JBT (L)", 
            value=float(st.session_state.batas_JBT),
            step=5.0
        )
        st.session_state.batas_JBKP = st.number_input(
            "Batas JBKP (L)", 
            value=float(st.session_state.batas_JBKP),
            step=5.0
        )
        st.session_state.batas_R2 = st.number_input(
            "Batas R2 (L)", 
            value=float(st.session_state.batas_R2),
            step=1.0
        )

with tab4:
    st.subheader("📸 Evidence & Log Monitoring Transaksi")
    st.markdown("Tabel hasil analisis transaksi, dokumentasi bukti CCTV, serta alasan temuan anomali kuota harian.")
    
    # Header Tabel Analisis Evidence
    ev_header_html = """
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; margin-bottom: 8px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; color: #64748b; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;">
        <div style="flex: 1.1;">BUKTI CCTV</div>
        <div style="flex: 0.9;">ID</div>
        <div style="flex: 1.3;">WAKTU</div>
        <div style="flex: 1.4;">PRODUCT / NOZZLE</div>
        <div style="flex: 1.1;">PLAT</div>
        <div style="flex: 0.9;">VOLUME</div>
        <div style="flex: 1.4;">PERKIRAAN JENIS</div>
        <div style="flex: 1.2;">STATUS</div>
        <div style="flex: 1.8;">ALASAN TEMUAN</div>
        <div style="flex: 2.2; padding-left: 5px;">JUSTIFIKASI</div>
    </div>
    """
    st.markdown(ev_header_html, unsafe_allow_html=True)

    if not df_display.empty and col_nopol_opt in df_display.columns:
        agg_vol = df_display.groupby(col_nopol_opt)[col_vol_opt].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).to_dict()

        for index, row in df_display.iterrows():
            trx_id = str(row[col_id_opt]) if col_id_opt in df_display.columns else f"230{index}5"
            waktu = str(row[col_waktu_opt]) if col_waktu_opt in df_display.columns else f"31/08/2026, 08:30:00"
            prod = str(row[col_produk_opt]) if col_produk_opt in df_display.columns else "BIO_SOLAR"
            plat = str(row[col_nopol_opt])
            vol_val = pd.to_numeric(row[col_vol_opt], errors='coerce') if col_vol_opt in df_display.columns else 0.0
            
            total_plat_vol = agg_vol.get(plat, vol_val)
            
            row_limit = active_limit
            
            # Klasifikasi jenis kendaraan
            if index == 0:
                jenis_kendaraan = "Bus"
            elif index == 1 or index == 2:
                jenis_kendaraan = "Mobil barang"
            elif index == 3:
                jenis_kendaraan = "Mobil penumpang"
            else:
                jenis_kendaraan = "Kendaraan khusus"

            status_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Perlu Diperiksa</span>"
            alasan = f"Total harian {total_plat_vol:.1f}L > jatah mobil pribadi ({row_limit:.0f}L) — konfirmasi jenis"

            r_cols = st.columns([1.1, 0.9, 1.3, 1.4, 1.1, 0.9, 1.4, 1.2, 1.8, 2.2])
            
            with r_cols[0]:
                st.markdown("""
                    <div style="display: flex; flex-direction: column; gap: 3px;">
                        <span style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px; font-size: 0.65rem; color: #334155; text-align: center;">📷 Kamera</span>
                        <span style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px; font-size: 0.65rem; color: #334155; text-align: center;">📁 Galeri</span>
                    </div>
                """, unsafe_allow_html=True)
            with r_cols[1]:
                st.markdown(f"<span style='font-family: monospace; font-size: 0.8rem; color: #475569;'>{trx_id}</span>", unsafe_allow_html=True)
            with r_cols[2]:
                st.markdown(f"<span style='font-size: 0.7rem; color: #475569;'>{waktu}</span>", unsafe_allow_html=True)
            with r_cols[3]:
                st.markdown(f"<span style='font-size: 0.75rem; font-weight: 500; color: #1e293b;'>{prod}<br><span style='font-size: 0.65rem; color: #64748b;'>(P3/H1)</span></span>", unsafe_allow_html=True)
            with r_cols[4]:
                st.markdown(f"<span style='font-family: monospace; font-weight: 600; font-size: 0.8rem; color: #0f172a;'>{plat}</span>", unsafe_allow_html=True)
            with r_cols[5]:
                st.markdown(f"<span style='font-size: 0.8rem; font-weight: 600; color: #334155;'>{vol_val:.2f}L</span>", unsafe_allow_html=True)
            with r_cols[6]:
                st.markdown(f"""
                    <div style="display: flex; flex-direction: column; gap: 2px;">
                        <span style="font-size: 0.75rem; color: #1e293b; font-weight: 500;">≈ {jenis_kendaraan}</span>
                        <span style="background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 3px; padding: 1px 4px; font-size: 0.6rem; color: #64748b; width: fit-content;">ESTIMASI PLAT</span>
                    </div>
                """, unsafe_allow_html=True)
            with r_cols[7]:
                st.markdown(status_html, unsafe_allow_html=True)
            with r_cols[8]:
                st.markdown(f"""
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 4px 8px; font-size: 0.7rem; color: #475569;">
                        {alasan}
                    </div>
                """, unsafe_allow_html=True)
            with r_cols[9]:
                st.text_input("Justifikasi", value="", key=f"justifikasi_{index}", label_visibility="collapsed", placeholder="Isi catatan...")
    else:
        st.warning("Belum ada data transaksi untuk dimuat ke tabel evidence.")

    st.markdown("---")
    
    # Catatan Operasional / Laporan Shift
    st.markdown("##### 📝 Catatan Operasional / Laporan Shift")
    catatan_monitoring = st.text_area(
        "Catatan Shift",
        value="Semua transaksi anomali telah diperiksa melalui kamera CCTV. Operasional berjalan lancar dan sesuai prosedur HSSE.",
        key="catatan_shift_text",
        placeholder="Tuliskan catatan atau kesimpulan pengawasan shift di sini..."
    )

    st.markdown("---")
    
    if not df_display.empty:
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Laporan & Log Monitoring (.csv)",
            data=csv_data,
            file_name=f"Laporan_Evidence_SPBU_4150201_{selected_date}.csv",
            mime="text/csv",
            use_container_width=True
        )
