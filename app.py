import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io

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
    st.session_state.min_jeda_waktu = 30  # dalam menit
if "batas_sekali_isi" not in st.session_state:
    st.session_state.batas_sekali_isi = 200.0

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU Monitoring System | JBT & JBKP Advanced Fraud Detection**")
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

        # --- FITUR 4: Validasi Format & Karakter Nopol (Regex Plate Validator & Cleaner) ---
        if col_nopol_opt in df_raw.columns:
            df_raw = df_raw.copy()
            
            def clean_and_validate_nopol(val):
                s = str(val).strip()
                s_upper = s.upper()
                # Cek kata sampah / invalid input
                invalid_keywords = ["CASH", "TIDAK ADA", "NAN", "NONE", "-", "NULL", "TUNAI", "0", ""]
                if s_upper in invalid_keywords or len(s) < 3:
                    return "INVALID_NOPOL"
                # Bersihkan karakter aneh, pertahankan huruf, angka, dan spasi tengah
                cleaned = re.sub(r'[^A-Z0-9 ]', '', s_upper)
                return cleaned if len(cleaned) >= 3 else "INVALID_NOPOL"

            df_raw[col_nopol_opt] = df_raw[col_nopol_opt].apply(clean_and_validate_nopol)

        # Fungsi Klasifikasi Kendaraan & Kuota Berdasarkan JBT / JBKP & Rentang Angka Plat
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
                    return "Minibus / Bus (R4+)", st.session_state.kuota_penumpang
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
                    return "Minibus Penumpang (R4+)", st.session_state.kuota_penumpang
                else:
                    return "Mobil Pribadi (R4)", st.session_state.kuota_pribadi_r4

        # Pisahkan data JBT dan JBKP
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

        # --- FITUR 1 & 2: ANALISIS WAKTU (Time Interval) & CROSS-PUMP ANOMALI ---
        df_analysis = df_display.copy()
        if col_time_opt in df_analysis.columns:
            df_analysis['parsed_time'] = pd.to_datetime(df_analysis[col_time_opt], errors='coerce')
            df_analysis = df_analysis.sort_values(by=[col_nopol_opt, 'parsed_time'])
            
            # Hitung selisih waktu dengan transaksi sebelumnya untuk nopol yang sama
            df_analysis['prev_time'] = df_analysis.groupby(col_nopol_opt)['parsed_time'].shift(1)
            df_analysis['diff_minutes'] = (df_analysis['parsed_time'] - df_analysis['prev_time']).dt.total_seconds() / 60.0
            
            # Deteksi Jeda Waktu Terlalu Singkat (< min_jeda_waktu)
            df_analysis['is_fast_interval'] = df_analysis['diff_minutes'] <= st.session_state.min_jeda_waktu
        else:
            df_analysis['diff_minutes'] = None
            df_analysis['is_fast_interval'] = False

        # Deteksi Cross-Pump (Nopol sama isi di nozzle/pompa berbeda dalam rentang waktu < 60 menit)
        if col_nozzle_opt in df_analysis.columns and col_time_opt in df_analysis.columns:
            df_analysis['prev_nozzle'] = df_analysis.groupby(col_nopol_opt)[col_nozzle_opt].shift(1)
            df_analysis['is_cross_pump'] = (
                df_analysis['is_fast_interval'] & 
                (df_analysis[col_nozzle_opt].astype(str) != df_analysis['prev_nozzle'].astype(str)) &
                (df_analysis['diff_minutes'] <= 60)
            )
        else:
            df_analysis['is_cross_pump'] = False

        # Main Layout Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan Batas & Regulasi"])

        with tab1:
            st.subheader("Rekap Harian Penyaluran BBM Subsidi & Deteksi Kecurangan")
            
            if not df_display.empty and col_nopol_opt in df_display.columns:
                agg_dict_m = {
                    'total_volume': (col_vol_opt, lambda x: pd.to_numeric(x, errors='coerce').sum()),
                    'freq': (col_vol_opt, 'count')
                }
                df_g_metric = df_analysis.groupby(col_nopol_opt).agg(**agg_dict_m).reset_index()
                
                plat_lewat_kuota = len(df_g_metric[df_g_metric['total_volume'] > st.session_state.kuota_berat])
                tanpa_nopol = len(df_analysis[df_analysis[col_nopol_opt] == "INVALID_NOPOL"])
                mobil_helikopter_count = len(df_g_metric[df_g_metric['freq'] > st.session_state.max_frekuensi_harian])
                
                vol_numeric = pd.to_numeric(df_analysis[col_vol_opt], errors='coerce').fillna(0)
                single_cap_violations = len(df_analysis[vol_numeric > st.session_state.batas_sekali_isi])
                
                # Metrik Fitur Baru 1 & 2
                fast_interval_count = int(df_analysis['is_fast_interval'].sum()) if 'is_fast_interval' in df_analysis.columns else 0
                cross_pump_count = int(df_analysis['is_cross_pump'].sum()) if 'is_cross_pump' in df_analysis.columns else 0
            else:
                plat_lewat_kuota = 0
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

            # Baris Metrik Peringatan Anomali Advance
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                render_custom_metric("Jeda Waktu Singkat (<30m)", fast_interval_count, "⏱️", alert_if_gt_zero=True)
            with m2:
                render_custom_metric("Anomali Cross-Pump", cross_pump_count, "🔀", alert_if_gt_zero=True)
            with m3:
                render_custom_metric("Potensi Helikopter", mobil_helikopter_count, "🚁", alert_if_gt_zero=True)
            with m4:
                render_custom_metric("Langgar Sekali Isi", single_cap_violations, "⚠️", alert_if_gt_zero=True)
            with m5:
                render_custom_metric("Nopol Tidak Valid", tanpa_nopol, "🚫", alert_if_gt_zero=True)

            st.markdown("<br style='display: block; margin: 4px 0;'>", unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_custom_metric("Total Volume Terjual", f"{total_vol:,.1f} L", "📈", alert_if_gt_zero=False)
            with c2:
                render_custom_metric("Total Transaksi", f"{total_transaksi:,} Baris", "📋", alert_if_gt_zero=False)
            with c3:
                render_custom_metric("Produk Aktif Filter", st.session_state.filter_produk, "🏷️", alert_if_gt_zero=False)
            with c4:
                render_custom_metric("SPBU ID", "4150201", "🏢", alert_if_gt_zero=False)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- FITUR 3: Ekspor Laporan Anomali (Tombol Unduh Excel) ---
            st.markdown("#### 📥 Unduh Laporan Temuan Anomali & Pelanggaran")
            
            # Filter data yang mengalami anomali (Melebihi kuota, jeda singkat, atau cross-pump)
            if not df_analysis.empty and col_nopol_opt in df_analysis.columns:
                df_anomali_export = df_analysis[
                    (df_analysis['is_fast_interval'] == True) | 
                    (df_analysis['is_cross_pump'] == True) |
                    (df_analysis[col_nopol_opt] == "INVALID_NOPOL")
                ].copy()

                # Buat file excel di dalam memori
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df_anomali_export.to_excel(writer, index=False, sheet_name='Temuan_Anomali')
                excel_data = output_excel.getvalue()

                st.download_button(
                    label="📥 Unduh Laporan Temuan Anomali (.xlsx)",
                    data=excel_data,
                    file_name=f"Laporan_Anomali_SPBU_{selected_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.info("Data belum tersedia untuk diekspor.")

            st.markdown("---")
            
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
            st.markdown("### Daftar Agregasi Plat Nomor (Dilengkapi Validasi Waktu & Nozzle)")

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
                        status_badge = "<span style='background-color: #fef2f2; color: #b91c1c; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Indikasi Kecurangan</span>"
                    elif vol > st.session_state.kuota_pribadi_r4:
                        status_badge = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>"
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
                            <span style="color: {'#b91c1c' if is_helikopter else '#334155'}; font-size: 0.85rem; font-weight: 600;">{freq}×</span>
                        </div>
                        <div style="flex: 3.5; padding: 0 15px;">
                            <div style="background-color: #e2e8f0; border-radius: 4px; height: 6px; width: 100%; display: flex; overflow: hidden; margin-bottom: 4px;">
                                <div style="background-color: {'#ef4444' if persen > 100 else '#10b981'}; width: {green_width}%; height: 100%;"></div>
                            </div>
                            <div style="font-size: 0.75rem; color: #64748b; display: flex; justify-content: space-between;">
                                <span>{vol:,.0f} L / {target_kuota:,.0f} L {'(Jeda Singkat/Cross-Pump Terdeteksi)' if (is_fast or is_cp) else ''}</span>
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
            st.subheader("Tabel Detail Transaksi Beserta Analisis Waktu & Nozzle")
            st.dataframe(df_analysis, use_container_width=True)

        with tab3:
            st.subheader("⚙️ Pengaturan Batas & Regulasi Advance")
            st.markdown("Konfigurasi ambang batas waktu, jeda transaksi, kuota, serta pembersihan data nopol otomatis.")

            col_s1, col_s2 = st.columns(2)

            with col_s1:
                st.markdown("#### 🚗 Batas Kuota Berdasarkan Kategori Plat")
                st.session_state.kuota_pribadi_r4 = st.number_input(
                    "Angka 0001–2999: Mobil Pribadi (R4) [L/Hari]", 
                    value=float(st.session_state.kuota_pribadi_r4),
                    step=5.0
                )
                st.session_state.kuota_motor = st.number_input(
                    "Angka 3000–6999: Sepeda Motor (R2) [L/Hari]", 
                    value=float(st.session_state.kuota_motor),
                    step=2.0
                )
                st.session_state.kuota_penumpang = st.number_input(
                    "Angka 7000–7999: Minibus / Bus Penumpang [L/Hari]", 
                    value=float(st.session_state.kuota_penumpang),
                    step=10.0
                )
                st.session_state.kuota_barang = st.number_input(
                    "Angka 8000–8999 (JBT): Truk Barang [L/Hari]", 
                    value=float(st.session_state.kuota_barang),
                    step=10.0
                )
                st.session_state.kuota_berat = st.number_input(
                    "Angka 9000–9999 (JBT): Truk & Beban Berat [L/Hari]", 
                    value=float(st.session_state.kuota_berat),
                    step=10.0
                )

            with col_s2:
                st.markdown("#### 🚨 Mitigasi Fraud & Waktu Transaksi")
                st.session_state.max_frekuensi_harian = st.number_input(
                    "Batas Frekuensi Pengisian Harian (Kali/Hari)", 
                    value=int(st.session_state.max_frekuensi_harian),
                    min_value=1,
                    max_value=10,
                    step=1
                )
                st.session_state.min_jeda_waktu = st.number_input(
                    "Batas Jeda Waktu Pengisian Minimal (Menit)", 
                    value=int(st.session_state.min_jeda_waktu),
                    step=5,
                    help="Mendeteksi transaksi bolak-balik terlalu cepat (< 30 menit) di SPBU."
                )
                st.session_state.batas_sekali_isi = st.number_input(
                    "Batas Volume Maksimal Sekali Isi / Cap (Liter)", 
                    value=float(st.session_state.batas_sekali_isi),
                    step=10.0
                )

            st.success("✅ Seluruh fitur advance (Deteksi Jeda Waktu, Cross-Pump, Regex Validator, & Ekspor Excel) aktif sepenuhnya.")

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
else:
    st.info("👈 Silakan unggah file transaksi Excel (.xlsx) atau CSV melalui panel di sebelah kiri.")
