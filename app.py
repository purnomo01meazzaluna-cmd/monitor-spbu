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

# Sidebar untuk Filter / Upload Data & Pengaturan Dinamis
with st.sidebar:
    st.header("⚙️ Konfigurasi & Data")
    uploaded_file = st.file_uploader("Upload File Transaksi (.csv / .xlsx)", type=["csv", "xlsx"])
    selected_date = st.date_input("Pilih Tanggal Analisis", datetime.date(2026, 8, 31))
    
    st.markdown("---")
    st.subheader("🔍 Filter Interaktif")
    filter_produk = st.selectbox("Filter Berdasarkan Produk", ["Semua", "PERTALITE", "BIO_SOLAR"])
    search_nopol = st.text_input("Cari Nomor Polisi / Plat", "").strip().upper()

# Load Data (File Upload atau Dummy Sesuai Gambar Referensi)
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
    # Dummy data sesuai struktur gambar interaktif terbaru (ID, Date, Product, Price, Volume, Value, Payment/Nopol)
    df_raw = pd.DataFrame({
        'ID': [2305845, 2305873, 2305876, 2305877, 2305888, 2305894, 2305895, 2305917, 2305921, 2305924],
        'Date': [
            '2026-08-31 05:23:56', '2026-08-31 05:45:48', '2026-08-31 05:49:08', 
            '2026-08-31 05:58:04', '2026-08-31 07:12:46', '2026-08-31 07:18:47', 
            '2026-08-31 07:20:46', '2026-08-31 07:40:05', '2026-08-31 07:42:18', '2026-08-31 07:45:21'
        ],
        'Pu / H / Product': [
            '2 / 1 / PERTALITE', '3 / 1 / BIO_SOLAR', '3 / 1 / BIO_SOLAR', 
            '3 / 1 / BIO_SOLAR', '2 / 1 / PERTALITE', '2 / 1 / PERTALITE', 
            '3 / 1 / BIO_SOLAR', '3 / 1 / BIO_SOLAR', '3 / 1 / BIO_SOLAR', '3 / 1 / BIO_SOLAR'
        ],
        'Price': [10000, 6800, 6800, 6800, 10000, 10000, 6800, 6800, 6800, 10000],
        'Volume (L)': [10.0, 34.35, 17.65, 29.42, 23.0, 25.0, 11.77, 36.77, 22.06, 40.0],
        'Value (Rp.)': [100000, 233580, 120000, 200000, 230000, 250000, 80000, 250000, 150000, 400000],
        'Payment': ['H9638AV', 'H1460UW', 'H7257BC', 'H8652OV', 'H8728CC', 'AD8946MD', 'AD1178KH', 'H7309OQ', 'H8747IC', 'H8747IC']
    })

# Mapping kolom dinamis
col_id = 'ID' if 'ID' in df_raw.columns else df_raw.columns[0]
col_date = 'Date' if 'Date' in df_raw.columns else df_raw.columns[1]
col_prod = 'Pu / H / Product' if 'Pu / H / Product' in df_raw.columns else df_raw.columns[2]
col_price = 'Price' if 'Price' in df_raw.columns else df_raw.columns[3]
col_vol = 'Volume (L)' if 'Volume (L)' in df_raw.columns else df_raw.columns[4]
col_val = 'Value (Rp.)' if 'Value (Rp.)' in df_raw.columns else df_raw.columns[5]
col_nopol = 'Payment' if 'Payment' in df_raw.columns else df_raw.columns[6]

# Terapkan Filter Dinamis
df_filtered = df_raw.copy()
if filter_produk != "Semua":
    df_filtered = df_filtered[df_filtered[col_prod].str.contains(filter_produk, case=False, na=False)]
if search_nopol:
    df_filtered = df_filtered[df_filtered[col_nopol].str.contains(search_nopol, case=False, na=False)]

# Main Layout Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Ringkasan Transaksi", 
    "🔍 Detail & Filter Interaktif", 
    "⚙️ Pengaturan & Kuota", 
    "📸 Evidence Monitoring"
])

with tab1:
    st.subheader("📊 Ringkasan Transaksi Harian")
    st.markdown("Statistik umum, total volume, dan nilai transaksi secara dinamis.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transaksi", len(df_filtered))
    with col2:
        total_vol = pd.to_numeric(df_filtered[col_vol], errors='coerce').sum()
        st.metric("Total Volume", f"{total_vol:.2f} L")
    with col3:
        total_val_rp = pd.to_numeric(df_filtered[col_val], errors='coerce').sum()
        st.metric("Total Nilai", f"Rp {total_val_rp:,.0f}")
    with col4:
        st.metric("Status Sistem", "🟢 Normal / Online")

    st.markdown("---")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("🔍 Detail Kendaraan & Log Interaktif")
    st.markdown("Gunakan pencarian plat nomor atau filter produk di sidebar untuk melihat data secara spesifik.")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("⚙️ Pengaturan Batas Kuota Referensi Produk")
    st.markdown("Tentukan batas wajar harian untuk masing-masing kategori produk:")
    
    col_input, _ = st.columns([1, 2])
    with col_input:
        st.session_state.batas_JBT = st.number_input("Batas JBT (L)", value=float(st.session_state.batas_JBT), step=5.0)
        st.session_state.batas_JBKP = st.number_input("Batas JBKP (L)", value=float(st.session_state.batas_JBKP), step=5.0)
        st.session_state.batas_R2 = st.number_input("Batas R2 (L)", value=float(st.session_state.batas_R2), step=1.0)

with tab4:
    st.subheader("📸 Evidence & Log Monitoring Transaksi")
    st.markdown("Tabel hasil analisis transaksi, dokumentasi bukti CCTV, serta alasan temuan anomali kuota harian.")
    
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

    if not df_filtered.empty:
        agg_vol = df_filtered.groupby(col_nopol)[col_vol].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).to_dict()

        for index, row in df_filtered.iterrows():
            trx_id = str(row[col_id])
            waktu = str(row[col_date])
            prod = str(row[col_prod])
            plat = str(row[col_nopol])
            vol_val = pd.to_numeric(row[col_vol], errors='coerce')
            total_plat_vol = agg_vol.get(plat, vol_val)
            
            # Klasifikasi jenis kendaraan dinamis berdasarkan volume
            if vol_val > 40:
                jenis_kendaraan = "Bus / Truk"
            elif vol_val > 20:
                jenis_kendaraan = "Mobil barang"
            else:
                jenis_kendaraan = "Mobil penumpang"

            status_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Perlu Diperiksa</span>"
            alasan = f"Akumulasi {total_plat_vol:.1f}L terdeteksi pada plat {plat}"

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
                st.markdown(f"<span style='font-size: 0.75rem; font-weight: 500; color: #1e293b;'>{prod}</span>", unsafe_allow_html=True)
            with r_cols[4]:
                st.markdown(f"<span style='font-family: monospace; font-weight: 600; font-size: 0.8rem; color: #0f172a;'>{plat}</span>", unsafe_allow_html=True)
            with r_cols[5]:
                st.markdown(f"<span style='font-size: 0.8rem; font-weight: 600; color: #334155;'>{vol_val:.2f}L</span>", unsafe_allow_html=True)
            with r_cols[6]:
                st.markdown(f"<span style='font-size: 0.75rem; color: #1e293b; font-weight: 500;'>≈ {jenis_kendaraan}</span>", unsafe_allow_html=True)
            with r_cols[7]:
                st.markdown(status_html, unsafe_allow_html=True)
            with r_cols[8]:
                st.markdown(f"<div style='background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 4px 8px; font-size: 0.7rem; color: #475569;'>{alasan}</div>", unsafe_allow_html=True)
            with r_cols[9]:
                st.text_input("Justifikasi", value="", key=f"justifikasi_{trx_id}", label_visibility="collapsed", placeholder="Isi catatan...")
    else:
        st.warning("Tidak ada data yang sesuai dengan filter pencarian.")

    st.markdown("---")
    st.markdown("##### 📝 Catatan Operasional / Laporan Shift")
    st.text_area("Catatan Shift", value="Pemantauan transaksi berjalan lancar dengan filter dinamis aktif.", key="catatan_shift_text")

    st.markdown("---")
    if not df_filtered.empty:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Laporan Terfiltrasi (.csv)",
            data=csv_data,
            file_name=f"Laporan_SPBU_Filter_{selected_date}.csv",
            mime="text/csv",
            use_container_width=True
        )
