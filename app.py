import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="SPBU 4150201 - Monitoring & Investigasi Transaksi",
    page_icon="⛽",
    layout="wide"
)

# Inisialisasi Database SQLite
DB_FILE = "spbu_monitoring.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaksi_investigasi (
            trans_id TEXT PRIMARY KEY,
            tanggal TEXT,
            nozzle TEXT,
            produk TEXT,
            plat TEXT,
            volume REAL,
            status_anomali TEXT,
            hasil_monitoring TEXT,
            catatan TEXT,
            link_foto TEXT,
            link_cctv TEXT
        )
    ''')
    
    # Masukkan data dummy awal jika tabel masih kosong
    cursor.execute("SELECT COUNT(*) FROM transaksi_investigasi")
    if cursor.fetchone()[0] == 0:
        dummy_data = [
            ("2301755", "2026-08-31 05:45:48", "Nozzle 3 / 1", "BIO_SOLAR", "2305873", 34.35, "Normal", "Volume wajar untuk kendaraan niaga/pribadi. Jeda aman dari transaksi berikutnya.", "", "foto_2301755.jpg", "cctv_2301755.mp4"),
            ("2302755", "2026-08-31 05:49:08", "Nozzle 3 / 1", "BIO_SOLAR", "2305876", 17.65, "Normal", "Pengisian parsial terpantau. Plat nomor berbeda dengan transaksi sebelumnya (aman dari anomali helikopter).", "", "foto_2302755.jpg", "cctv_2302755.mp4"),
            ("2303891", "2026-08-31 08:12:30", "Nozzle 1 / 2", "PERTALITE", "H 1234 ABC", 20.00, "Normal", "Transaksi Pertalite non-subsidi dalam batas normal.", "", "foto_2303891.jpg", "cctv_2303891.mp4"),
            ("2304102", "2026-08-31 09:30:15", "Nozzle 2 / 1", "BIO_SOLAR", "H 9999 XYZ", 45.50, "Perlu Pengecekan", "Volume mendekati batas maksimum sekali isi. Perlu verifikasi barcode subsidi.", "Indikasi pengisian berulang dalam 1 jam", "foto_2304102.jpg", "cctv_2304102.mp4")
        ]
        cursor.executemany('''
            INSERT OR IGNORE INTO transaksi_investigasi 
            (trans_id, tanggal, nozzle, produk, plat, volume, status_anomali, hasil_monitoring, catatan, link_foto, link_cctv)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', dummy_data)
        conn.commit()
    conn.close()

init_db()

def load_all_from_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM transaksi_investigasi ORDER BY tanggal DESC", conn)
    conn.close()
    return df

# Header Utama Dashboard
st.markdown("## ⛽ DASHBOARD MONITORING & PENGAWASAN SPBU 4150201 SEMARANG")
st.markdown("Sistem Pengawasan Operasional Non-Fuel Retail, Nozzle, dan Transaksi BBM Subsidi.")

# State untuk pencarian
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# Sidebar Navigasi & Filter
st.sidebar.header("🎛️ Panel Kontrol & Filter")
st.sidebar.markdown("---")
st.session_state.search_query = st.sidebar.text_input("🔍 Cari Nomor Plat / ID Transaksi", value=st.session_state.search_query)

if st.sidebar.button("🔄 Segarkan Data Database"):
    st.rerun()

# Layout Utama dengan Tab
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan & Statistik", "🔍 Detail Transaksi & Catatan Evidens", "📁 Ekspor Data & Laporan"])

df_current = load_all_from_db()
if st.session_state.search_query.strip():
    q = st.session_state.search_query.strip().upper()
    df_current = df_current[df_current['plat'].str.upper().str.contains(q, na=False) | df_current['trans_id'].str.contains(q, na=False)]

with tab1:
    st.subheader("📈 Ringkasan Kinerja Transaksi SPBU")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    total_trx = len(df_current)
    total_vol = df_current['volume'].sum() if total_trx > 0 else 0
    normal_count = len(df_current[df_current['status_anomali'] == 'Normal'])
    check_count = total_trx - normal_count

    col_m1.metric("Total Transaksi Tampil", f"{total_trx}")
    col_m2.metric("Total Volume Penyaluran", f"{total_vol:.2f} Liter")
    col_m3.metric("Status Normal", f"{normal_count}")
    col_m4.metric("Perlu Investigasi", f"{check_count}", delta_color="inverse")

    st.markdown("---")
    st.markdown("### Distribusi Volume Berdasarkan Produk")
    if not df_current.empty:
        prod_grouped = df_current.groupby('produk')['volume'].sum().reset_index()
        st.bar_chart(prod_grouped.set_index('produk'))
    else:
        st.info("Tidak ada data untuk ditampilkan pada grafik.")

with tab2:
    st.subheader("📝 Detail Transaksi, Hasil Monitoring & Catatan Investigasi")
    st.markdown("Setiap transaksi dilengkapi **Hasil Monitoring Otomatis** serta kolom **Catatan Pengawas** yang tersimpan permanen.")

    if not df_current.empty:
        for idx, row in df_current.iterrows():
            trans_id = row['trans_id']
            waktu_val = row['tanggal']
            produk_val = row['produk']
            nozzle_val = row['nozzle']
            plat_val = row['plat']
            vol_val = f"{row['volume']}L"
            status_anom = row['status_anomali']
            hasil_mon = row['hasil_monitoring']
            saved_note = row['catatan']
            foto_link = row['link_foto']
            cctv_link = row['link_cctv']

            col_card_1, col_card_2, col_card_3, col_card_4, col_card_5, col_card_6 = st.columns([1.2, 1.1, 1.5, 1.5, 1.2, 1.1])
            
            with col_card_1:
                if st.button("📷 Kamera", key=f"cam_{trans_id}"):
                    st.toast(f"Membuka rekaman CCTV [{cctv_link}]")
                if st.button("📁 Galeri", key=f"gal_{trans_id}"):
                    st.toast(f"Menampilkan foto plat [{foto_link}]")
            with col_card_2:
                st.markdown(f"**ID**\n`{trans_id}`")
            with col_card_3:
                st.markdown(f"**Waktu**\n{waktu_val}")
            with col_card_4:
                st.markdown(f"**Produk**\n{produk_val}\n`(Nozzle: {nozzle_val})`")
            with col_card_5:
                st.markdown(f"**Plat**\n**`{plat_val}`**")
            with col_card_6:
                st.markdown(f"**Volume**\n`{vol_val}`")
            
            # Baris Keterangan Status & Hasil Monitoring Otomatis
            col_info_1, col_info_2 = st.columns([2, 4])
            with col_info_1:
                if status_anom != "Normal":
                    st.error(f"⚠️ {status_anom}")
                else:
                    st.success("● Normal")
            with col_info_2:
                st.info(f"📊 **Hasil Monitoring:** {hasil_mon}")

            # Baris Kolom Catatan / Notes Manual Pengawas
            new_note = st.text_input(
                f"Catatan / Notes Investigasi Pengawas #{trans_id}", 
                value=saved_note, 
                placeholder="✏️ Tulis catatan atau tindak lanjut pengawas di sini...",
                key=f"note_db_{trans_id}"
            )
            if new_note != saved_note:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE transaksi_investigasi SET catatan = ? WHERE trans_id = ?", (new_note, trans_id))
                conn.commit()
                conn.close()
                st.toast(f"Catatan untuk transaksi {trans_id} berhasil disimpan!")
            
            st.markdown("---")
    else:
        st.info("Tidak ada data transaksi yang ditemukan.")

with tab3:
    st.subheader("📁 Ekspor Laporan & Database Monitoring")
    st.markdown("Unduh seluruh data transaksi lengkap beserta hasil monitoring sistem dan catatan pengawas dalam format Excel.")

    df_full_export = load_all_from_db()
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_full_export.to_excel(writer, index=False, sheet_name='Monitoring_SPBU')
    excel_data = output.getvalue()

    file_name = f"Laporan_Monitoring_SPBU_4150201_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    st.download_button(
        label="📥 Unduh Laporan Excel (Termasuk Hasil Monitoring & Notes)",
        data=excel_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("### Pratinjau Data di Database")
    st.dataframe(df_full_export, use_container_width=True)
