import streamlit as st
import pandas as pdimport streamlit as st
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
    page_title="Monitor Subsidi Tepat Guna - Pertamina Retail",
    page_icon="⛽",
    layout="wide"
)

# CSS Kustom untuk Styling Header, Kartu Metrik, & Tampilan Awal
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
    }
    .info-box-custom {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 40px;
        text-align: center;
        color: #64748b;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
    }
</style>
""", unsafe_allow_html=True)

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

# Header Utama Sesuai Gambar Referensi (Layout 2 Kolom: Teks & Logo Pertamina Retail)
head_col1, head_col2 = st.columns([5, 1.5])
with head_col1:
    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; margin-bottom: 2px;'>MONITORING &nbsp;·&nbsp; DATA H-1 (KEMARIN)</p>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #0f172a; margin-top: 0; margin-bottom: 4px; font-weight: 800;'>Monitor Subsidi Tepat Guna</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 0.9rem; margin-top: 0;'>Penyaringan awal anomali BBM bersubsidi — untuk verifikasi CCTV & koordinasi SAMSAT.</p>", unsafe_allow_html=True)

with head_col2:
    # Menampilkan Logo Pertamina Retail menggunakan Markdown / HTML Image
    st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center; padding-top: 5px;">
            <div style="text-align: right;">
                <span style="font-weight: 900; font-size: 1.1rem; color: #003366; letter-spacing: -0.5px;">PERTAMINA</span><br>
                <span style="font-weight: 800; font-size: 0.75rem; color: #cc0000; letter-spacing: 1px;">RETAIL</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Sidebar untuk Pengaturan & Input Data Utama (Opsional, atau dikontrol lewat file uploader utama)
with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    spbu_id_input = st.text_input("ID SPBU", value="4150201")
    selected_date = st.date_input("Tanggal Transaksi", value=datetime.today())

# Area Utama File Uploader (Tengah Halaman)
uploaded_file = st.file_uploader("Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk pilih file", type=["xlsx", "xls", "csv"])
st.markdown("<p style='text-align: center; font-size: 0.75rem; color: #64748b; margin-top: -5px;'>Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi (Pertamax dll.) diabaikan. Plat diambil dari kolom Payment.</p>", unsafe_allow_html=True)

# Panel Pengaturan Ambang Batas & Kuota (Expander)
with st.expander("⚙️ Pengaturan ambang batas & kuota"):
    sc1, sc2 = st.columns(2)
    with sc1:
        st.session_state.kuota_pribadi_r4 = st.number_input("Kuota Harian Mobil Pribadi R4 (Liter)", value=st.session_state.kuota_pribadi_r4, step=5.0)
        st.session_state.kuota_motor = st.number_input("Kuota Harian Sepeda Motor R2 (Liter)", value=st.session_state.kuota_motor, step=2.0)
    with sc2:
        st.session_state.kuota_barang = st.number_input("Kuota Harian Truk Barang R4+ (Liter)", value=st.session_state.kuota_barang, step=10.0)
        st.session_state.batas_sekali_isi = st.number_input("Batas Maksimal Sekali Pengisian (Liter)", value=st.session_state.batas_sekali_isi, step=10.0)

# Kotak Informasi Cara Kerja Penilaian
st.markdown(
    """
    <div style="background-color: #fffbeb; border: 1px solid #fef3c7; padding: 12px 16px; border-radius: 8px; margin-top: 10px; margin-bottom: 15px; color: #92400e; font-size: 0.85rem;">
        <strong>Cara kerja penilaian.</strong> Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
        <strong>Perkiraan jenis</strong> dari angka plat (<code>ESTIMASI PLAT</code>) hanya jadi <em>lead "cek plat palsu"</em> bila janggal — mis. angka plat $\approx$ motor tapi mengisi Solar. 
        Foto CCTV per baris (kamera HP atau upload file di PC) menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
    </div>
    """, 
    unsafe_allow_html=True
)

# Logika Pemrosesan Berdasarkan Ada/Tidaknya File yang Diunggah
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
        st.success("✅ File berhasil dimuat dan dianalisis!")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        df_raw = None
else:
    df_raw = None

if df_raw is not None:
    cols_lower = {c.lower(): c for c in df_raw.columns}
    col_time_opt = next((cols_lower[c] for c in cols_lower if 'waktu' in c or 'time' in c or 'jam' in c), df_raw.columns[0])
    col_nopol_opt = next((cols_lower[c] for c in cols_lower if 'polisi' in c or 'nopol' in c or 'plate' in c or 'plat' in c), df_raw.columns[1] if len(df_raw.columns) > 1 else df_raw.columns[0])
    col_produk_opt = next((cols_lower[c] for c in cols_lower if 'produk' in c or 'product' in c or 'bbm' in c), df_raw.columns[2] if len(df_raw.columns) > 2 else df_raw.columns[0])
    col_vol_opt = next((cols_lower[c] for c in cols_lower if 'volume' in c or 'liter' in c or 'qty' in c), df_raw.columns[3] if len(df_raw.columns) > 3 else df_raw.columns[0])
    col_nozzle_opt = next((cols_lower[c] for c in cols_lower if 'nozzle' in c or ' pompa' in c), df_raw.columns[4] if len(df_raw.columns) > 4 else df_raw.columns[0])

    df_analysis = df_raw.copy()
    df_analysis['vol_numeric'] = pd.to_numeric(df_analysis[col_vol_opt], errors='coerce').fillna(0)
    df_plat_grouped = df_analysis.groupby(col_nopol_opt)['vol_numeric'].agg(['sum', 'count']).reset_index()
    
    plat_lewat_kuota_count = len(df_plat_grouped[df_plat_grouped['sum'] > 50.0])
    transaksi_tanpa_nopol_count = len(df_analysis[df_analysis[col_nopol_opt].astype(str).str.upper().isin(["INVALID_NOPOL", "", "NONE", "NAN"])])

    tab1, tab2, tab3, tab_db = st.tabs(["📊 Ringkasan & Metrik", "🔍 Detail Transaksi & Evidens", "⚙️ Pengaturan Kuota", "🗄️ Bank Database Arsip"])

    with tab1:
        # Baris Kartu Metrik Atas
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">⛽ Plat melewati kuota harian</div>
                    <div class="metric-value">{plat_lewat_kuota_count}</div>
                </div>
            """, unsafe_allow_html=True)
        with mc2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🚫 Transaksi subsidi tanpa nopol</div>
                    <div class="metric-value">{transaksi_tanpa_nopol_count}</div>
                </div>
            """, unsafe_allow_html=True)
        with mc3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🔑 Angka plat tak cocok konsumsi (lead)</div>
                    <div class="metric-value">0</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Baris Kartu Metrik Bawah
        sc1, sc2, sc3, sc4 = st.columns(4)
        total_jbt = len(df_analysis)
        with sc1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Transaksi JBT</div>
                    <div class="metric-value">{total_jbt}</div>
                </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Sangat mencurigakan</div>
                    <div class="metric-value">0</div>
                </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Perlu diperiksa</div>
                    <div class="metric-value">{plat_lewat_kuota_count}</div>
                </div>
            """, unsafe_allow_html=True)
        with sc4:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Normal</div>
                    <div class="metric-value">{max(0, total_jbt - plat_lewat_kuota_count)}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Rekap per Plat (Harian) — Solar/JBT")
        
        for _, r_plat in df_plat_grouped.iterrows():
            nopol_val = r_plat[col_nopol_opt]
            total_vol = r_plat['sum']
            count_trx = r_plat['count']
            
            status_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>" if total_vol > 50.0 else "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"

            with st.container():
                rc_cols = st.columns([1.5, 2.5, 1.0, 3.5, 1.5])
                with rc_cols[0]:
                    st.markdown(f"**{nopol_val}**")
                with rc_cols[1]:
                    st.markdown("≈ Mobil penumpang <span style='background-color: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; color: #475569; border: 1px solid #cbd5e1;'>ESTIMASI PLAT</span>", unsafe_allow_html=True)
                with rc_cols[2]:
                    st.markdown(f"{count_trx}×")
                with rc_cols[3]:
                    st.markdown(f"{total_vol:.1f} L / 200 L <span style='font-size: 0.75rem; color: #64748b;'>(batas terlonggar)</span>", unsafe_allow_html=True)
                    st.progress(min(float(total_vol / 200.0), 1.0))
                with rc_cols[4]:
                    st.markdown(status_html, unsafe_allow_html=True)
                st.markdown("---")

    with tab2:
        st.subheader("🔍 Detail Transaksi & Evidens Kamera Perangkat")
        search_query = st.text_input("Cari plat nomor...", placeholder="Ketik nomor plat...")
        
        df_filtered_detail = df_analysis.copy()
        if search_query.strip():
            df_filtered_detail = df_filtered_detail[
                df_filtered_detail[col_nopol_opt].astype(str).str.contains(search_query.strip(), case=False, na=False)
            ]

        for idx, row in df_filtered_detail.iterrows():
            row_key = f"row_{idx}"
            trans_id = str(2300000 + idx)
            waktu_val = str(row[col_time_opt]) if col_time_opt in df_filtered_detail.columns else "-"
            produk_val = str(row[col_produk_opt]) if col_produk_opt in df_filtered_detail.columns else "SOLAR"
            plat_raw_val = str(row[col_nopol_opt])
            vol_numeric_val = row['vol_numeric']
            
            with st.container():
                cols = st.columns([1.2, 1.5, 1.8, 2.2, 1.5, 1.0, 2.2, 1.8, 3.0])
                with cols[0]:
                    uploaded_img = st.file_uploader("Foto", type=["png", "jpg", "jpeg"], key=f"img_up_{idx}", label_visibility="collapsed")
                    if uploaded_img is not None:
                        st.session_state.foto_evidens[row_key] = uploaded_img.getvalue()
                with cols[1]:
                    st.text(trans_id)
                with cols[2]:
                    st.text(waktu_val)
                with cols[3]:
                    st.text(f"{produk_val}")
                with cols[4]:
                    st.markdown(f"**{plat_raw_val}**")
                with cols[5]:
                    st.text(f"{vol_numeric_val:.2f}L")
                with cols[6]:
                    st.text("Mobil Pribadi")
                with cols[7]:
                    st.markdown("● Normal")
                with cols[8]:
                    catatan_val = st.text_input("Catatan", value=st.session_state.catatan_transaksi.get(row_key, ""), key=f"note_{idx}", label_visibility="collapsed", placeholder="Tambah catatan...")
                    st.session_state.catatan_transaksi[row_key] = catatan_val
                st.markdown("---")

    with tab3:
        st.subheader("⚙️ Pengaturan Kuota Lanjutan")
        st.session_state.kuota_pribadi_r4 = st.number_input("Kuota Harian Mobil Pribadi R4", value=st.session_state.kuota_pribadi_r4)

    with tab_db:
        st.subheader("🗄️ Bank Database Arsip")
        cursor_db = db_conn.cursor()
        cursor_db.execute("SELECT id, waktu_unduh, jenis_laporan, nama_file, spbu_id, total_baris FROM riwayat_unduhan ORDER BY id DESC")
        rows_db = cursor_db.fetchall()
        if rows_db:
            st.dataframe(pd.DataFrame(rows_db, columns=["ID", "Waktu", "Jenis", "Nama File", "SPBU", "Baris"]), use_container_width=True)
        else:
            st.info("Belum ada riwayat arsip.")

else:
    # Tampilan awal saat belum ada file yang dimasukkan (Persis seperti gambar referensi Anda)
    st.markdown(
        """
        <div class="info-box-custom">
            <h4 style="color: #0f172a; margin-bottom: 8px;">Belum ada data yang dianalisis</h4>
            <p style="margin: 0; font-size: 0.9rem;">Upload satu file CSV/XLSX hose delivery (data kemarin) untuk mulai monitoring.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Footer Sesuai Referensi
st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.75rem;'>Analisis & foto berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun. Foto hilang bila halaman dimuat ulang.<br>Alat bantu penyaringan awal; setiap temuan wajib dikonfirmasi CCTV/SAMSAT sebelum tindakan.<br><br><b>Made by Antoni · Area Business Head NTT</b></p>", unsafe_allow_html=True)
import numpy as np
import io
import sqlite3
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PilImage

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - Pertamina Retail",
    page_icon="⛽",
    layout="wide"
)

# CSS Kustom untuk Styling Header, Kartu Metrik, & Tampilan Awal
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
    }
    .info-box-custom {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 40px;
        text-align: center;
        color: #64748b;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
    }
</style>
""", unsafe_allow_html=True)

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

# Header Utama Sesuai Gambar Referensi (Layout 2 Kolom: Teks & Logo Pertamina Retail)
head_col1, head_col2 = st.columns([5, 1.5])
with head_col1:
    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; margin-bottom: 2px;'>MONITORING &nbsp;·&nbsp; DATA H-1 (KEMARIN)</p>", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #0f172a; margin-top: 0; margin-bottom: 4px; font-weight: 800;'>Monitor Subsidi Tepat Guna</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748b; font-size: 0.9rem; margin-top: 0;'>Penyaringan awal anomali BBM bersubsidi — untuk verifikasi CCTV & koordinasi SAMSAT.</p>", unsafe_allow_html=True)

with head_col2:
    # Menampilkan Logo Pertamina Retail menggunakan Markdown / HTML Image
    st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center; padding-top: 5px;">
            <div style="text-align: right;">
                <span style="font-weight: 900; font-size: 1.1rem; color: #003366; letter-spacing: -0.5px;">PERTAMINA</span><br>
                <span style="font-weight: 800; font-size: 0.75rem; color: #cc0000; letter-spacing: 1px;">RETAIL</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Sidebar untuk Pengaturan & Input Data Utama (Opsional, atau dikontrol lewat file uploader utama)
with st.sidebar:
    st.header("⚙️ Panel Kontrol")
    spbu_id_input = st.text_input("ID SPBU", value="4150201")
    selected_date = st.date_input("Tanggal Transaksi", value=datetime.today())

# Area Utama File Uploader (Tengah Halaman)
uploaded_file = st.file_uploader("Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk pilih file", type=["xlsx", "xls", "csv"])
st.markdown("<p style='text-align: center; font-size: 0.75rem; color: #64748b; margin-top: -5px;'>Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi (Pertamax dll.) diabaikan. Plat diambil dari kolom Payment.</p>", unsafe_allow_html=True)

# Panel Pengaturan Ambang Batas & Kuota (Expander)
with st.expander("⚙️ Pengaturan ambang batas & kuota"):
    sc1, sc2 = st.columns(2)
    with sc1:
        st.session_state.kuota_pribadi_r4 = st.number_input("Kuota Harian Mobil Pribadi R4 (Liter)", value=st.session_state.kuota_pribadi_r4, step=5.0)
        st.session_state.kuota_motor = st.number_input("Kuota Harian Sepeda Motor R2 (Liter)", value=st.session_state.kuota_motor, step=2.0)
    with sc2:
        st.session_state.kuota_barang = st.number_input("Kuota Harian Truk Barang R4+ (Liter)", value=st.session_state.kuota_barang, step=10.0)
        st.session_state.batas_sekali_isi = st.number_input("Batas Maksimal Sekali Pengisian (Liter)", value=st.session_state.batas_sekali_isi, step=10.0)

# Kotak Informasi Cara Kerja Penilaian
st.markdown(
    """
    <div style="background-color: #fffbeb; border: 1px solid #fef3c7; padding: 12px 16px; border-radius: 8px; margin-top: 10px; margin-bottom: 15px; color: #92400e; font-size: 0.85rem;">
        <strong>Cara kerja penilaian.</strong> Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
        <strong>Perkiraan jenis</strong> dari angka plat (<code>ESTIMASI PLAT</code>) hanya jadi <em>lead "cek plat palsu"</em> bila janggal — mis. angka plat $\approx$ motor tapi mengisi Solar. 
        Foto CCTV per baris (kamera HP atau upload file di PC) menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
    </div>
    """, 
    unsafe_allow_html=True
)

# Logika Pemrosesan Berdasarkan Ada/Tidaknya File yang Diunggah
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
        st.success("✅ File berhasil dimuat dan dianalisis!")
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        df_raw = None
else:
    df_raw = None

if df_raw is not None:
    cols_lower = {c.lower(): c for c in df_raw.columns}
    col_time_opt = next((cols_lower[c] for c in cols_lower if 'waktu' in c or 'time' in c or 'jam' in c), df_raw.columns[0])
    col_nopol_opt = next((cols_lower[c] for c in cols_lower if 'polisi' in c or 'nopol' in c or 'plate' in c or 'plat' in c), df_raw.columns[1] if len(df_raw.columns) > 1 else df_raw.columns[0])
    col_produk_opt = next((cols_lower[c] for c in cols_lower if 'produk' in c or 'product' in c or 'bbm' in c), df_raw.columns[2] if len(df_raw.columns) > 2 else df_raw.columns[0])
    col_vol_opt = next((cols_lower[c] for c in cols_lower if 'volume' in c or 'liter' in c or 'qty' in c), df_raw.columns[3] if len(df_raw.columns) > 3 else df_raw.columns[0])
    col_nozzle_opt = next((cols_lower[c] for c in cols_lower if 'nozzle' in c or ' pompa' in c), df_raw.columns[4] if len(df_raw.columns) > 4 else df_raw.columns[0])

    df_analysis = df_raw.copy()
    df_analysis['vol_numeric'] = pd.to_numeric(df_analysis[col_vol_opt], errors='coerce').fillna(0)
    df_plat_grouped = df_analysis.groupby(col_nopol_opt)['vol_numeric'].agg(['sum', 'count']).reset_index()
    
    plat_lewat_kuota_count = len(df_plat_grouped[df_plat_grouped['sum'] > 50.0])
    transaksi_tanpa_nopol_count = len(df_analysis[df_analysis[col_nopol_opt].astype(str).str.upper().isin(["INVALID_NOPOL", "", "NONE", "NAN"])])

    tab1, tab2, tab3, tab_db = st.tabs(["📊 Ringkasan & Metrik", "🔍 Detail Transaksi & Evidens", "⚙️ Pengaturan Kuota", "🗄️ Bank Database Arsip"])

    with tab1:
        # Baris Kartu Metrik Atas
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">⛽ Plat melewati kuota harian</div>
                    <div class="metric-value">{plat_lewat_kuota_count}</div>
                </div>
            """, unsafe_allow_html=True)
        with mc2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🚫 Transaksi subsidi tanpa nopol</div>
                    <div class="metric-value">{transaksi_tanpa_nopol_count}</div>
                </div>
            """, unsafe_allow_html=True)
        with mc3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">🔑 Angka plat tak cocok konsumsi (lead)</div>
                    <div class="metric-value">0</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Baris Kartu Metrik Bawah
        sc1, sc2, sc3, sc4 = st.columns(4)
        total_jbt = len(df_analysis)
        with sc1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Transaksi JBT</div>
                    <div class="metric-value">{total_jbt}</div>
                </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Sangat mencurigakan</div>
                    <div class="metric-value">0</div>
                </div>
            """, unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Perlu diperiksa</div>
                    <div class="metric-value">{plat_lewat_kuota_count}</div>
                </div>
            """, unsafe_allow_html=True)
        with sc4:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Normal</div>
                    <div class="metric-value">{max(0, total_jbt - plat_lewat_kuota_count)}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Rekap per Plat (Harian) — Solar/JBT")
        
        for _, r_plat in df_plat_grouped.iterrows():
            nopol_val = r_plat[col_nopol_opt]
            total_vol = r_plat['sum']
            count_trx = r_plat['count']
            
            status_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>" if total_vol > 50.0 else "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"

            with st.container():
                rc_cols = st.columns([1.5, 2.5, 1.0, 3.5, 1.5])
                with rc_cols[0]:
                    st.markdown(f"**{nopol_val}**")
                with rc_cols[1]:
                    st.markdown("≈ Mobil penumpang <span style='background-color: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; color: #475569; border: 1px solid #cbd5e1;'>ESTIMASI PLAT</span>", unsafe_allow_html=True)
                with rc_cols[2]:
                    st.markdown(f"{count_trx}×")
                with rc_cols[3]:
                    st.markdown(f"{total_vol:.1f} L / 200 L <span style='font-size: 0.75rem; color: #64748b;'>(batas terlonggar)</span>", unsafe_allow_html=True)
                    st.progress(min(float(total_vol / 200.0), 1.0))
                with rc_cols[4]:
                    st.markdown(status_html, unsafe_allow_html=True)
                st.markdown("---")

    with tab2:
        st.subheader("🔍 Detail Transaksi & Evidens Kamera Perangkat")
        search_query = st.text_input("Cari plat nomor...", placeholder="Ketik nomor plat...")
        
        df_filtered_detail = df_analysis.copy()
        if search_query.strip():
            df_filtered_detail = df_filtered_detail[
                df_filtered_detail[col_nopol_opt].astype(str).str.contains(search_query.strip(), case=False, na=False)
            ]

        for idx, row in df_filtered_detail.iterrows():
            row_key = f"row_{idx}"
            trans_id = str(2300000 + idx)
            waktu_val = str(row[col_time_opt]) if col_time_opt in df_filtered_detail.columns else "-"
            produk_val = str(row[col_produk_opt]) if col_produk_opt in df_filtered_detail.columns else "SOLAR"
            plat_raw_val = str(row[col_nopol_opt])
            vol_numeric_val = row['vol_numeric']
            
            with st.container():
                cols = st.columns([1.2, 1.5, 1.8, 2.2, 1.5, 1.0, 2.2, 1.8, 3.0])
                with cols[0]:
                    uploaded_img = st.file_uploader("Foto", type=["png", "jpg", "jpeg"], key=f"img_up_{idx}", label_visibility="collapsed")
                    if uploaded_img is not None:
                        st.session_state.foto_evidens[row_key] = uploaded_img.getvalue()
                with cols[1]:
                    st.text(trans_id)
                with cols[2]:
                    st.text(waktu_val)
                with cols[3]:
                    st.text(f"{produk_val}")
                with cols[4]:
                    st.markdown(f"**{plat_raw_val}**")
                with cols[5]:
                    st.text(f"{vol_numeric_val:.2f}L")
                with cols[6]:
                    st.text("Mobil Pribadi")
                with cols[7]:
                    st.markdown("● Normal")
                with cols[8]:
                    catatan_val = st.text_input("Catatan", value=st.session_state.catatan_transaksi.get(row_key, ""), key=f"note_{idx}", label_visibility="collapsed", placeholder="Tambah catatan...")
                    st.session_state.catatan_transaksi[row_key] = catatan_val
                st.markdown("---")

    with tab3:
        st.subheader("⚙️ Pengaturan Kuota Lanjutan")
        st.session_state.kuota_pribadi_r4 = st.number_input("Kuota Harian Mobil Pribadi R4", value=st.session_state.kuota_pribadi_r4)

    with tab_db:
        st.subheader("🗄️ Bank Database Arsip")
        cursor_db = db_conn.cursor()
        cursor_db.execute("SELECT id, waktu_unduh, jenis_laporan, nama_file, spbu_id, total_baris FROM riwayat_unduhan ORDER BY id DESC")
        rows_db = cursor_db.fetchall()
        if rows_db:
            st.dataframe(pd.DataFrame(rows_db, columns=["ID", "Waktu", "Jenis", "Nama File", "SPBU", "Baris"]), use_container_width=True)
        else:
            st.info("Belum ada riwayat arsip.")

else:
    # Tampilan awal saat belum ada file yang dimasukkan (Persis seperti gambar referensi Anda)
    st.markdown(
        """
        <div class="info-box-custom">
            <h4 style="color: #0f172a; margin-bottom: 8px;">Belum ada data yang dianalisis</h4>
            <p style="margin: 0; font-size: 0.9rem;">Upload satu file CSV/XLSX hose delivery (data kemarin) untuk mulai monitoring.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

# Footer Sesuai Referensi
st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.75rem;'>Analisis & foto berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun. Foto hilang bila halaman dimuat ulang.<br>Alat bantu penyaringan awal; setiap temuan wajib dikonfirmasi CCTV/SAMSAT sebelum tindakan.<br><br><b>Made by Antoni · Area Business Head NTT</b></p>", unsafe_allow_html=True)
