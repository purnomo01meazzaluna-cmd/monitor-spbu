import streamlit as st
import pandas as pd
from datetime import datetime

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
    
    /* Style untuk card metrik normal */
    .custom-metric-card {
        background-color: #ffffff;
        padding: 12px 16px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* Style khusus card metrik saat alert (Background Merah) */
    .custom-metric-card-alert {
        background-color: #fee2e2 !important;
        padding: 12px 16px;
        border-radius: 6px;
        border: 1px solid #f87171 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Session State untuk Filter & Pengaturan Batas Lanjutan
if "filter_produk" not in st.session_state:
    st.session_state.filter_produk = "SEMUA"

# 1. Batas Kuota Berdasarkan Jenis Kendaraan (Aturan BPH Migas)
if "kuota_pribadi_r4" not in st.session_state:
    st.session_state.kuota_pribadi_r4 = 60.0
if "kuota_umum_r4" not in st.session_state:
    st.session_state.kuota_umum_r4 = 80.0
if "kuota_truk_r6" not in st.session_state:
    st.session_state.kuota_truk_r6 = 200.0

# 2. Batas Frekuensi Pengisian Harian (Mencegah Mobil Helikopter)
if "max_frekuensi_harian" not in st.session_state:
    st.session_state.max_frekuensi_harian = 2

# 3. Batas Jeda Waktu Pengisian Minimal (Time Interval Threshold)
if "min_jeda_waktu" not in st.session_state:
    st.session_state.min_jeda_waktu = 30  # dalam menit

# 4. Batas Volume Maksimal Sekali Isi (Single Transaction Cap)
if "batas_sekali_isi" not in st.session_state:
    st.session_state.batas_sekali_isi = 200.0

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU Monitoring System | Jawa Tengah**")
st.markdown("---")

# Sidebar / Upload Section
st.sidebar.header("📂 Pengaturan & Sumber Data")
uploaded_file = st.sidebar.file_uploader("Upload file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])
selected_date = st.sidebar.date_input("Pilih Tanggal Analisis", datetime.now().date())

if uploaded_file is not None:
    try:
        # Membaca file
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.sidebar.success("File berhasil dimuat!")
        
        # Normalisasi nama kolom
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

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Pemetaan Kolom Data")

        col_nopol_opt = st.sidebar.selectbox("Kolom Plat Nomor / Nopol", columns_list, index=columns_list.index(default_nopol) if default_nopol in columns_list else 0)
        col_vol_opt = st.sidebar.selectbox("Kolom Volume (L)", columns_list, index=columns_list.index(default_vol) if default_vol in columns_list else 0)
        col_produk_opt = st.sidebar.selectbox("Kolom Produk / Jenis BBM", columns_list, index=columns_list.index(default_produk) if default_produk in columns_list else 0)
        col_status_opt = st.sidebar.selectbox("Kolom Status / Keterangan", columns_list, index=columns_list.index(default_status) if default_status in columns_list else 0)
        col_time_opt = st.sidebar.selectbox("Kolom Waktu / Jam Transaksi (Opsional)", columns_list, index=columns_list.index(default_time) if default_time in columns_list else 0)

        # Bersihkan kata "Cash" pada data mentah untuk kolom nopol
        if col_nopol_opt in df_raw.columns:
            df_raw = df_raw.copy()
            df_raw[col_nopol_opt] = (
                df_raw[col_nopol_opt]
                .astype(str)
                .str.replace(r'(?i)\bcash\b', '', regex=True)
                .str.strip()
            )

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

        # Main Layout Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan Batas & Regulasi"])

        with tab1:
            st.subheader("Rekap Harian Penyaluran BBM Subsidi (Data File Upload)")
            
            # --- PERHITUNGAN ANOMALI & METRIK ---
            if not df_display.empty and col_nopol_opt in df_display.columns:
                agg_dict_m = {
                    'total_volume': (col_vol_opt, lambda x: pd.to_numeric(x, errors='coerce').sum()),
                    'freq': (col_vol_opt, 'count')
                }
                df_g_metric = df_display.groupby(col_nopol_opt).agg(**agg_dict_m).reset_index()
                
                # Anomali 1: Plat melebihi kuota absolut (menggunakan patokan truk/bus 200L sebagai batas maksimal umum)
                limit_kuota_max = st.session_state.kuota_truk_r6
                plat_lewat_kuota = len(df_g_metric[df_g_metric['total_volume'] > limit_kuota_max])
                
                # Anomali 2: Transaksi tanpa nopol
                nopol_series = df_display[col_nopol_opt].astype(str).str.strip().str.upper()
                tanpa_nopol = len(df_display[nopol_series.isin(["", "NAN", "NONE", "-", "NULL"])])

                # Anomali 3: Mobil Helikopter (Frekuensi > Batas Harian)
                mobil_helikopter_count = len(df_g_metric[df_g_metric['freq'] > st.session_state.max_frekuensi_harian])

                # Anomali 4: Single Transaction Cap (Volume sekali isi > batas_sekali_isi)
                vol_numeric = pd.to_numeric(df_display[col_vol_opt], errors='coerce').fillna(0)
                single_cap_violations = len(df_display[vol_numeric > st.session_state.batas_sekali_isi])
                
                perlu_periksa_count = len(df_g_metric[df_g_metric['total_volume'] > st.session_state.kuota_pribadi_r4])
                normal_count = len(df_g_metric) - perlu_periksa_count
            else:
                plat_lewat_kuota = 0
                tanpa_nopol = 0
                mobil_helikopter_count = 0
                single_cap_violations = 0
                perlu_periksa_count = 0
                normal_count = 0

            # Fungsi bantuan metrik kustom
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

            # Baris 1: Metrik Peringatan / Anomali Lanjutan
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                render_custom_metric("Plat Lewat Kuota Maks (R6)", plat_lewat_kuota, "⛽", alert_if_gt_zero=True)
            with m2:
                render_custom_metric("Potensi Mobil Helikopter", mobil_helikopter_count, "🚁", alert_if_gt_zero=True)
            with m3:
                render_custom_metric("Langgar Batas Sekali Isi", single_cap_violations, "⚠️", alert_if_gt_zero=True)
            with m4:
                render_custom_metric("Transaksi Tanpa Nopol", tanpa_nopol, "🚫", alert_if_gt_zero=True)

            st.markdown("<br style='display: block; margin: 4px 0;'>", unsafe_allow_html=True)

            # Baris 2: Ringkasan Utama
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

            # Tombol Filter Interaktif
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
            st.markdown("### Daftar Agregasi Plat Nomor Berdasarkan File Upload")

            header_html = """
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 6px 16px; margin-bottom: 6px; color: #64748b; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;">
                <div style="flex: 1.2;">PLAT</div>
                <div style="flex: 1.8;">ESTIMASI KENDARAAN (BPH MIGAS)</div>
                <div style="flex: 0.6; text-align: center;">ISI</div>
                <div style="flex: 3.5; padding: 0 15px;">TOTAL VS KUOTA JENIS</div>
                <div style="flex: 1.5; text-align: right;">STATUS</div>
            </div>
            """
            st.markdown(header_html, unsafe_allow_html=True)

            if not df_display.empty and col_nopol_opt in df_display.columns:
                agg_dict = {
                    'total_transaksi': (col_vol_opt, 'count'),
                    'total_volume': (col_vol_opt, lambda x: pd.to_numeric(x, errors='coerce').sum())
                }

                df_grouped = df_display.groupby(col_nopol_opt).agg(**agg_dict).reset_index()
                df_grouped = df_grouped.sort_values(by="total_volume", ascending=False).reset_index(drop=True)

                for index, row in df_grouped.iterrows():
                    plat = str(row[col_nopol_opt])
                    freq = int(row['total_transaksi'])
                    vol = row['total_volume']
                    
                    plat_upper = plat.upper()
                    # Penentuan jenis kendaraan berdasarkan volume dan estimasi aturan BPH Migas
                    if vol > st.session_state.kuota_umum_r4:
                        jenis_kendaraan = "Truk / Bus (R6+)"
                        target_kuota = st.session_state.kuota_truk_r6
                    elif vol > st.session_state.kuota_pribadi_r4:
                        jenis_kendaraan = "Angkutan Umum / Barang (R4)"
                        target_kuota = st.session_state.kuota_umum_r4
                    else:
                        jenis_kendaraan = "Mobil Pribadi (R4)"
                        target_kuota = st.session_state.kuota_pribadi_r4

                    # Indikasi pelanggaran frekuensi (Mobil Helikopter)
                    is_helikopter = freq > st.session_state.max_frekuensi_harian

                    persen = int((vol / target_kuota) * 100) if target_kuota > 0 else 100
                    green_width = min(100, persen)

                    if vol > target_kuota or is_helikopter:
                        status_badge = "<span style='background-color: #fef2f2; color: #b91c1c; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Melebihi Batas</span>"
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
                            <span style="color: #64748b; font-size: 0.85rem;">≈ {jenis_kendaraan}</span>
                        </div>
                        <div style="flex: 0.6; text-align: center;">
                            <span style="color: {'#b91c1c' if is_helikopter else '#334155'}; font-size: 0.85rem; font-weight: 600;" title="{'Frekuensi melebihi batas wajar (Helikopter)' if is_helikopter else ''}">{freq}×</span>
                        </div>
                        <div style="flex: 3.5; padding: 0 15px;">
                            <div style="background-color: #e2e8f0; border-radius: 4px; height: 6px; width: 100%; display: flex; overflow: hidden; margin-bottom: 4px;">
                                <div style="background-color: {'#ef4444' if persen > 100 else '#10b981'}; width: {green_width}%; height: 100%;"></div>
                            </div>
                            <div style="font-size: 0.75rem; color: #64748b; display: flex; justify-content: space-between;">
                                <span>{vol:,.0f} L / {target_kuota:,.0f} L (Batas Kategori)</span>
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
            st.subheader("Tabel Mentah Data Upload")
            st.dataframe(df_raw, use_container_width=True)

        with tab3:
            st.subheader("⚙️ Pengaturan Batas & Regulasi BPH Migas")
            st.markdown("Sesuaikan parameter nilai ambang batas (*threshold*) di bawah untuk validasi transaksi secara otomatis:")

            col_s1, col_s2 = st.columns(2)

            with col_s1:
                st.markdown("#### 🚗 1. Batas Kuota Berdasarkan Jenis Kendaraan")
                st.session_state.kuota_pribadi_r4 = st.number_input(
                    "Mobil Pribadi Roda 4 (L / Hari)", 
                    value=float(st.session_state.kuota_pribadi_r4),
                    step=5.0,
                    help="Aturan BPH Migas: Maksimal 60 Liter/hari."
                )
                st.session_state.kuota_umum_r4 = st.number_input(
                    "Angkutan Umum / Barang Roda 4 (L / Hari)", 
                    value=float(st.session_state.kuota_umum_r4),
                    step=5.0,
                    help="Aturan BPH Migas: Maksimal 80 Liter/hari."
                )
                st.session_state.kuota_truk_r6 = st.number_input(
                    "Truk / Bus Roda 6 atau Lebih (L / Hari)", 
                    value=float(st.session_state.kuota_truk_r6),
                    step=10.0,
                    help="Aturan BPH Migas: Maksimal 200 Liter/hari."
                )

            with col_s2:
                st.markdown("#### 🚨 2, 3 & 4. Mitigasi Fraud & Kesalahan Input")
                st.session_state.max_frekuensi_harian = st.number_input(
                    "Batas Frekuensi Pengisian Harian (Kali)", 
                    value=int(st.session_state.max_frekuensi_harian),
                    min_value=1,
                    max_value=10,
                    step=1,
                    help="Mencegah modus 'Mobil Helikopter' (pengisian berulang kali dalam sehari untuk ditimbun)."
                )
                st.session_state.min_jeda_waktu = st.number_input(
                    "Batas Jeda Waktu Pengisian Minimal (Menit)", 
                    value=int(st.session_state.min_jeda_waktu),
                    step=5,
                    help="Mendeteksi transaksi bolak-balik dalam waktu singkat di SPBU yang sama."
                )
                st.session_state.batas_sekali_isi = st.number_input(
                    "Batas Volume Maksimal Sekali Isi / Cap (Liter)", 
                    value=float(st.session_state.batas_sekali_isi),
                    step=10.0,
                    help="Mencegah kesalahan input operator (typo) atau transaksi anomali skala besar."
                )

            st.success("✅ Seluruh perubahan parameter batas otomatis tersimpan dan memperbarui perhitungan metrik secara *real-time*.")

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
else:
    st.info("👈 Silakan unggah file transaksi Excel (.xlsx) atau CSV melalui panel di sebelah kiri.")
