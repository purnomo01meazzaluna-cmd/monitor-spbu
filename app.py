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

# Inisialisasi batas wajar untuk JBT, JBKP, dan R2
if "batas_JBT" not in st.session_state:
    st.session_state.batas_JBT = 60.0
if "batas_JBKP" not in st.session_state:
    st.session_state.batas_JBKP = 60.0
if "batas_R2" not in st.session_state:
    st.session_state.batas_R2 = 15.0

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
        default_id = find_best_column(["id", "transaction", "trx", "kode"], ["nopol", "plat"])
        default_waktu = find_best_column(["waktu", "time", "tanggal", "date", "jam"], [])

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Pemetaan Kolom Data")

        col_nopol_opt = st.sidebar.selectbox("Kolom Plat Nomor / Nopol", columns_list, index=columns_list.index(default_nopol) if default_nopol in columns_list else 0)
        col_vol_opt = st.sidebar.selectbox("Kolom Volume (L)", columns_list, index=columns_list.index(default_vol) if default_vol in columns_list else 0)
        col_produk_opt = st.sidebar.selectbox("Kolom Produk / Jenis BBM", columns_list, index=columns_list.index(default_produk) if default_produk in columns_list else 0)
        col_status_opt = st.sidebar.selectbox("Kolom Status / Keterangan", columns_list, index=columns_list.index(default_status) if default_status in columns_list else 0)
        col_id_opt = st.sidebar.selectbox("Kolom ID Transaksi", columns_list, index=columns_list.index(default_id) if default_id in columns_list else 0)
        col_waktu_opt = st.sidebar.selectbox("Kolom Waktu / Tanggal", columns_list, index=columns_list.index(default_waktu) if default_waktu in columns_list else 0)

        # Bersihkan kata "Cash" pada data mentah untuk kolom nopol
        if col_nopol_opt in df_raw.columns:
            df_raw = df_raw.copy()
            df_raw[col_nopol_opt] = (
                df_raw[col_nopol_opt]
                .astype(str)
                .str.replace(r'(?i)\bcash\b', '', regex=True)
                .str.strip()
            )

        # Pisahkan data JBT, JBKP, dan R2 berdasarkan nama produk di file
        if col_produk_opt in df_raw.columns:
            produk_series = df_raw[col_produk_opt].astype(str)
            df_jbt = df_raw[produk_series.str.contains("SOLAR|BIOSOLAR|JBT|MHD|DEALITE", case=False, na=False)]
            df_jbkp = df_raw[produk_series.str.contains("PERTALITE|JBKP|RON90", case=False, na=False)]
            df_r2 = df_raw[produk_series.str.contains("R2|MOTOR|PERTAMAX", case=False, na=False)]
        else:
            df_jbt = df_raw.iloc[:0]
            df_jbkp = df_raw.iloc[:0]
            df_r2 = df_raw.iloc[:0]

        jbt_count = len(df_jbt)
        jbkp_count = len(df_jbkp)
        r2_count = len(df_r2)
        total_all_count = len(df_raw)

        # Tentukan dataframe aktif dan batas kuota berdasarkan filter produk
        if st.session_state.filter_produk == "JBT":
            df_display = df_jbt
            active_limit = st.session_state.batas_JBT
        elif st.session_state.filter_produk == "JBKP":
            df_display = df_jbkp
            active_limit = st.session_state.batas_JBKP
        elif st.session_state.filter_produk == "R2":
            df_display = df_r2
            active_limit = st.session_state.batas_R2
        else:
            df_display = df_raw
            active_limit = st.session_state.batas_JBT

        total_transaksi = len(df_display)
        total_vol = pd.to_numeric(df_display[col_vol_opt], errors='coerce').fillna(0).sum() if col_vol_opt in df_display.columns else 0.0

        # Main Layout Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Ringkasan Transaksi", 
            "🔍 Detail Kendaraan", 
            "⚙️ Pengaturan & Kuota", 
            "📸 Evidence Monitoring"
        ])

        with tab1:
            st.subheader("Rekap Harian Penyaluran BBM Subsidi (Data File Upload)")
            
            # --- PERHITUNGAN METRIK ---
            if not df_display.empty and col_nopol_opt in df_display.columns:
                agg_dict_m = {
                    'total_volume': (col_vol_opt, lambda x: pd.to_numeric(x, errors='coerce').sum())
                }
                df_g_metric = df_display.groupby(col_nopol_opt).agg(**agg_dict_m).reset_index()
                
                plat_lewat_kuota = len(df_g_metric[df_g_metric['total_volume'] > active_limit])
                
                nopol_series = df_display[col_nopol_opt].astype(str).str.strip().str.upper()
                tanpa_nopol = len(df_display[nopol_series.isin(["", "NAN", "NONE", "-", "NULL"])])
                
                perlu_periksa_count = len(df_g_metric[df_g_metric['total_volume'] > active_limit])
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
            f_col1, f_col2, f_col3, f_col4, _ = st.columns([1.2, 1.2, 1.2, 1.2, 1.5])
            with f_col1:
                if st.button(f"⛽ JBT ({jbt_count:,})", use_container_width=True):
                    st.session_state.filter_produk = "JBT"
                    st.rerun()
            with f_col2:
                if st.button(f"⛽ JBKP ({jbkp_count:,})", use_container_width=True):
                    st.session_state.filter_produk = "JBKP"
                    st.rerun()
            with f_col3:
                if st.button(f"🏍️ R2 ({r2_count:,})", use_container_width=True):
                    st.session_state.filter_produk = "R2"
                    st.rerun()
            with f_col4:
                if st.button(f"📦 All ({total_all_count:,})", use_container_width=True):
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
                
                for index, row in df_grouped.iterrows():
                    plat = str(row[col_nopol_opt])
                    freq = int(row['total_transaksi'])
                    vol = row['total_volume']
                    
                    plat_upper = plat.upper()
                    if any(char.isdigit() for char in plat_upper) and len(plat_upper) > 6:
                        jenis_kendaraan = "Bus" if vol > 160 else ("Mobil barang" if vol > 60 else "Mobil penumpang")
                    else:
                        jenis_kendaraan = "Mobil barang"

                    row_limit = active_limit
                    if st.session_state.filter_produk == "SEMUA" and col_produk_opt in df_display.columns:
                        sub_df = df_display[df_display[col_nopol_opt].astype(str) == plat]
                        if not sub_df.empty:
                            sample_prod = str(sub_df.iloc[0][col_produk_opt]).upper()
                            if "SOLAR" in sample_prod or "JBT" in sample_prod:
                                row_limit = st.session_state.batas_JBT
                            elif "PERTALITE" in sample_prod or "JBKP" in sample_prod:
                                row_limit = st.session_state.batas_JBKP
                            elif "R2" in sample_prod or "MOTOR" in sample_prod:
                                row_limit = st.session_state.batas_R2

                    persen = int((vol / row_limit) * 100) if row_limit > 0 else 100
                    green_width = min(100, persen)

                    status_badge = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>" if vol > row_limit else "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"

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
                                <span>{vol:,.0f} L / {row_limit:,.0f} L (batas acuan)</span>
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
            st.subheader("Pengaturan Batas Kuota Referensi Produk")
            st.markdown("Tentukan batas wajar harian untuk masing-masing kategori produk dalam satu kolom:")
            
            col_input, _ = st.columns([1, 2])
            with col_input:
                st.session_state.batas_JBT = st.number_input(
                    "Batas JBT (L)", 
                    value=float(st.session_state.batas_JBT),
                    step=5.0
                )
                st.session_state.batas_JBKP = st.number_input(
                    "Batas JBKP (L)", 
                    value=float(st.session_state.batas_JBKP),
                    step=5.0
                )
                st.session_state.batas_R2 = st.number_input(
                    "Batas R2 (L)", 
                    value=float(st.session_state.batas_R2),
                    step=1.0
                )

        with tab4:
            st.subheader("📸 Evidence & Log Monitoring Transaksi")
            st.markdown("Tabel hasil analisis transaksi, dokumentasi bukti CCTV, serta alasan temuan anomali kuota harian.")
            
            # Header Tabel Analisis Evidence ala Dashboard SPBU
            ev_header_html = """
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; margin-bottom: 8px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; color: #64748b; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;">
                <div style="flex: 1.2;">BUKTI CCTV</div>
                <div style="flex: 1.0;">ID</div>
                <div style="flex: 1.4;">WAKTU</div>
                <div style="flex: 1.5;">PRODUCT / NOZZLE</div>
                <div style="flex: 1.2;">PLAT</div>
                <div style="flex: 1.0;">VOLUME</div>
                <div style="flex: 1.5;">PERKIRAAN JENIS</div>
                <div style="flex: 1.3;">STATUS</div>
                <div style="flex: 2.2;">ALASAN TEMUAN</div>
            </div>
            """
            st.markdown(ev_header_html, unsafe_allow_html=True)

            if not df_display.empty and col_nopol_opt in df_display.columns:
                # Kalkulasi total volume per plat untuk mendeteksi anomali lebih kuota
                agg_vol = df_display.groupby(col_nopol_opt)[col_vol_opt].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).to_dict()

                for index, row in df_display.iterrows():
                    trx_id = str(row[col_id_opt]) if col_id_opt in df_display.columns else f"230{index}5"
                    waktu = str(row[col_waktu_opt]) if col_waktu_opt in df_display.columns else f"{selected_date}, 08:30:00"
                    prod = str(row[col_produk_opt]) if col_produk_opt in df_display.columns else "BIOSOLAR"
                    plat = str(row[col_nopol_opt])
                    vol_val = pd.to_numeric(row[col_vol_opt], errors='coerce') if col_vol_opt in df_display.columns else 0.0
                    
                    total_plat_vol = agg_vol.get(plat, vol_val)
                    
                    # Tentukan batas acuan baris ini
                    row_limit = active_limit
                    plat_upper = plat.upper()
                    if any(char.isdigit() for char in plat_upper) and len(plat_upper) > 6:
                        jenis_kendaraan = "Bus" if vol_val > 100 else ("Mobil barang" if vol_val > 40 else "Mobil penumpang")
                    else:
                        jenis_kendaraan = "Mobil barang"

                    is_anomaly = total_plat_vol > row_limit
                    status_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Perlu Diperiksa</span>" if is_anomaly else "<span style='background-color: #def7ec; color: #03543f; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Normal</span>"
                    alasan = f"Total harian {total_plat_vol:.1f}L > jatah wajar ({row_limit:.0f}L) — konfirmasi jenis" if is_anomaly else "Dalam batas wajar kuota harian"

                    row_card_html = f"""
                    <div style="background-color: white; border: 1px solid #e2e8f0; padding: 10px 16px; margin-bottom: 8px; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02); font-size: 0.85rem;">
                        <div style="flex: 1.2; display: flex; flex-direction: column; gap: 4px;">
                            <button style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 6px; font-size: 0.7rem; cursor: pointer; text-align: left; color: #334155;">📷 Kamera</button>
                            <button style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 6px; font-size: 0.7rem; cursor: pointer; text-align: left; color: #334155;">📁 Galeri</button>
                        </div>
                        <div style="flex: 1.0; color: #475569; font-family: monospace;">{trx_id}</div>
                        <div style="flex: 1.4; color: #475569; font-size: 0.75rem;">{waktu}</div>
                        <div style="flex: 1.5; color: #1e293b; font-weight: 500; font-size: 0.75rem;">{prod}</div>
                        <div style="flex: 1.2; font-family: monospace; font-weight: 600; color: #0f172a;">{plat}</div>
                        <div style="flex: 1.0; color: #334155; font-weight: 600;">{vol_val:.2f}L</div>
                        <div style="flex: 1.5; color: #64748b; font-size: 0.75rem;">≈ {jenis_kendaraan}<br><span style="font-size: 0.65rem; background: #f1f5f9; padding: 1px 4px; border-radius: 3px;">ESTIMASI PLAT</span></div>
                        <div style="flex: 1.3;">{status_html}</div>
                        <div style="flex: 2.2; color: #64748b; font-size: 0.75rem; background: #f8fafc; padding: 6px; border-radius: 4px; border: 1px solid #f1f5f9;">{alasan}</div>
                    </div>
                    """
                    st.markdown(row_card_html, unsafe_allow_html=True)
            else:
                st.warning("Belum ada data transaksi untuk dimuat ke tabel evidence.")

            st.markdown("---")
            
            # Tombol unduh laporan evidence
            if not df_display.empty:
                csv_data = df_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Laporan & Log Monitoring (.csv)",
                    data=csv_data,
                    file_name=f"Laporan_Evidence_SPBU_4150201_{selected_date}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
else:
    st.info("👈 Silakan unggah file transaksi Excel (.xlsx) atau CSV melalui panel di sebelah kiri.")
