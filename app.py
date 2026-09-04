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

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU Monitoring System | Jawa Tengah**")
st.markdown("---")

# Sidebar / Upload Section
st.sidebar.header("📂 Pengaturan & Sumber Data")
uploaded_file = st.sidebar.file_uploader("Upload file Excel (.xlsx) atau CSV", type=["xlsx", "csv"])
selected_date = st.sidebar.date_input("Pilih Tanggal Analisis", datetime.now().date())

# Inisialisasi session state
if "filter_produk" not in st.session_state:
    st.session_state.filter_produk = "SEMUA"

if "batas_jbt" not in st.session_state:
    st.session_state.batas_jbt = 60.0
if "batas_jbkp_r4" not in st.session_state:
    st.session_state.batas_jbkp_r4 = 60.0
if "batas_jbkp_2" not in st.session_state:
    st.session_state.batas_jbkp_2 = 60.0

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

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Pemetaan Kolom Data")

        col_nopol_opt = st.sidebar.selectbox("Kolom Plat Nomor / Nopol", columns_list, index=columns_list.index(default_nopol) if default_nopol in columns_list else 0)
        col_vol_opt = st.sidebar.selectbox("Kolom Volume (L)", columns_list, index=columns_list.index(default_vol) if default_vol in columns_list else 0)
        col_produk_opt = st.sidebar.selectbox("Kolom Produk / Jenis BBM", columns_list, index=columns_list.index(default_produk) if default_produk in columns_list else 0)
        col_status_opt = st.sidebar.selectbox("Kolom Status / Keterangan", columns_list, index=columns_list.index(default_status) if default_status in columns_list else 0)

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
            limit_kuota = st.session_state.batas_jbt
        elif st.session_state.filter_produk == "JBKP":
            df_display = df_jbkp
            limit_kuota = st.session_state.batas_jbkp_r4
        else:
            df_display = df_raw
            limit_kuota = st.session_state.batas_jbt

        total_transaksi = len(df_display)
        total_vol = pd.to_numeric(df_display[col_vol_opt], errors='coerce').fillna(0).sum() if col_vol_opt in df_display.columns else 0.0

        # Main Layout Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])

        with tab1:
            st.subheader("Rekap Harian Penyaluran BBM Subsidi (Data File Upload)")
            
            # --- PERHITUNGAN METRIK TERHUBUNG DENGAN BATAS KATEGORI ---
            if not df_display.empty and col_nopol_opt in df_display.columns:
                agg_dict_m = {
                    'total_volume': (col_vol_opt, lambda x: pd.to_numeric(x, errors='coerce').sum())
                }
                df_g_metric = df_display.groupby(col_nopol_opt).agg(**agg_dict_m).reset_index()
                
                plat_lewat_kuota = len(df_g_metric[df_g_metric['total_volume'] > limit_kuota])
                
                nopol_series = df_display[col_nopol_opt].astype(str).str.strip().str.upper()
                tanpa_nopol = len(df_display[nopol_series.isin(["", "NAN", "NONE", "-", "NULL"])])
                
                perlu_periksa_count = len(df_g_metric[df_g_metric['total_volume'] > limit_kuota])
                normal_count = len(df_g_metric) - perlu_periksa_count
            else:
                plat_lewat_kuota = 0
                tanpa_nopol = 0
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

            # Baris 1: Metrik Peringatan / Anomali
            m1, m2, m3 = st.columns(3)
            with m1:
                render_custom_metric("Plat melewati kuota harian", plat_lewat_kuota, "⛽", alert_if_gt_zero=True)
            with m2:
                render_custom_metric("Transaksi subsidi tanpa nopol", tanpa_nopol, "🚫", alert_if_gt_zero=True)
            with m3:
                render_custom_metric("Angka plat tak cocok konsumsi (lead)", 0, "🔍", alert_if_gt_zero=False)

            st.markdown("<br style='display: block; margin: 4px 0;'>", unsafe_allow_html=True)

            # Baris 2: Metrik Status Transaksi
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                render_custom_metric("Transaksi JBT", jbt_count, "📊", alert_if_gt_zero=False)
            with s2:
                render_custom_metric("Sangat mencurigakan", 0, "⚠️", alert_if_gt_zero=False)
            with s3:
                render_custom_metric("Perlu diperiksa", perlu_periksa_count, "🧐", alert_if_gt_zero=False)
            with s4:
                render_custom_metric("Normal", normal_count, "✅", alert_if_gt_zero=False)

            st.markdown("<br style='display: block; margin: 4px 0;'>", unsafe_allow_html=True)

            # Baris 3: Ringkasan Utama
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
                <div style="flex: 1.8;">PERKIRAAN JENIS (DARI PLAT)</div>
                <div style="flex: 0.6; text-align: center;">ISI</div>
                <div style="flex: 3.5; padding: 0 15px;">TOTAL VS KUOTA HARIAN</div>
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
                
                max_kuota = limit_kuota

                for index, row in df_grouped.iterrows():
                    plat = str(row[col_nopol_opt])
                    freq = int(row['total_transaksi'])
                    vol = row['total_volume']
                    
                    plat_upper = plat.upper()
                    if any(char.isdigit() for char in plat_upper) and len(plat_upper) > 6:
                        jenis_kendaraan = "Bus" if vol > 160 else ("Mobil barang" if vol > 60 else "Mobil penumpang")
                    else:
                        jenis_kendaraan = "Mobil barang"

                    persen = int((vol / max_kuota) * 100) if max_kuota > 0 else 100
                    green_width = min(100, persen)

                    status_badge = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>" if vol > max_kuota else "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"

                    card_html = f"""
                    <div style="background-color: white; border: 1px solid #e2e8f0; padding: 12px 16px; margin-bottom: 8px; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="flex: 1.2; display: flex; align-items: center;">
                            <strong style="font-size: 1.05rem; color: #1e293b; font-family: monospace;">{plat}</strong>
                        </div>
                        <div style="flex: 1.8; display: flex; align-items: center; gap: 8px;">
                            <span style="color: #64748b; font-size: 0.85rem;">≈ {jenis_kendaraan}</span>
                            <span style="background-color: #f8fafc; color: #64748b; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; border: 1px solid #e2e8f0; font-weight: 500;">ESTIMASI PLAT</span>
                        </div>
                        <div style="flex: 0.6; text-align: center;">
                            <span style="color: #334155; font-size: 0.85rem; font-weight: 600;">{freq}×</span>
                        </div>
                        <div style="flex: 3.5; padding: 0 15px;">
                            <div style="background-color: #e2e8f0; border-radius: 4px; height: 6px; width: 100%; display: flex; overflow: hidden; margin-bottom: 4px;">
                                <div style="background-color: #10b981; width: {green_width}%; height: 100%;"></div>
                            </div>
                            <div style="font-size: 0.75rem; color: #64748b; display: flex; justify-content: space-between;">
                                <span>{vol:,.0f} L / {max_kuota:,.0f} L (batas acuan)</span>
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
            st.subheader("Pengaturan Batas Kuota Referensi Produk Subsidi")
            st.markdown("Tentukan batas wajar harian untuk masing-masing kategori produk subsidi:")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.session_state.batas_jbt = st.number_input(
                    "JBT", 
                    value=float(st.session_state.batas_jbt),
                    step=5.0
                )
            with col2:
                st.session_state.batas_jbkp_r4 = st.number_input(
                    "JBKP R4", 
                    value=float(st.session_state.batas_jbkp_r4),
                    step=5.0
                )
            with col3:
                st.session_state.batas_jbkp_2 = st.number_input(
                    "JBKP 2", 
                    value=float(st.session_state.batas_jbkp_2),
                    step=5.0
                )

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
else:
    st.info("👈 Silakan unggah file transaksi Excel (.xlsx) atau CSV melalui panel di sebelah kiri.")
