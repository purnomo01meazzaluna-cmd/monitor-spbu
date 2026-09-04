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
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 8px 12px !important;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    div[data-testid="stMetric"] label {
        font-size: 0.7rem !important;
        color: #64748b !important;
        margin-bottom: 0px !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        font-weight: 600;
        color: #1e293b;
        line-height: 1.2 !important;
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

# Inisialisasi session state untuk filter produk
if "filter_produk" not in st.session_state:
    st.session_state.filter_produk = "SEMUA"

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

        # Fungsi pencarian kolom otomatis
        def find_best_column(keywords):
            for col in columns_list:
                for kw in keywords:
                    if kw.lower() in col.lower():
                        return col
            return columns_list[0] if columns_list else None

        default_nopol = find_best_column(["plat", "nopol", "nomor", "vehicle", "police"])
        default_vol = find_best_column(["volume", "liter", "vol", "qty", "jumlah"])
        default_produk = find_best_column(["produk", "bbm", "jenis", "product", "fuel", "bahan bakar"])
        default_status = find_best_column(["status", "keterangan", "ket", "remark", "note"])

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Pemetaan Kolom Data")
        st.sidebar.caption("Sesuaikan pilihan di bawah jika belum pas dengan kolom file Anda:")

        col_nopol_opt = st.sidebar.selectbox("Kolom Plat Nomor / Nopol", columns_list, index=columns_list.index(default_nopol) if default_nopol in columns_list else 0)
        col_vol_opt = st.sidebar.selectbox("Kolom Volume (L)", columns_list, index=columns_list.index(default_vol) if default_vol in columns_list else 0)
        col_produk_opt = st.sidebar.selectbox("Kolom Produk / Jenis BBM", columns_list, index=columns_list.index(default_produk) if default_produk in columns_list else 0)
        col_status_opt = st.sidebar.selectbox("Kolom Status / Keterangan", columns_list, index=columns_list.index(default_status) if default_status in columns_list else 0)

        # Pisahkan data JBT dan JBKP berdasarkan isi kolom produk secara akurat
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

        # Tentukan data yang aktif ditampilkan berdasarkan state filter saat ini
        if st.session_state.filter_produk == "JBT":
            df_display = df_jbt
        elif st.session_state.filter_produk == "JBKP":
            df_display = df_jbkp
        else:
            df_display = df_raw  # Menampilkan SEMUA data upload

        # --- HITUNG METRIK BERDASARKAN DATA AKTIF ---
        total_transaksi = len(df_display)
        
        if col_vol_opt in df_display.columns:
            vol_numeric = pd.to_numeric(df_display[col_vol_opt], errors='coerce').fillna(0)
            total_vol = vol_numeric.sum()
        else:
            total_vol = 0.0

        normal_count = 0
        perlu_cek_count = 0
        mencurigakan_count = 0

        if col_status_opt in df_display.columns:
            status_series = df_display[col_status_opt].astype(str).str.lower()
            normal_count = len(df_display[status_series.str.contains("normal|valid|sesuai|sukses|success", na=False)])
            perlu_cek_count = len(df_display[status_series.str.contains("perlu|check|cek|lewat|kuota|warning|perhatian", na=False)])
            mencurigakan_count = len(df_display[status_series.str.contains("mencurigakan|suspect|tidak|tanpa|nopol|anomaly|abnormal", na=False)])

        # Main Layout Tabs
        tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])

        with tab1:
            st.subheader("Rekap Harian Penyaluran BBM Subsidi (Data File Upload)")
            
            # Baris 1 Metrik Utama
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric(label="Total Volume Terjual", value=f"{total_vol:,.1f} L")
            with c2:
                st.metric(label="Total Transaksi", value=f"{total_transaksi:,} Baris")
            with c3:
                st.metric(label="Produk Aktif Filter", value=st.session_state.filter_produk)
            with c4:
                st.metric(label="SPBU ID", value="4150201")

            st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

            # Baris 2 Kategori Status dari File
            r3_1, r3_2, r3_3, r3_4 = st.columns(4)
            with r3_1:
                st.metric(label="Total Baris Data", value=f"{total_transaksi:,}")
            with r3_2:
                st.metric(label="Status: Mencurigakan", value=f"{mencurigakan_count:,}")
            with r3_3:
                st.metric(label="Status: Perlu Diperiksa", value=f"{perlu_cek_count:,}")
            with r3_4:
                st.metric(label="Status: Normal", value=f"{normal_count:,}")

            st.markdown("<br>", unsafe_allow_html=True)

            # Tombol Filter Interaktif dengan "All Product"
            st.markdown("#### Kategori Produk Subsidi")
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

            if st.session_state.filter_produk == "SEMUA":
                st.info(f"Menampilkan seluruh data transaksi (JBT & JBKP). Total baris: {len(df_display):,}")
            else:
                st.info(f"Menampilkan data tersaring: **{st.session_state.filter_produk}** (Jumlah Baris: {len(df_display):,})")

            st.markdown("---")
            st.markdown("### Daftar Agregasi Plat Nomor Berdasarkan File Upload")

            # --- TAMPILAN KARTU BERDASARKAN DATA RIIL ---
            if not df_display.empty and col_nopol_opt in df_display.columns:
                df_grouped = df_display.groupby(col_nopol_opt).agg(
                    total_transaksi=(col_vol_opt, 'count'),
                    total_volume=(col_vol_opt, lambda x: pd.to_numeric(x, errors='coerce').sum())
                ).reset_index()

                df_grouped = df_grouped.sort_values(by="total_volume", ascending=False).reset_index(drop=True)

                for index, row in df_grouped.iterrows():
                    plat = row[col_nopol_opt]
                    freq = row['total_transaksi']
                    vol = row['total_volume']
                    
                    if vol > 120:
                        status_badge = "<span style='background-color: #fde8e8; color: #9b1c1c; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Tinggi / Perlu Cek</span>"
                        border_color = "#e02424"
                    else:
                        status_badge = "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"
                        border_color = "#0e9f6e"

                    card_html = f"""
                    <div style="background-color: white; border-left: 5px solid {border_color}; border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; padding: 12px 16px; margin-bottom: 10px; border-radius: 6px; display: flex; align-items: center; justify-content: space-between;">
                        <div style="flex: 1.5;">
                            <strong style="font-size: 1.05rem; color: #1e293b;">{plat}</strong>
                        </div>
                        <div style="flex: 1; text-align: center;">
                            <span style="background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.85rem;">{freq} Transaksi</span>
                        </div>
                        <div style="flex: 3; padding: 0 15px;">
                            <div style="font-size: 0.85rem; color: #334155; display: flex; justify-content: space-between;">
                                <span>Total Volume: <b>{vol:,.1f} Liter</b></span>
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
            st.subheader("Tabel Mentah Data Upload (Pencarian Nopol)")
            search_query = st.text_input("Cari kata kunci pada data:", "")
            
            if search_query:
                mask = df_raw.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                st.dataframe(df_raw[mask], use_container_width=True)
            else:
                st.dataframe(df_raw, use_container_width=True)

        with tab3:
            st.subheader("Pengaturan Batas Kuota Referensi")
            col1, col2 = st.columns(2)
            with col1:
                st.number_input("Batas Wajar Referensi Harian (L)", value=60)
            with col2:
                st.text_input("Jenis BBM Terdeteksi di File", value=", ".join(df_raw[col_produk_opt].dropna().unique().astype(str)[:5]) if col_produk_opt in df_raw.columns else "-")

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
else:
    st.info("👈 Silakan unggah file transaksi Excel (.xlsx) atau CSV melalui panel di sebelah kiri.")
    
    tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])
    with tab1:
        st.warning("Menunggu unggahan file data transaksi...")
