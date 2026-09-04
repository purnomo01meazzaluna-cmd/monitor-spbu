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
    st.session_state.batas_JBT = 200.0
if 'batas_JBKP' not in st.session_state:
    st.session_state.batas_JBKP = 50.0
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
    # Dummy data lengkap dengan skenario anomali sesuai gambar referensi terbaru
    df_raw = pd.DataFrame({
        'ID': [2305921, 2305924, 2305963, 2305991, 2306012],
        'Date': [
            '31/08/2026, 07.42.06', '31/08/2026, 07.45.08', 
            '31/08/2026, 08.11.22', '31/08/2026, 08.31.01', '31/08/2026, 09.15.40'
        ],
        'Pu / H / Product': [
            'BIO_SOLAR (P3/H1)', 'BIO_SOLAR (P3/H1)', 
            'BIO_SOLAR (P3/H1)', 'BIO_SOLAR (P3/H1)', 'PERTALITE (P2/H1)'
        ],
        'Price': [6800, 6800, 6800, 6800, 10000],
        'Volume (L)': [22.06, 40.0, 7.36, 29.42, 15.0],
        'Value (Rp.)': [150000, 400000, 50000, 200000, 150000],
        'Payment': ['H8747IC', 'H8747IC', '- tanpa plat -', 'Z8782CQ', 'H8929KC']
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
    "📸 Evidence Monitoring & Anomali"
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
        st.session_state.batas_JBT = st.number_input("Batas JBT (L)", value=float(st.session_state.batas_JBT), step=10.0)
        st.session_state.batas_JBKP = st.number_input("Batas JBKP (L)", value=float(st.session_state.batas_JBKP), step=5.0)
        st.session_state.batas_R2 = st.number_input("Batas R2 (L)", value=float(st.session_state.batas_R2), step=1.0)

with tab4:
    st.subheader("📸 Evidence & Log Monitoring Anomali Transaksi")
    st.markdown("Tabel hasil analisis transaksi, dokumentasi bukti CCTV, serta alasan temuan anomali kuota harian sesuai standar.")
    
    # Header Tabel Analisis Evidence (ditambahkan kolom JUSTIFIKASI di sebelah kanan)
    ev_header_html = """
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; margin-bottom: 10px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; color: #64748b; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;">
        <div style="flex: 1.0;">BUKTI CCTV</div>
        <div style="flex: 0.8;">ID</div>
        <div style="flex: 1.2;">WAKTU</div>
        <div style="flex: 1.3;">PRODUCT / NOZZLE</div>
        <div style="flex: 1.0;">PLAT</div>
        <div style="flex: 0.8;">VOLUME</div>
        <div style="flex: 1.3;">PERKIRAAN JENIS</div>
        <div style="flex: 1.1;">STATUS</div>
        <div style="flex: 1.8;">ALASAN TEMUAN</div>
        <div style="flex: 1.8; padding-left: 5px;">JUSTIFIKASI</div>
    </div>
    """
    st.markdown(ev_header_html, unsafe_allow_html=True)

    if not df_filtered.empty:
        # Hitung akumulasi volume per plat
        agg_vol = df_filtered.groupby(col_nopol)[col_vol].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).to_dict()
        max_quota = st.session_state.batas_JBKP

        for index, row in df_filtered.iterrows():
            trx_id = str(row[col_id])
            waktu = str(row[col_date])
            prod = str(row[col_prod])
            plat = str(row[col_nopol])
            vol_val = pd.to_numeric(row[col_vol], errors='coerce')
            total_plat_vol = agg_vol.get(plat, vol_val)
            
            # Tentukan jenis kendaraan & alasan anomali
            if "- tanpa plat -" in plat:
                jenis_kendaraan = "—"
                status_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Perlu Diperiksa</span>"
                alasan = "Subsidi tanpa nopol — wajib dicatat per aturan"
            elif total_plat_vol > max_quota:
                jenis_kendaraan = "Mobil barang" if vol_val > 25 else "Mobil penumpang"
                status_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Perlu Diperiksa</span>"
                alasan = f"Total harian {total_plat_vol:.1f}L > jatah mobil pribadi ({max_quota:.0f}L) — konfirmasi jenis"
            else:
                jenis_kendaraan = "Mobil penumpang"
                status_html = "<span style='background-color: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Normal</span>"
                alasan = "Transaksi dalam batas wajar kuota harian"

            r_cols = st.columns([1.0, 0.8, 1.2, 1.3, 1.0, 0.8, 1.3, 1.1, 1.8, 1.8])
            
            with r_cols[0]:
                st.markdown("""
                    <div style="display: flex; flex-direction: column; gap: 3px;">
                        <span style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px; font-size: 0.65rem; color: #334155; text-align: center; cursor: pointer;">📷 Kamera</span>
                        <span style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px; font-size: 0.65rem; color: #334155; text-align: center; cursor: pointer;">📁 Galeri</span>
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
                if jenis_kendaraan != "—":
                    st.markdown(f"""
                        <div style="display: flex; flex-direction: column; gap: 2px;">
                            <span style="font-size: 0.75rem; color: #1e293b; font-weight: 500;">≈ {jenis_kendaraan}</span>
                            <span style="background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 3px; padding: 1px 4px; font-size: 0.6rem; color: #64748b; width: fit-content;">ESTIMASI PLAT</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='font-size: 0.75rem; color: #94a3b8;'>—</span>", unsafe_allow_html=True)
            with r_cols[7]:
                st.markdown(status_html, unsafe_allow_html=True)
            with r_cols[8]:
                st.markdown(f"<div style='background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 6px 8px; font-size: 0.7rem; color: #475569;'>{alasan}</div>", unsafe_allow_html=True)
            with r_cols[9]:
                st.text_input("Justifikasi", value="", key=f"justifikasi_{trx_id}", label_visibility="collapsed", placeholder="Isi catatan...")
    else:
        st.warning("Tidak ada data yang sesuai dengan filter pencarian.")

    st.markdown("---")
    st.markdown("##### 📝 Catatan Operasional / Laporan Shift")
    st.text_area("Catatan Shift", value="Pemantauan transaksi anomali dan verifikasi CCTV telah dilakukan sesuai prosedur HSSE.", key="catatan_shift_text")

    st.markdown("---")
    if not df_filtered.empty:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Laporan & Log Monitoring (.csv)",
            data=csv_data,
            file_name=f"Laporan_Evidence_SPBU_{selected_date}.csv",
            mime="text/csv",
            use_container_width=True
        )
