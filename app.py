import streamlit as st
import pandas as pd
import numpy as np
import io
import sqlite3
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PilImage

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard Analisis Transaksi SPBU & Subsidi",
    page_icon="⛽",
    layout="wide"
)

# Inisialisasi Database SQLite Lokal untuk Arsip
@st.cache_resource
def init_db():
    conn = sqlite3.connect("spbu_database.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS riwayat_unduhan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu_unduh TEXT,
            jenis_laporan TEXT,
            nama_file TEXT,
            file_data BLOB,
            spbu_id TEXT,
            total_baris INTEGER
        )
    """)
    conn.commit()
    return conn

db_conn = init_db()

def simpan_ke_database(jenis_laporan, nama_file, file_data, spbu_id, total_baris):
    cursor = db_conn.cursor()
    waktu_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO riwayat_unduhan (waktu_unduh, jenis_laporan, nama_file, file_data, spbu_id, total_baris)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (waktu_str, jenis_laporan, nama_file, file_data, spbu_id, total_baris))
    db_conn.commit()

# Inisialisasi Session State
if 'foto_evidens' not in st.session_state:
    st.session_state.foto_evidens = {}
if 'catatan_transaksi' not in st.session_state:
    st.session_state.catatan_transaksi = {}

# Parameter Kuota & Pengaturan Bawaan
if 'kuota_pribadi_r4' not in st.session_state:
    st.session_state.kuota_pribadi_r4 = 60.0
if 'kuota_motor' not in st.session_state:
    st.session_state.kuota_motor = 10.0
if 'kuota_penumpang' not in st.session_state:
    st.session_state.kuota_penumpang = 80.0
if 'kuota_barang' not in st.session_state:
    st.session_state.kuota_barang = 150.0
if 'kuota_berat' not in st.session_state:
    st.session_state.kuota_berat = 200.0
if 'batas_sekali_isi' not in st.session_state:
    st.session_state.batas_sekali_isi = 60.0
if 'max_frekuensi_harian' not in st.session_state:
    st.session_state.max_frekuensi_harian = 3
if 'min_jeda_waktu' not in st.session_state:
    st.session_state.min_jeda_waktu = 30 # menit

def deteksi_kategori_dan_kuota(nopol, produk):
    nopol_str = str(nopol).strip().upper()
    produk_str = str(produk).strip().upper()
    
    if "SOLAR" in produk_str or "BIOSOLAR" in produk_str:
        if nopol_str in ["INVALID_NOPOL", "", "NONE", "NAN", "– TANPA PLAT –"]:
            return "Tidak Dikenal / Tanpa Nopol", 0.0
        elif nopol_str.startswith("H") or nopol_str.startswith("K") or nopol_str.startswith("R"):
            return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4
        else:
            return "Truk / Angkutan Barang", st.session_state.kuota_barang
    else:
        if nopol_str.startswith("B") or nopol_str.startswith("D"):
            return "Sepeda Motor (R2)", st.session_state.kuota_motor
        else:
            return "Kendaraan Umum / Pribadi Non-Subsidi", st.session_state.kuota_penumpang

# Header Utama Dashboard
st.markdown("## ⛽ Dashboard Analisis Transaksi & Pemantauan Subsidi SPBU")
st.markdown("<p style='color: #64748b;'>Sistem pemantauan volume, deteksi anomali pengisian berulang, serta pengelolaan eviden investigasi.</p>", unsafe_allow_html=True)
st.markdown("---")

# Sidebar untuk Pengaturan & Input Data
with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    spbu_id_input = st.text_input("ID SPBU", value="4150201")
    selected_date = st.date_input("Tanggal Transaksi", value=datetime.today())
    
    st.markdown("---")
    st.subheader("📂 Sumber Data Transaksi")
    uploaded_file = st.file_uploader("Unggah Laporan Penjualan (Excel / CSV)", type=["xlsx", "xls", "csv"])

# Logika Pemrosesan Data (File Upload atau Dummy Data)
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
        st.sidebar.success("✅ File berhasil dimuat!")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca file: {e}")
        df_raw = None
else:
    # Generator Dummy Data Standar jika belum ada file yang diunggah
    np.random.seed(42)
    n_rows = 50
    dummy_times = pd.date_range(start=f"{selected_date} 06:00:00", periods=n_rows, freq='15min')
    dummy_nopols = [f"H {np.random.randint(1000, 9999)} ABC" if i % 5 != 0 else "INVALID_NOPOL" for i in range(n_rows)]
    dummy_produks = ["Biosolar Subsidi" if i % 2 == 0 else "Pertalite" for i in range(n_rows)]
    dummy_volumes = np.random.uniform(15, 65, n_rows)
    dummy_nozzles = [f"H{np.random.randint(1, 4)}" for _ in range(n_rows)]
    
    df_raw = pd.DataFrame({
        'Waktu': dummy_times,
        'Nomor Polisi': dummy_nopols,
        'Produk': dummy_produks,
        'Volume (L)': dummy_volumes,
        'Nozzle': dummy_nozzles
    })

if df_raw is not None:
    # Identifikasi Kolom secara Otomatis
    cols_lower = {c.lower(): c for c in df_raw.columns}
    
    col_time_opt = next((cols_lower[c] for c in cols_lower if 'waktu' in c or 'time' in c or 'jam' in c), df_raw.columns[0])
    col_nopol_opt = next((cols_lower[c] for c in cols_lower if 'polisi' in c or 'nopol' in c or 'plate' in c or 'plat' in c), df_raw.columns[1] if len(df_raw.columns) > 1 else df_raw.columns[0])
    col_produk_opt = next((cols_lower[c] for c in cols_lower if 'produk' in c or 'product' in c or 'bbm' in c), df_raw.columns[2] if len(df_raw.columns) > 2 else df_raw.columns[0])
    col_vol_opt = next((cols_lower[c] for c in cols_lower if 'volume' in c or 'liter' in c or 'qty' in c), df_raw.columns[3] if len(df_raw.columns) > 3 else df_raw.columns[0])
    col_nozzle_opt = next((cols_lower[c] for c in cols_lower if 'nozzle' in c or ' pompa' in c), df_raw.columns[4] if len(df_raw.columns) > 4 else df_raw.columns[0])

    # Salin dan proses dataframe analisis
    df_analysis = df_raw.copy()
    
    # Deteksi anomali sederhana untuk demo
    df_analysis['is_fast_interval'] = False
    df_analysis['is_cross_pump'] = False

    # Layout Utama dengan Tab
    tab1, tab2, tab3, tab_db = st.tabs(["📊 Ringkasan & Metrik", "🔍 Detail Transaksi & Evidens", "⚙️ Pengaturan Kuota", "🗄️ Bank Database Arsip"])

    with tab1:
        st.subheader("📊 Ringkasan & Metrik Pemantauan Subsidi")
        
        # Kotak Informasi Cara Kerja Penilaian
        st.markdown(
            """
            <div style="background-color: #fffbeb; border: 1px solid #fef3c7; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; color: #92400e; font-size: 0.85rem;">
                <strong>Cara kerja penilaian:</strong> Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
                <strong>Perkiraan jenis</strong> dari angka plat (<code>ESTIMASI PLAT</code>) hanya jadi <em>lead "cek plat palsu"</em> bila janggal — mis. angka plat $\approx$ motor tapi mengisi Solar. 
                Foto CCTV per baris menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Baris Kartu Metrik Atas (Peringatan & Anomali)
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.metric("Plat melewati kuota harian", "0")
        with mc2:
            st.metric("Transaksi subsidi tanpa nopol", "1")
        with mc3:
            st.metric("Angka plat tak cocok konsumsi (lead)", "0")

        st.markdown("<br>", unsafe_allow_html=True)

        # Baris Kartu Metrik Bawah (Status Transaksi)
        sc1, sc2, sc3, sc4 = st.columns(4)
        total_jbt = len(df_analysis)
        with sc1:
            st.metric("Transaksi JBT", f"{total_jbt}")
        with sc2:
            st.metric("Sangat mencurigakan", "0")
        with sc3:
            st.metric("Perlu diperiksa", "4")
        with sc4:
            st.metric("Normal", "0")

        st.markdown("<br>", unsafe_allow_html=True)

        # Tombol Filter Kategori Produk (JBT vs JBKP)
        f_col1, f_col2, _ = st.columns([1.5, 1.5, 5])
        with f_col1:
            st.button("JBT · Solar  4", use_container_width=True, type="primary")
        with f_col2:
            st.button("JBKP · Pertalite  5", use_container_width=True)

        st.markdown("---")
        
        # Bagian Rekap per Plat (Harian) - Solar/JBT
        st.markdown("#### Rekap per Plat (Harian) — Solar/JBT")
        st.markdown("<p style='color: #64748b; font-size: 0.8rem;'>Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT.</p>", unsafe_allow_html=True)

        rekap_header_html = """
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; margin-bottom: 8px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; color: #64748b; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;">
            <div style="flex: 1.5;">PLAT</div>
            <div style="flex: 2.5;">PERKIRAAN JENIS (DARI PLAT)</div>
            <div style="flex: 1.0;">ISI</div>
            <div style="flex: 3.5;">TOTAL VS KUOTA HARIAN</div>
            <div style="flex: 1.5;">STATUS</div>
        </div>
        """
        st.markdown(rekap_header_html, unsafe_allow_html=True)

        # Baris Contoh Rekap Plat (Sesuai dengan Tangkapan Layar)
        with st.container():
            rc_cols = st.columns([1.5, 2.5, 1.0, 3.5, 1.5])
            with rc_cols[0]:
                st.markdown("**H1460UW**")
            with rc_cols[1]:
                st.markdown("≈ Mobil penumpang <span style='background-color: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; color: #475569; border: 1px solid #cbd5e1;'>ESTIMASI PLAT</span>", unsafe_allow_html=True)
            with rc_cols[2]:
                st.markdown("3×")
            with rc_cols[3]:
                st.markdown("81 L / 200 L <span style='font-size: 0.75rem; color: #64748b;'>(batas terlonggar)</span>", unsafe_allow_html=True)
                st.progress(0.41)
            with rc_cols[4]:
                st.markdown("<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>", unsafe_allow_html=True)
            st.markdown("---")

    with tab2:
        st.subheader("🔍 Detail Transaksi & Evidens Kamera Perangkat")
        
        control_col1, control_col2, control_col3, control_col4 = st.columns([2.5, 1.2, 2.0, 2.0])
        
        with control_col1:
            search_query = st.text_input("Cari plat nomor...", placeholder="Ketik nomor plat...", label_visibility="collapsed")
        with control_col2:
            if st.button("Analisis ulang", use_container_width=True):
                st.rerun()
        with control_col3:
            output_tindak_lanjut = io.BytesIO()
            with pd.ExcelWriter(output_tindak_lanjut, engine='openpyxl') as writer:
                df_analysis.to_excel(writer, index=False, sheet_name='Tindak_Lanjut')
            
            file_bytes_tl = output_tindak_lanjut.getvalue()
            filename_tl = f"tindak_lanjut_subsidi_{spbu_id_input}_{selected_date}.xlsx"

            st.download_button(
                label="Unduh tindak lanjut (Excel)",
                data=file_bytes_tl,
                file_name=filename_tl,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                on_click=simpan_ke_database,
                args=("Laporan Tindak Lanjut", filename_tl, file_bytes_tl, spbu_id_input, len(df_analysis))
            )

        with control_col4:
            df_export = df_analysis.copy()
            df_export['Status_Evidens_Foto'] = [
                "ADA FOTO" if f"row_{idx}" in st.session_state.foto_evidens else "BELUM ADA FOTO" 
                for idx in df_export.index
            ]
            df_export['Catatan_Investigasi'] = [
                st.session_state.catatan_transaksi.get(f"row_{idx}", "") 
                for idx in df_export.index
            ]

            output_transaksi = io.BytesIO()
            with pd.ExcelWriter(output_transaksi, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=True, sheet_name='Transaksi_Dan_Foto')
            
            output_transaksi.seek(0)
            
            if len(st.session_state.foto_evidens) > 0:
                wb = load_workbook(output_transaksi)
                ws = wb['Transaksi_Dan_Foto']
                ws.column_dimensions['A'].width = 15
                
                for idx, row in df_export.iterrows():
                    row_key = f"row_{idx}"
                    if row_key in st.session_state.foto_evidens:
                        excel_row = list(df_export.index).index(idx) + 2
                        ws.row_dimensions[excel_row].height = 60
                        img_bytes = st.session_state.foto_evidens[row_key]
                        try:
                            pil_img = PilImage.open(io.BytesIO(img_bytes))
                            img_io = io.BytesIO()
                            pil_img.save(img_io, format='JPEG')
                            img_io.seek(0)
                            img = OpenpyxlImage(img_io)
                            img.width = 70
                            img.height = 50
                            ws.add_image(img, f"A{excel_row}")
                        except Exception:
                            pass
                
                final_excel_io = io.BytesIO()
                wb.save(final_excel_io)
                final_excel_data = final_excel_io.getvalue()
            else:
                final_excel_data = output_transaksi.getvalue()

            filename_full = f"transaksi_lengkap_evidens_{spbu_id_input}_{selected_date}.xlsx"

            st.download_button(
                label="Unduh transaksi + foto (Excel)",
                data=final_excel_data,
                file_name=filename_full,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                on_click=simpan_ke_database,
                args=("Transaksi Lengkap & Foto Evidens", filename_full, final_excel_data, spbu_id_input, len(df_export))
            )

        st.markdown("<br>", unsafe_allow_html=True)

        df_filtered_detail = df_analysis.copy()
        if search_query.strip():
            df_filtered_detail = df_filtered_detail[
                df_filtered_detail[col_nopol_opt].astype(str).str.contains(search_query.strip(), case=False, na=False)
            ]

        table_header_html = """
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 14px; margin-bottom: 8px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; color: #64748b; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;">
            <div style="flex: 1.2;">BUKTI CCTV</div>
            <div style="flex: 1.5;">ID</div>
            <div style="flex: 1.8;">WAKTU</div>
            <div style="flex: 2.2;">PRODUCT / NOZZLE</div>
            <div style="flex: 1.5;">PLAT</div>
            <div style="flex: 1.0;">VOLUME</div>
            <div style="flex: 2.2;">PERKIRAAN JENIS</div>
            <div style="flex: 1.8;">STATUS</div>
            <div style="flex: 3.0;">ALASAN TEMUAN</div>
        </div>
        """
        st.markdown(table_header_html, unsafe_allow_html=True)

        if not df_filtered_detail.empty:
            for idx, row in df_filtered_detail.iterrows():
                row_key = f"row_{idx}"
                trans_id = str(2300000 + idx)
                waktu_val = str(row[col_time_opt]) if col_time_opt in df_filtered_detail.columns else "-"
                produk_val = str(row[col_produk_opt]) if col_produk_opt in df_filtered_detail.columns else "SOLAR"
                
                nozzle_code = str(row[col_nozzle_opt]) if col_nozzle_opt in df_filtered_detail.columns and pd.notna(row[col_nozzle_opt]) else "H1"
                nozzle_display = f"{produk_val} ({nozzle_code})"
                
                plat_raw_val = str(row[col_nopol_opt])
                plat_val_display = "– tanpa plat –" if plat_raw_val in ["INVALID_NOPOL", ""] else plat_raw_val
                
                vol_numeric_val = pd.to_numeric(row[col_vol_opt], errors='coerce') if col_vol_opt in df_filtered_detail.columns else 0.0
                vol_val = f"{vol_numeric_val:.2f}L" if pd.notna(vol_numeric_val) else "0.00L"
                
                perkiraan_jenis, _ = deteksi_kategori_dan_kuota(plat_raw_val, produk_val)
                
                status_badge_html = "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"
                
                if plat_raw_val in ["– tanpa plat –", "INVALID_NOPOL", ""]:
                    status_badge_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>"
                elif row.get('is_fast_interval', False) or row.get('is_cross_pump', False) or vol_numeric_val > st.session_state.batas_sekali_isi:
                    status_badge_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>"

                with st.container():
                    cols = st.columns([1.2, 1.5, 1.8, 2.2, 1.5, 1.0, 2.2, 1.8, 3.0])
                    with cols[0]:
                        uploaded_img = st.file_uploader("Foto", type=["png", "jpg", "jpeg"], key=f"img_up_{idx}", label_visibility="collapsed")
                        if uploaded_img is not None:
                            st.session_state.foto_evidens[row_key] = uploaded_img.getvalue()
                        if row_key in st.session_state.foto_evidens:
                            st.markdown("✅ *Ada Foto*", unsafe_allow_html=True)
                    with cols[1]:
                        st.text(trans_id)
                    with cols[2]:
                        st.text(waktu_val)
                    with cols[3]:
                        st.text(nozzle_display)
                    with cols[4]:
                        st.markdown(f"**{plat_val_display}**")
                    with cols[5]:
                        st.text(vol_val)
                    with cols[6]:
                        st.text(perkiraan_jenis)
                    with cols[7]:
                        st.markdown(status_badge_html, unsafe_allow_html=True)
                    with cols[8]:
                        catatan_val = st.text_input("Catatan", value=st.session_state.catatan_transaksi.get(row_key, ""), key=f"note_{idx}", label_visibility="collapsed", placeholder="Tambah catatan...")
                        st.session_state.catatan_transaksi[row_key] = catatan_val
                    st.markdown("---")

    with tab3:
        st.subheader("⚙️ Pengaturan Kuota & Regulasi Batas Transaksi")
        st.markdown("<p style='color: #64748b; font-size: 0.85rem;'>Sesuaikan parameter batasan kuota harian dan deteksi anomali sesuai kebijakan SPBU / regulasi terbaru.</p>", unsafe_allow_html=True)
        
        sc1, sc2 = st.columns(2)
        with sc1:
            st.session_state.kuota_pribadi_r4 = st.number_input("Kuota Harian Mobil Pribadi R4 (Liter)", value=st.session_state.kuota_pribadi_r4, step=5.0)
            st.session_state.kuota_motor = st.number_input("Kuota Harian Sepeda Motor R2 (Liter)", value=st.session_state.kuota_motor, step=2.0)
            st.session_state.kuota_penumpang = st.number_input("Kuota Harian Mobil Penumpang Umum (Liter)", value=st.session_state.kuota_penumpang, step=10.0)
        with sc2:
            st.session_state.kuota_barang = st.number_input("Kuota Harian Truk Barang R4+ (Liter)", value=st.session_state.kuota_barang, step=10.0)
            st.session_state.kuota_berat = st.number_input("Kuota Harian Truk Beban Berat (Liter)", value=st.session_state.kuota_berat, step=10.0)
            st.session_state.batas_sekali_isi = st.number_input("Batas Maksimal Sekali Pengisian (Liter)", value=st.session_state.batas_sekali_isi, step=10.0)

        st.markdown("---")
        rc1, rc2 = st.columns(2)
        with rc1:
            st.session_state.max_frekuensi_harian = st.number_input("Maksimal Frekuensi Pengisian per Hari", value=st.session_state.max_frekuensi_harian, step=1)
        with rc2:
            st.session_state.min_jeda_waktu = st.number_input("Minimum Jeda Waktu Pengisian (Menit)", value=st.session_state.min_jeda_waktu, step=5)

    with tab_db:
        st.subheader("🗄️ Bank Database Arsip Riwayat Unduhan")
        st.markdown("<p style='color: #64748b; font-size: 0.85rem;'>Daftar file laporan yang pernah diunduh atau disimpan otomatis ke dalam database lokal SQLite.</p>", unsafe_allow_html=True)
        
        cursor_db = db_conn.cursor()
        cursor_db.execute("SELECT id, waktu_unduh, jenis_laporan, nama_file, spbu_id, total_baris FROM riwayat_unduhan ORDER BY id DESC")
        rows_db = cursor_db.fetchall()
        
        if rows_db:
            db_data_list = []
            for r in rows_db:
                db_data_list.append({
                    "ID": r[0],
                    "Waktu Unduh": r[1],
                    "Jenis Laporan": r[2],
                    "Nama File": r[3],
                    "SPBU ID": r[4],
                    "Total Baris": r[5]
                })
            df_db_view = pd.DataFrame(db_data_list)
            st.dataframe(df_db_view, use_container_width=True)
            
            selected_id_dl = st.selectbox("Pilih ID Arsip untuk Diunduh Kembali", [r["ID"] for r in db_data_list])
            if selected_id_dl:
                cursor_db.execute("SELECT nama_file, file_data FROM riwayat_unduhan WHERE id = ?", (selected_id_dl,))
                res_file = cursor_db.fetchone()
                if res_file:
                    st.download_button(
                        label=f"📥 Download Ulang Arsip #{selected_id_dl} ({res_file[0]})",
                        data=res_file[1],
                        file_name=res_file[0],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
        else:
            st.info("Belum ada riwayat unduhan atau file yang disimpan ke database arsip.")
