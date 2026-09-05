import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io
from PIL import Image as PilImage
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl import load_workbook
import sqlite3

# Inisialisasi Database SQLite Lokal
def init_db():
    conn = sqlite3.connect('spbu_database.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS riwayat_unduhan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu_unduh TEXT,
            jenis_laporan TEXT,
            nama_file TEXT,
            file_data BLOB,
            spbu_id TEXT,
            total_baris INTEGER
        )
    ''')
    conn.commit()
    return conn

db_conn = init_db()

def simpan_ke_database(jenis_laporan, nama_file, file_bytes, spbu_id, total_baris):
    cursor = db_conn.cursor()
    waktu_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO riwayat_unduhan (waktu_unduh, jenis_laporan, nama_file, file_data, spbu_id, total_baris)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (waktu_str, jenis_laporan, nama_file, sqlite3.Binary(file_bytes), spbu_id, total_baris))
    db_conn.commit()

# Page Configuration
st.set_page_config(
    page_title="Monitoring Subsidi Tepat - SPBU TAC",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #f1f5f9; }
    
    .custom-metric-card {
        background-color: #ffffff;
        padding: 12px 16px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .custom-metric-card-alert {
        background-color: #fee2e2 !important;
        padding: 12px 16px;
        border-radius: 6px;
        border: 1px solid #f87171 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .estimasi-tag {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        color: #475569;
        font-size: 0.60rem;
        padding: 1px 4px;
        border-radius: 4px;
        font-weight: 600;
        letter-spacing: 0.03em;
        margin-top: 2px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State
if "filter_produk" not in st.session_state:
    st.session_state.filter_produk = "SEMUA"

if "kuota_pribadi_r4" not in st.session_state:
    st.session_state.kuota_pribadi_r4 = 60.0
if "kuota_motor" not in st.session_state:
    st.session_state.kuota_motor = 10.0
if "kuota_penumpang" not in st.session_state:
    st.session_state.kuota_penumpang = 100.0
if "kuota_barang" not in st.session_state:
    st.session_state.kuota_barang = 150.0
if "kuota_berat" not in st.session_state:
    st.session_state.kuota_berat = 200.0

if "max_frekuensi_harian" not in st.session_state:
    st.session_state.max_frekuensi_harian = 2
if "min_jeda_waktu" not in st.session_state:
    st.session_state.min_jeda_waktu = 30
if "batas_sekali_isi" not in st.session_state:
    st.session_state.batas_sekali_isi = 200.0

if "catatan_transaksi" not in st.session_state:
    st.session_state.catatan_transaksi = {}

if "foto_evidens" not in st.session_state:
    st.session_state.foto_evidens = {}

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU Monitoring System | JBT & JBKP Advanced Fraud Detection & Evidence**")
st.markdown("---")

# Sidebar (Pengaturan Global & Tanggal)
st.sidebar.header("📅 Pengaturan Umum")
selected_date = st.sidebar.date_input("Pilih Tanggal Analisis", datetime.now().date())
spbu_id_input = st.sidebar.text_input("ID SPBU", value="4150201")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips:** Setiap file yang Anda unduh akan otomatis disimpan ke dalam **Bank Database Arsip** lokal dan dapat diakses kembali kapan saja.")

# Inisialisasi variabel default jika belum upload
df_raw = None
col_nopol_opt, col_vol_opt, col_produk_opt, col_time_opt, col_nozzle_opt = None, None, None, None, None

# Main Layout Tabs (Ditambahkan tab "🗄️ Bank Database Arsip")
tab_upload, tab1, tab2, tab3, tab_db = st.tabs([
    "📁 Data Upload & Manajemen", 
    "📊 Ringkasan & Agregasi Plat", 
    "🔍 Detail Transaksi & Evidens Kamera", 
    "⚙️ Pengaturan Batas & Regulasi",
    "🗄️ Bank Database Arsip"
])

with tab_upload:
    st.subheader("📂 Unggah File Data Transaksi & Pemetaan Kolom")
    st.markdown("<p style='color: #64748b; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px;'>Silakan unggah file transaksi dalam format Excel (.xlsx) atau CSV, lalu sesuaikan pemetaan kolom tabel agar sistem dapat membaca data dengan benar.</p>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
            
            st.success(f"File **{uploaded_file.name}** berhasil dimuat! Total baris data: {len(df_raw):,}")
            
            df_raw.columns = df_raw.columns.str.strip()
            columns_list = list(df_raw.columns)

            def find_best_column(keywords, negative_keywords=[]):
                for col in columns_list:
                    col_lower = col.lower()
                    if any(neg in col_lower for neg in negative_keywords):
                        continue
                    for kw in keywords:
                        if kw in col_lower:
                            return col
                return columns_list[0] if columns_list else None

            default_nopol = find_best_column(["plat", "nopol", "nomor", "vehicle", "police", "kendaraan"], ["payment", "bayar", "status", "id"])
            default_vol = find_best_column(["volume", "liter", "vol", "qty", "jumlah"])
            default_produk = find_best_column(["produk", "bbm", "jenis", "product", "fuel", "bahan bakar"])
            default_time = find_best_column(["waktu", "time", "jam", "tanggal", "date", "timestamp"])
            default_nozzle = find_best_column(["nozzle", "nosel", "pompa", "island", "dispenser"])

            st.markdown("---")
            st.markdown("### ⚙️ Konfigurasi Kolom Data")
            
            map_c1, map_c2, map_c3 = st.columns(3)
            with map_c1:
                col_nopol_opt = st.selectbox("Kolom Plat Nomor / Nopol", columns_list, index=columns_list.index(default_nopol) if default_nopol in columns_list else 0)
                col_vol_opt = st.selectbox("Kolom Volume (L)", columns_list, index=columns_list.index(default_vol) if default_vol in columns_list else 0)
            with map_c2:
                col_produk_opt = st.selectbox("Kolom Produk / Jenis BBM", columns_list, index=columns_list.index(default_produk) if default_produk in columns_list else 0)
                col_time_opt = st.selectbox("Kolom Waktu / Jam Transaksi", columns_list, index=columns_list.index(default_time) if default_time in columns_list else 0)
            with map_c3:
                col_nozzle_opt = st.selectbox("Kolom Nozzle / Pompa (Opsional)", columns_list, index=columns_list.index(default_nozzle) if default_nozzle in columns_list else 0)

            st.markdown("---")
            st.markdown("### 🔍 Pratinjau Data Mentah (5 Baris Pertama)")
            st.dataframe(df_raw.head(5), use_container_width=True)

        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")
    else:
        st.info("👆 Silakan unggah file Excel atau CSV di atas untuk memulai analisis.")

# Proses Data jika file sudah diunggah
if uploaded_file is not None and df_raw is not None:
    try:
        if col_nopol_opt in df_raw.columns:
            df_raw = df_raw.copy()
            
            def clean_and_validate_nopol(val):
                s = str(val).strip()
                s_upper = s.upper()
                invalid_keywords = ["CASH", "TIDAK ADA", "NAN", "NONE", "-", "NULL", "TUNAI", "0", ""]
                if s_upper in invalid_keywords or len(s) < 3:
                    return "INVALID_NOPOL"
                cleaned = re.sub(r'[^A-Z0-9 ]', '', s_upper)
                return cleaned if len(cleaned) >= 3 else "INVALID_NOPOL"

            df_raw[col_nopol_opt] = df_raw[col_nopol_opt].apply(clean_and_validate_nopol)

        def deteksi_kategori_dan_kuota(plat_str, produk_str):
            if plat_str == "INVALID_NOPOL":
                return "Tidak Valid / Tanpa Nopol", 0.0
            
            angka_list = re.findall(r'\d+', str(plat_str))
            if not angka_list:
                return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4
            
            nomor_reg = int(angka_list[0])
            prod_upper = str(produk_str).upper()
            is_jbt = any(x in prod_upper for x in ["SOLAR", "BIOSOLAR", "JBT", "MHD", "DEALITE"])
            
            if is_jbt:
                if 1 <= nomor_reg <= 2999:
                    return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4
                elif 3000 <= nomor_reg <= 6999:
                    return "Sepeda Motor (R2)", st.session_state.kuota_motor
                elif 7000 <= nomor_reg <= 7999:
                    return "Mobil penumpang", st.session_state.kuota_penumpang
                elif 8000 <= nomor_reg <= 8999:
                    return "Truk Barang (R4+)", st.session_state.kuota_barang
                elif 9000 <= nomor_reg <= 9999:
                    return "Truk & Kendaraan Beban Berat", st.session_state.kuota_berat
                else:
                    return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4
            else: 
                if 1 <= nomor_reg <= 2999:
                    return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4
                elif 3000 <= nomor_reg <= 6999:
                    return "Sepeda Motor (R2)", st.session_state.kuota_motor
                elif 7000 <= nomor_reg <= 7999:
                    return "Mobil penumpang", st.session_state.kuota_penumpang
                else:
                    return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4

        if col_produk_opt in df_raw.columns:
            produk_series = df_raw[col_produk_opt].astype(str)
            df_jbt = df_raw[produk_series.str.contains("SOLAR|BIOSOLAR|JBT|MHD|DEALITE", case=False, na=False)]
            df_jbkp = df_raw[produk_series.str.contains("PERTALITE|JBKP|RON90", case=False, na=False)]
        else:
            df_jbt = df_raw.iloc[:0]
            df_jbkp = df_raw.iloc[:0]

        jbt_count = len(df_jbt)
        jbkp_count = len(df_jbkp)
        total_all_count = len(df_raw)

        if st.session_state.filter_produk == "JBT":
            df_display = df_jbt
        elif st.session_state.filter_produk == "JBKP":
            df_display = df_jbkp
        else:
            df_display = df_raw

        total_transaksi = len(df_display)
        total_vol = pd.to_numeric(df_display[col_vol_opt], errors='coerce').fillna(0).sum() if col_vol_opt in df_display.columns else 0.0

        df_analysis = df_display.copy()
        if col_time_opt in df_analysis.columns:
            df_analysis['parsed_time'] = pd.to_datetime(df_analysis[col_time_opt], errors='coerce')
            df_analysis = df_analysis.sort_values(by=[col_nopol_opt, 'parsed_time'])
            
            df_analysis['prev_time'] = df_analysis.groupby(col_nopol_opt)['parsed_time'].shift(1)
            df_analysis['diff_minutes'] = (df_analysis['parsed_time'] - df_analysis['prev_time']).dt.total_seconds() / 60.0
            
            df_analysis['is_fast_interval'] = df_analysis['diff_minutes'] <= st.session_state.min_jeda_waktu
        else:
            df_analysis['diff_minutes'] = None
            df_analysis['is_fast_interval'] = False

        if col_nozzle_opt in df_analysis.columns and col_time_opt in df_analysis.columns:
            df_analysis['prev_nozzle'] = df_analysis.groupby(col_nopol_opt)[col_nozzle_opt].shift(1)
            df_analysis['is_cross_pump'] = (
                df_analysis['is_fast_interval'] & 
                (df_analysis[col_nozzle_opt].astype(str) != df_analysis['prev_nozzle'].astype(str)) &
                (df_analysis['diff_minutes'] <= 60)
            )
        else:
            df_analysis['is_cross_pump'] = False

        with tab1:
            st.subheader("Rekap per Plat (Harian) — Solar/JBT")
            st.markdown("<p style='color: #64748b; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px;'>Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT.</p>", unsafe_allow_html=True)
            
            if not df_display.empty and col_nopol_opt in df_display.columns:
                agg_dict_m = {
                    'total_volume': (col_vol_opt, lambda x: pd.to_numeric(x, errors='coerce').sum()),
                    'freq': (col_vol_opt, 'count')
                }
                df_g_metric = df_analysis.groupby(col_nopol_opt).agg(**agg_dict_m).reset_index()
                
                tanpa_nopol = len(df_analysis[df_analysis[col_nopol_opt] == "INVALID_NOPOL"])
                mobil_helikopter_count = len(df_g_metric[df_g_metric['freq'] > st.session_state.max_frekuensi_harian])
                
                vol_numeric = pd.to_numeric(df_analysis[col_vol_opt], errors='coerce').fillna(0)
                single_cap_violations = len(df_analysis[vol_numeric > st.session_state.batas_sekali_isi])
                
                fast_interval_count = int(df_analysis['is_fast_interval'].sum()) if 'is_fast_interval' in df_analysis.columns else 0
                cross_pump_count = int(df_analysis['is_cross_pump'].sum()) if 'is_cross_pump' in df_analysis.columns else 0
            else:
                tanpa_nopol = 0
                mobil_helikopter_count = 0
                single_cap_violations = 0
                fast_interval_count = 0
                cross_pump_count = 0

            def render_custom_metric(label, value, icon, alert_if_gt_zero=False):
                is_alert = alert_if_gt_zero and (isinstance(value, (int, float)) and value > 0)
                card_class = "custom-metric-card-alert" if is_alert else "custom-metric-card"
                text_color = "#b91c1c" if is_alert else "#1e293b"
                label_color = "#991b1b" if is_alert else "#64748b"
                
                html_content = f"""
                <div class="{card_class}">
                    <div style="font-size: 0.75rem; color: {label_color}; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; font-weight: 500;">
                        <span>{icon}</span> {label}
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 600; color: {text_color};">
                        {value}
                    </div>
                </div>
                """
                st.markdown(html_content, unsafe_allow_html=True)

            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                render_custom_metric("Jeda Waktu Singkat (<30m)", fast_interval_count, "⏱️", alert_if_gt_zero=True)
            with m2:
                render_custom_metric("Anomali Cross-Pump", cross_pump_count, "🔀", alert_if_gt_zero=True)
            with m3:
                render_custom_metric("Potensi Mobil Helikopter", mobil_helikopter_count, "🚁", alert_if_gt_zero=True)
            with m4:
                render_custom_metric("Langgar Batas Sekali Isi", single_cap_violations, "⚠️", alert_if_gt_zero=True)
            with m5:
                render_custom_metric("Transaksi Tanpa Nopol", tanpa_nopol, "🚫", alert_if_gt_zero=True)

            st.markdown("<br>", unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_custom_metric("Total Volume Terjual", f"{total_vol:,.1f} L", "📈", alert_if_gt_zero=False)
            with c2:
                render_custom_metric("Total Transaksi", f"{total_transaksi:,} Baris", "📋", alert_if_gt_zero=False)
            with c3:
                render_custom_metric("Produk Aktif Filter", st.session_state.filter_produk, "🏷️", alert_if_gt_zero=False)
            with c4:
                render_custom_metric("SPBU ID", spbu_id_input, "🏢", alert_if_gt_zero=False)

            st.markdown("<br>", unsafe_allow_html=True)

            # Tombol Filter Produk
            f_col1, f_col2, f_col3, _ = st.columns([1.5, 1.5, 1.5, 2])
            with f_col1:
                if st.button(f"⛽ JBT · Solar ({jbt_count:,})", use_container_width=True):
                    st.session_state.filter_produk = "JBT"
                    st.rerun()
            with f_col2:
                if st.button(f"⛽ JBKP · Pertalite ({jbkp_count:,})", use_container_width=True):
                    st.session_state.filter_produk = "JBKP"
                    st.rerun()
            with f_col3:
                if st.button(f"📦 All Product ({total_all_count:,})", use_container_width=True):
                    st.session_state.filter_produk = "SEMUA"
                    st.rerun()

            st.markdown("---")

            header_html = """
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px; margin-bottom: 6px; color: #64748b; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;">
                <div style="flex: 1.5;">PLAT</div>
                <div style="flex: 2.0;">PERKIRAAN JENIS (DARI PLAT)</div>
                <div style="flex: 0.6; text-align: center;">ISI</div>
                <div style="flex: 3.5; padding: 0 15px;">TOTAL VS KUOTA HARIAN</div>
                <div style="flex: 1.5; text-align: right;">STATUS</div>
            </div>
            """
            st.markdown(header_html, unsafe_allow_html=True)

            if not df_analysis.empty and col_nopol_opt in df_analysis.columns:
                agg_dict = {
                    'total_transaksi': (col_vol_opt, 'count'),
                    'total_volume': (col_vol_opt, lambda x: pd.to_numeric(x, errors='coerce').sum()),
                    'sample_produk': (col_produk_opt, 'first') if col_produk_opt in df_analysis.columns else (col_vol_opt, lambda x: "JBT"),
                    'has_fast_interval': ('is_fast_interval', 'any'),
                    'has_cross_pump': ('is_cross_pump', 'any')
                }

                df_grouped = df_analysis.groupby(col_nopol_opt).agg(**agg_dict).reset_index()
                df_grouped = df_grouped.sort_values(by="total_volume", ascending=False).reset_index(drop=True)

                for index, row in df_grouped.iterrows():
                    plat = str(row[col_nopol_opt])
                    freq = int(row['total_transaksi'])
                    vol = row['total_volume']
                    prod_val = row['sample_produk'] if 'sample_produk' in row else "JBT"
                    is_fast = row['has_fast_interval']
                    is_cp = row['has_cross_pump']
                    
                    jenis_kendaraan, target_kuota = deteksi_kategori_dan_kuota(plat, prod_val)
                    is_helikopter = freq > st.session_state.max_frekuensi_harian
                    persen = int((vol / target_kuota) * 100) if target_kuota > 0 else 100
                    green_width = min(100, persen)

                    if plat == "INVALID_NOPOL":
                        status_badge = "<span style='background-color: #fee2e2; color: #b91c1c; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Nopol Tidak Valid</span>"
                    elif vol > target_kuota or is_helikopter or is_fast or is_cp:
                        status_badge = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>"
                    elif vol > st.session_state.kuota_pribadi_r4:
                        status_badge = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>"
                    else:
                        status_badge = "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"

                    card_html = f"""
                    <div style="background-color: white; border: 1px solid #e2e8f0; padding: 12px 16px; margin-bottom: 8px; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="flex: 1.5; display: flex; align-items: center; gap: 6px;">
                            <strong style="font-size: 1.05rem; color: #1e293b; font-family: monospace;">{plat}</strong>
                        </div>
                        <div style="flex: 2.0; display: flex; align-items: center;">
                            <span style="color: #64748b; font-size: 0.85rem;">≈ {jenis_kendaraan}</span>
                            <span class="estimasi-tag">ESTIMASI PLAT</span>
                        </div>
                        <div style="flex: 0.6; text-align: center;">
                            <span style="color: {'#b91c1c' if is_helikopter else '#334155'}; font-size: 0.85rem; font-weight: 600;">{freq}×</span>
                        </div>
                        <div style="flex: 3.5; padding: 0 15px;">
                            <div style="background-color: #e2e8f0; border-radius: 4px; height: 6px; width: 100%; display: flex; overflow: hidden; margin-bottom: 4px;">
                                <div style="background-color: {'#ef4444' if persen > 100 else '#10b981'}; width: {green_width}%; height: 100%;"></div>
                            </div>
                            <div style="font-size: 0.75rem; color: #64748b; display: flex; justify-content: space-between;">
                                <span>{vol:,.0f} L / {target_kuota:,.0f} L (batas terlonggar)</span>
                                <span style="font-weight: 600;">{persen}%</span>
                            </div>
                        </div>
                        <div style="flex: 1.5; text-align: right;">
                            {status_badge}
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.warning("Kolom Plat Nomor tidak ditemukan pada file Anda.")

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
                
                # Simpan otomatis ke Database saat tombol unduh dirender/diklik
                if st.button("Simpan & Unduh Tindak Lanjut (Excel)", use_container_width=True, key="btn_dl_tl"):
                    simpan_ke_database("Laporan Tindak Lanjut", filename_tl, file_bytes_tl, spbu_id_input, len(df_analysis))
                    st.success("✅ File berhasil disimpan ke Bank Database & diunduh!")

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
                    waktu_val = str(row[col_time_opt]) if col_time_opt in df_filtered_detail.columns else "31/08/2026, 05.45.36"
                    produk_val = str(row[col_produk_opt]) if col_produk_opt in df_filtered_detail.columns else "BIO_SOLAR"
                    
                    nozzle_code = str(row[col_nozzle_opt]) if col_nozzle_opt in df_filtered_detail.columns and pd.notna(row[col_nozzle_opt]) else "H1"
                    nozzle_display = f"{produk_val} (P3/{nozzle_code})"
                    
                    plat_raw_val = str(row[col_nopol_opt])
                    plat_val_display = "– tanpa plat –" if plat_raw_val in ["INVALID_NOPOL", ""] else plat_raw_val
                    
                    vol_numeric_val = pd.to_numeric(row[col_vol_opt], errors='coerce') if col_vol_opt in df_filtered_detail.columns else 0.0
                    vol_val = f"{vol_numeric_val:.2f}L" if pd.notna(vol_numeric_val) else "0.00L"
                    
                    perkiraan_jenis, _ = deteksi_kategori_dan_kuota(plat_raw_val, produk_val)
                    
                    alasan = "Transaksi Normal"
                    status_badge_html = "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"
                    is_err = False
                    
                    if plat_raw_val in ["– tanpa plat –", "INVALID_NOPOL", ""]:
                        alasan = "Subsidi tanpa nopol — wajib dicatat per aturan"
                        status_badge_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>"
                        is_err = True
                    elif row.get('is_fast_interval', False) or row.get('is_cross_pump', False) or vol_numeric_val > st.session_state.batas_sekali_isi:
                        alasan = f"Total harian melewati kuota / jeda singkat (<30m)"
                        status_badge_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>"
                        is_err = True

                    @st.dialog(f"📸 Kamera & Galeri Evidens - Transaksi #{trans_id} ({plat_val_display})")
                    def show_media_modal(r_key):
                        tab_cam, tab_gal = st.tabs(["📷 Ambil dari Kamera", "📁 Upload dari Galeri"])
                        
                        with tab_cam:
                            cam_img = st.camera_input("Ambil Foto Langsung", key=f"cam_modal_{r_key}")
                            if cam_img is not None:
                                st.session_state.foto_evidens[r_key] = cam_img.getvalue()
                                st.success("✅ Foto kamera berhasil disimpan!")
                                st.image(st.session_state.foto_evidens[r_key], width=250)
                                
                        with tab_gal:
                            gal_file = st.file_uploader("Pilih file gambar", type=["png", "jpg", "jpeg"], key=f"gal_modal_{r_key}")
                            if gal_file is not None:
                                st.session_state.foto_evidens[r_key] = gal_file.getvalue()
                                st.success("✅ Foto galeri berhasil diunggah!")
                                st.image(st.session_state.foto_evidens[r_key], width=250)
                        
                        if r_key in st.session_state.foto_evidens and tab_cam is None and tab_gal is None:
                            st.info("Evidens saat ini:")
                            st.image(st.session_state.foto_evidens[r_key], width=200)

                        if st.button("Simpan & Tutup", use_container_width=True, key=f"close_modal_{r_key}*"):
                            st.rerun()

                    with st.container():
                        st.markdown("""<div style="background-color: #ffffff; border: 1px solid #e2e8f0; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px;">""", unsafe_allow_html=True)
                        
                        col_c1, col_c2, col_c3, col_c4, col_c5, col_c6, col_c7, col_c8, col_c9 = st.columns([1.2, 1.5, 1.8, 2.2, 1.5, 1.0, 2.2, 1.8, 3.0])
                        
                        with col_c1:
                            if row_key in st.session_state.foto_evidens:
                                st.image(st.session_state.foto_evidens[row_key], width=75)
                                if st.button("Ganti", key=f"chg_{row_key}", use_container_width=True):
                                    show_media_modal(row_key)
                                if st.button("Hapus", key=f"del_{row_key}", use_container_width=True):
                                    del st.session_state.foto_evidens[row_key]
                                    st.rerun()
                            else:
                                if st.button("📷/📁 Input", key=f"inp_{row_key}", use_container_width=True):
                                    show_media_modal(row_key)
                        
                        with col_c2:
                            st.markdown(f"<span style='font-family: monospace; font-size: 0.85rem; color: #334155; font-weight: 600;'>{trans_id}</span>", unsafe_allow_html=True)
                        with col_c3:
                            st.markdown(f"<span style='font-size: 0.75rem; color: #475569;'>{waktu_val}</span>", unsafe_allow_html=True)
                        with col_c4:
                            st.markdown(f"<span style='font-size: 0.8rem; font-weight: 600; color: #1e293b;'>{nozzle_display}</span>", unsafe_allow_html=True)
                        with col_c5:
                            st.markdown(f"<span style='font-family: monospace; font-weight: 700; font-size: 0.9rem; color: #1e293b;'>{plat_val_display}</span>", unsafe_allow_html=True)
                        with col_c6:
                            st.markdown(f"<span style='font-size: 0.85rem; font-weight: 600; color: #1e293b;'>{vol_val}</span>", unsafe_allow_html=True)
                        with col_c7:
                            st.markdown(f"<span style='font-size: 0.78rem; color: #475569;'>≈ {perkiraan_jenis}</span>", unsafe_allow_html=True)
                        with col_c8:
                            st.markdown(f"{status_badge_html}", unsafe_allow_html=True)
                        with col_c9:
                            st.markdown(f"<span style='font-size: 0.78rem; color: {'#b91c1c' if is_err else '#03543f'};'>{alasan}</span>", unsafe_allow_html=True)
                        
                        st.markdown("<div style='margin-top: 6px; border-top: 1px dashed #f1f5f9; padding-top: 6px;'></div>", unsafe_allow_html=True)
                        
                        current_note = st.session_state.catatan_transaksi.get(row_key, "")
                        new_note = st.text_input(
                            f"Catatan Investigasi #{trans_id}", 
                            value=current_note, 
                            placeholder="Tulis catatan investigasi pengawas di sini...",
                            key=f"note_input_{row_key}",
                            label_visibility="collapsed"
                        )
                        st.session_state.catatan_transaksi[row_key] = new_note
                        
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("Tidak ada transaksi yang cocok dengan pencarian plat nomor tersebut.")

        with tab3:
            st.subheader("⚙️ Pengaturan Batas & Regulasi Advance")
            col_s1, col_s2 = st.columns(2)

            with col_s1:
                st.markdown("#### 🚗 Batas Kuota Berdasarkan Kategori Plat")
                st.session_state.kuota_pribadi_r4 = st.number_input("Mobil Pribadi (R4) [L/Hari]", value=float(st.session_state.kuota_pribadi_r4), step=5.0)
                st.session_state.kuota_motor = st.number_input("Sepeda Motor (R2) [L/Hari]", value=float(st.session_state.kuota_motor), step=2.0)
                st.session_state.kuota_penumpang = st.number_input("Mobil Penumpang Umum [L/Hari]", value=float(st.session_state.kuota_penumpang), step=10.0)
                st.session_state.kuota_barang = st.number_input("Truk Barang (R4+) [L/Hari]", value=float(st.session_state.kuota_barang), step=10.0)
                st.session_state.kuota_berat = st.number_input("Truk & Beban Berat [L/Hari]", value=float(st.session_state.kuota_berat), step=10.0)

            with col_s2:
                st.markdown("#### ⏱️ Batas Deteksi Fraud & Anomali")
                st.session_state.max_frekuensi_harian = st.number_input("Maks Frekuensi Isi per Hari (Mobil Helikopter)", value=int(st.session_state.max_frekuensi_harian), step=1)
                st.session_state.min_jeda_waktu = st.number_input("Minimum Jeda Waktu antar Transaksi [Menit]", value=int(st.session_state.min_jeda_waktu), step=5)
                st.session_state.batas_sekali_isi = st.number_input("Batas Maksimal Sekali Isi [Liter]", value=float(st.session_state.batas_sekali_isi), step=10.0)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
else:
    with tab1:
        st.info("📂 Silakan unggah file terlebih dahulu melalui tab **📁 Data Upload & Manajemen**.")
    with tab2:
        st.info("📂 Silakan unggah file terlebih dahulu melalui tab **📁 Data Upload & Manajemen**.")
    with tab3:
        st.info("📂 Silakan unggah file terlebih dahulu melalui tab **📁 Data Upload & Manajemen**.")

with tab_db:
    st.subheader("🗄️ Bank Database Arsip Riwayat Unduhan")
    st.markdown("<p style='color: #64748b; font-size: 0.85rem; margin-top: -10px; margin-bottom: 20px;'>Daftar seluruh file laporan dan data yang pernah Anda unduh tersimpan aman di database lokal. Anda dapat mengunduhnya kembali kapan pun diperlukan.</p>", unsafe_allow_html=True)

    cursor = db_conn.cursor()
    cursor.execute("SELECT id, waktu_unduh, jenis_laporan, nama_file, spbu_id, total_baris FROM riwayat_unduhan ORDER BY id DESC")
    rows = cursor.fetchall()

    if rows:
        df_db_view = pd.DataFrame(rows, columns=["ID", "Waktu Unduh", "Jenis Laporan", "Nama File", "ID SPBU", "Total Baris"])
        st.dataframe(df_db_view, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📥 Unduh Ulang File dari Database")
        
        selected_id = st.selectbox("Pilih ID File yang ingin diunduh kembali", options=[r[0] for r in rows], format_func=lambda x: f"ID #{x} - {[r[3] for r in rows if r[0] == x][0]} ([{ [r[1] for r in rows if r[0] == x][0] }])")

        if selected_id:
            cursor.execute("SELECT nama_file, file_data FROM riwayat_unduhan WHERE id = ?", (selected_id,))
            res = cursor.fetchone()
            if res:
                fname, fdata = res[0], res[1]
                st.download_button(
                    label=f"📥 Download Ulang: {fname}",
                    data=fdata,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    else:
        st.info("Belum ada riwayat unduhan yang tersimpan di database. Silakan lakukan unduh file pada tab **🔍 Detail Transaksi & Evidens Kamera Perangkat**.")
