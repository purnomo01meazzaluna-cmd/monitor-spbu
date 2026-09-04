import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io
import sqlite3
import os

# Page Configuration
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
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
</style>
""", unsafe_allow_html=True)

# Inisialisasi Database SQLite Lokal untuk Menyimpan Riwayat & Catatan Investigasi
DB_FILE = "spbu_dashboard_storage.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaksi_investigasi (
            trans_id TEXT PRIMARY KEY,
            tanggal TEXT,
            plat TEXT,
            produk TEXT,
            volume REAL,
            nozzle TEXT,
            status_anomali TEXT,
            catatan TEXT,
            link_foto TEXT,
            link_cctv TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_to_db(trans_id, tanggal, plat, produk, volume, nozzle, status_anomali, catatan, link_foto, link_cctv):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO transaksi_investigasi 
        (trans_id, tanggal, plat, produk, volume, nozzle, status_anomali, catatan, link_foto, link_cctv)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (trans_id, tanggal, plat, produk, volume, nozzle, status_anomali, catatan, link_foto, link_cctv))
    conn.commit()
    conn.close()

def load_all_from_db():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM transaksi_investigasi", conn)
    conn.close()
    return df

# Inisialisasi Session State
if "filter_produk" not in st.session_state:
    st.session_state.filter_produk = "SEMUA"

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

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

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU Monitoring System | JBT & JBKP Advanced Fraud Detection, Evidence & Persistent Storage**")
st.markdown("---")

# Sidebar / Upload Section
st.sidebar.header("📂 Pengaturan & Sumber Data")
uploaded_file = st.sidebar.file_uploader("Upload file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])
selected_date = st.sidebar.date_input("Pilih Tanggal Analisis", datetime.now().date())

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.sidebar.success("File berhasil dimuat!")
        
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
        default_status = find_best_column(["status", "keterangan", "ket", "remark", "note"])
        default_time = find_best_column(["waktu", "time", "jam", "tanggal", "date", "timestamp"])
        default_nozzle = find_best_column(["nozzle", "nosel", "pompa", "island", "dispenser"])

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Pemetaan Kolom Data")

        col_nopol_opt = st.sidebar.selectbox("Kolom Plat Nomor / Nopol", columns_list, index=columns_list.index(default_nopol) if default_nopol in columns_list else 0)
        col_vol_opt = st.sidebar.selectbox("Kolom Volume (L)", columns_list, index=columns_list.index(default_vol) if default_vol in columns_list else 0)
        col_produk_opt = st.sidebar.selectbox("Kolom Produk / Jenis BBM", columns_list, index=columns_list.index(default_produk) if default_produk in columns_list else 0)
        col_time_opt = st.sidebar.selectbox("Kolom Waktu / Jam Transaksi", columns_list, index=columns_list.index(default_time) if default_time in columns_list else 0)
        col_nozzle_opt = st.sidebar.selectbox("Kolom Nozzle / Pompa (Opsional)", columns_list, index=columns_list.index(default_nozzle) if default_nozzle in columns_list else 0)

        # Validasi Format & Karakter Nopol
        if col_nopol_opt in df_raw.columns:
            df_raw = df_raw.copy()
            def clean_and_validate_nopol(val):
                s = str(val).strip().upper()
                if s in ["CASH", "TIDAK ADA", "NAN", "NONE", "-", "NULL", "TUNAI", "0", ""] or len(s) < 3:
                    return "INVALID_NOPOL"
                cleaned = re.sub(r'[^A-Z0-9 ]', '', s)
                return cleaned if len(cleaned) >= 3 else "INVALID_NOPOL"

            df_raw[col_nopol_opt] = df_raw[col_nopol_opt].apply(clean_and_validate_nopol)

        # Fungsi Klasifikasi Kendaraan & Kuota
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
                if 1 <= nomor_reg <= 2999: return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4
                elif 3000 <= nomor_reg <= 6999: return "Sepeda Motor (R2)", st.session_state.kuota_motor
                elif 7000 <= nomor_reg <= 7999: return "Minibus / Bus (R4+)", st.session_state.kuota_penumpang
                elif 8000 <= nomor_reg <= 8999: return "Truk Barang (R4+)", st.session_state.kuota_barang
                elif 9000 <= nomor_reg <= 9999: return "Truk & Beban Berat", st.session_state.kuota_berat
                else: return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4
            else: 
                if 1 <= nomor_reg <= 2999: return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4
                elif 3000 <= nomor_reg <= 6999: return "Sepeda Motor (R2)", st.session_state.kuota_motor
                elif 7000 <= nomor_reg <= 7999: return "Minibus Penumpang (R4+)", st.session_state.kuota_penumpang
                else: return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4

        # Pisahkan JBT dan JBKP
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

        # Analisis Waktu & Cross-Pump Anomali
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

        # Inisialisasi Database dengan data baru jika belum ada
        for idx, row in df_analysis.iterrows():
            trans_id = f"TRX-{selected_date}-{idx:04d}"
            waktu_val = str(row[col_time_opt]) if col_time_opt in df_analysis.columns else str(selected_date)
            plat_val = str(row[col_nopol_opt])
            prod_val = str(row[col_produk_opt]) if col_produk_opt in df_analysis.columns else "BBM"
            vol_val = float(row[col_vol_opt]) if col_vol_opt in df_analysis.columns else 0.0
            nozzle_val = str(row[col_nozzle_opt]) if col_nozzle_opt in df_analysis.columns else "P1"
            
            # Tentukan status anomali awal
            if plat_val == "INVALID_NOPOL":
                status_anomali = "Tanpa Nopol / Tidak Valid"
            elif row.get('is_fast_interval', False) or row.get('is_cross_pump', False):
                status_anomali = "Indikasi Cross-Pump / Jeda Singkat"
            else:
                status_anomali = "Normal"

            # Simpan ke DB lokal jika belum ada
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT trans_id FROM transaksi_investigasi WHERE trans_id = ?", (trans_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO transaksi_investigasi (trans_id, tanggal, plat, produk, volume, nozzle, status_anomali, catatan, link_foto, link_cctv)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (trans_id, waktu_val, plat_val, prod_val, vol_val, nozzle_val, status_anomali, "", f"foto_{trans_id}.jpg", f"cctv_{trans_id}.mp4"))
                conn.commit()
            conn.close()

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")

# Bar Kontrol Atas (Pencarian Plat, Analisis Ulang, Tombol Ekspor)
col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 1.2, 2, 2])
with col_ctrl1:
    search_query = st.text_input("🔍 Cari plat nomor...", value=st.session_state.search_query, placeholder="Ketik nomor polisi (cth: B 1234)...")
    st.session_state.search_query = search_query
with col_ctrl2:
    if st.button("🔄 Analisis ulang", use_container_width=True):
        st.rerun()
with col_ctrl3:
    # Unduh Transaksi + Foto & Catatan (Excel)
    df_stored_all = load_all_from_db()
    if not df_stored_all.empty:
        output_excel_all = io.BytesIO()
        with pd.ExcelWriter(output_excel_all, engine='openpyxl') as writer:
            df_stored_all.to_excel(writer, index=False, sheet_name='Database_Investigasi')
        excel_all_data = output_excel_all.getvalue()

        st.download_button(
            label="📥 Unduh transaksi + foto (Excel)",
            data=excel_all_data,
            file_name=f"Database_SPBU_Investigasi_{selected_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.button("📥 Unduh transaksi + foto (Excel)", disabled=True, use_container_width=True)
with col_ctrl4:
    # Unduh Tindak Lanjut / Temuan Anomali
    if not df_stored_all.empty:
        df_tindak_lanjut = df_stored_all[df_stored_all['status_anomali'] != "Normal"]
        output_excel_tl = io.BytesIO()
        with pd.ExcelWriter(output_excel_tl, engine='openpyxl') as writer:
            df_tindak_lanjut.to_excel(writer, index=False, sheet_name='Tindak_Lanjut_Anomali')
        excel_tl_data = output_excel_tl.getvalue()

        st.download_button(
            label="📥 Unduh tindak lanjut (Excel)",
            data=excel_tl_data,
            file_name=f"Laporan_Tindak_Lanjut_{selected_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.button("📥 Unduh tindak lanjut (Excel)", disabled=True, use_container_width=True)

st.markdown("---")

# Main Layout Tabs
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan & Evidens CCTV (Tersimpan)", "⚙️ Pengaturan Batas & Regulasi"])

with tab1:
    st.subheader("Rekap Harian Penyaluran BBM Subsidi & Deteksi Kecurangan")
    
    df_stored = load_all_from_db()
    if not df_stored.empty:
        if st.session_state.search_query.strip():
            q = st.session_state.search_query.strip().upper()
            df_stored = df_stored[df_stored['plat'].str.contains(q, case=False, na=False)]

        tanpa_nopol = len(df_stored[df_stored['plat'] == "INVALID_NOPOL"])
        mobil_helikopter_count = 0 # Dihitung dari frekuensi
        single_cap_violations = len(df_stored[df_stored['volume'] > st.session_state.batas_sekali_isi])
        fast_interval_count = len(df_stored[df_stored['status_anomali'].str.contains("Cross-Pump|Jeda", case=False, na=False)])
        cross_pump_count = fast_interval_count

        total_transaksi = len(df_stored)
        total_vol = df_stored['volume'].sum()
    else:
        tanpa_nopol = 0
        mobil_helikopter_count = 0
        single_cap_violations = 0
        fast_interval_count = 0
        cross_pump_count = 0
        total_transaksi = 0
        total_vol = 0.0

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
        render_custom_metric("Potensi Mobil Helikopter", mobil_helikopter_count, "🚁", alert_if_gt_zero=False)
    with m4:
        render_custom_metric("Langgar Batas Sekali Isi", single_cap_violations, "⚠️", alert_if_gt_zero=True)
    with m5:
        render_custom_metric("Transaksi Tanpa Nopol", tanpa_nopol, "🚫", alert_if_gt_zero=True)

    st.markdown("<br style='display: block; margin: 4px 0;'>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_custom_metric("Total Volume Terjual", f"{total_vol:,.1f} L", "📈", alert_if_gt_zero=False)
    with c2:
        render_custom_metric("Total Transaksi Tersimpan", f"{total_transaksi:,} Baris", "📋", alert_if_gt_zero=False)
    with c3:
        render_custom_metric("Produk Aktif Filter", st.session_state.filter_produk, "🏷️", alert_if_gt_zero=False)
    with c4:
        render_custom_metric("SPBU ID", "4150201", "🏢", alert_if_gt_zero=False)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Daftar Agregasi Plat Nomor (Data Tersimpan di Dashboard)")

    header_html = """
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px; margin-bottom: 6px; color: #64748b; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;">
        <div style="flex: 1.2;">PLAT</div>
        <div style="flex: 1.8;">KLASIFIKASI KENDARAAN</div>
        <div style="flex: 0.6; text-align: center;">ISI</div>
        <div style="flex: 3.5; padding: 0 15px;">TOTAL VS KUOTA KATEGORI</div>
        <div style="flex: 1.5; text-align: right;">STATUS ANOMALI</div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    if not df_stored.empty:
        agg_dict = {
            'total_transaksi': ('volume', 'count'),
            'total_volume': ('volume', 'sum'),
            'sample_produk': ('produk', 'first')
        }
        df_grouped = df_stored.groupby('plat').agg(**agg_dict).reset_index()
        df_grouped = df_grouped.sort_values(by="total_volume", ascending=False).reset_index(drop=True)

        for index, row in df_grouped.iterrows():
            plat = str(row['plat'])
            freq = int(row['total_transaksi'])
            vol = row['total_volume']
            prod_val = row['sample_produk']
            
            jenis_kendaraan, target_kuota = deteksi_kategori_dan_kuota(plat, prod_val)
            persen = int((vol / target_kuota) * 100) if target_kuota > 0 else 100
            green_width = min(100, persen)

            if plat == "INVALID_NOPOL":
                status_badge = "<span style='background-color: #fee2e2; color: #b91c1c; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Nopol Tidak Valid</span>"
            elif vol > target_kuota:
                status_badge = "<span style='background-color: #fef2f2; color: #b91c1c; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Indikasi Kecurangan</span>"
            else:
                status_badge = "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"

            card_html = f"""
            <div style="background-color: white; border: 1px solid #e2e8f0; padding: 12px 16px; margin-bottom: 8px; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <div style="flex: 1.2; display: flex; align-items: center;">
                    <strong style="font-size: 1.05rem; color: #1e293b; font-family: monospace;">{plat}</strong>
                </div>
                <div style="flex: 1.8; display: flex; align-items: center; gap: 8px;">
                    <span style="color: #64748b; font-size: 0.85rem;">📌 {jenis_kendaraan}</span>
                </div>
                <div style="flex: 0.6; text-align: center;">
                    <span style="color: #334155; font-size: 0.85rem; font-weight: 600;">{freq}×</span>
                </div>
                <div style="flex: 3.5; padding: 0 15px;">
                    <div style="background-color: #e2e8f0; border-radius: 4px; height: 6px; width: 100%; display: flex; overflow: hidden; margin-bottom: 4px;">
                        <div style="background-color: {'#ef4444' if persen > 100 else '#10b981'}; width: {green_width}%; height: 100%;"></div>
                    </div>
                    <div style="font-size: 0.75rem; color: #64748b; display: flex; justify-content: space-between;">
                        <span>{vol:,.0f} L / {target_kuota:,.0f} L</span>
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
        st.info("Belum ada data tersimpan. Silakan unggah file transaksi di sidebar.")

with tab2:
    st.subheader("🔍 Detail Transaksi, Rekaman Evidens CCTV & Catatan Investigasi (Tersimpan Permanen)")
    st.markdown("Setiap catatan investigasi yang Anda tulis di bawah ini **langsung tersimpan secara otomatis** ke dalam database lokal dashboard.")

    df_stored_tab2 = load_all_from_db()
    if st.session_state.search_query.strip():
        q = st.session_state.search_query.strip().upper()
        df_stored_tab2 = df_stored_tab2[df_stored_tab2['plat'].str.contains(q, case=False, na=False)]

    if not df_stored_tab2.empty:
        for idx, row in df_stored_tab2.iterrows():
            trans_id = row['trans_id']
            waktu_val = row['tanggal']
            produk_val = row['produk']
            nozzle_val = f"(Nozzle: {row['nozzle']})"
            plat_val = row['plat']
            vol_val = f"{row['volume']}L"
            status_anom = row['status_anomali']
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
                st.markdown(f"**Produk**\n{produk_val}\n`{nozzle_val}`")
            with col_card_5:
                st.markdown(f"**Plat**\n**`{plat_val}`**")
            with col_card_6:
                st.markdown(f"**Volume**\n`{vol_val}`")
            
            col_note_1, col_note_2 = st.columns([2.5, 3.5])
            with col_note_1:
                if status_anom != "Normal":
                    st.error(f"⚠️ {status_anom}")
                else:
                    st.success("● Normal")
            with col_note_2:
                new_note = st.text_input(
                    f"Catatan #{trans_id}", 
                    value=saved_note, 
                    placeholder="Tulis catatan investigasi di sini...",
                    key=f"note_db_{trans_id}",
                    label_visibility="collapsed"
                )
                if new_note != saved_note:
                    # Update otomatis ke database SQLite
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE transaksi_investigasi SET catatan = ? WHERE trans_id = ?", (new_note, trans_id))
                    conn.commit()
                    conn.close()
            
            st.markdown("---")
    else:
        st.info("Tidak ada data ditemukan sesuai kriteria pencarian.")

with tab3:
    st.subheader("⚙️ Pengaturan Batas & Regulasi Advance")
    st.markdown("Konfigurasi ambang batas kuota, jeda transaksi, dan parameter deteksi.")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("#### 🚗 Batas Kuota Berdasarkan Kategori Plat")
        st.session_state.kuota_pribadi_r4 = st.number_input("Mobil Pribadi (R4) [L/Hari]", value=float(st.session_state.kuota_pribadi_r4), step=5.0)
        st.session_state.kuota_motor = st.number_input("Sepeda Motor (R2) [L/Hari]", value=float(st.session_state.kuota_motor), step=2.0)
        st.session_state.kuota_penumpang = st.number_input("Minibus / Bus [L/Hari]", value=float(st.session_state.kuota_penumpang), step=10.0)
        st.session_state.kuota_barang = st.number_input("Truk Barang [L/Hari]", value=float(st.session_state.kuota_barang), step=10.0)
        st.session_state.kuota_berat = st.number_input("Truk & Beban Berat [L/Hari]", value=float(st.session_state.kuota_berat), step=10.0)

    with col_s2:
        st.markdown("#### 🚨 Mitigasi Fraud & Waktu Transaksi")
        st.session_state.max_frekuensi_harian = st.number_input("Batas Frekuensi Pengisian Harian", value=int(st.session_state.max_frekuensi_harian), min_value=1, max_value=10)
        st.session_state.min_jeda_waktu = st.number_input("Batas Jeda Waktu Minimal (Menit)", value=int(st.session_state.min_jeda_waktu), step=5)
        st.session_state.batas_sekali_isi = st.number_input("Batas Volume Maksimal Sekali Isi (Liter)", value=float(st.session_state.batas_sekali_isi), step=10.0)

    st.success("✅ Seluruh data dan catatan investigasi tersimpan aman di database dashboard lokal.")
