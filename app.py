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

        # Fungsi pencarian kolom otomatis yang lebih aman dari kata 'payment'
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
        default_payment = find_best_column(["payment", "metode", "bayar", "cash", "tunai"])

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Pemetaan Kolom Data")
        st.sidebar.caption("Pastikan kolom terpilih dengan benar:")

        col_nopol_opt = st.sidebar.selectbox("Kolom Plat Nomor / Nopol", columns_list, index=columns_list.index(default_nopol) if default_nopol in columns_list else 0)
        col_vol_opt = st.sidebar.selectbox("Kolom Volume (L)", columns_list, index=columns_list.index(default_vol) if default_vol in columns_list else 0)
        col_produk_opt = st.sidebar.selectbox("Kolom Produk / Jenis BBM", columns_list, index=columns_list.index(default_produk) if default_produk in columns_list else 0)
        col_status_opt = st.sidebar.selectbox("Kolom Status / Keterangan", columns_list, index=columns_list.index(default_status) if default_status in columns_list else 0)
        col_payment_opt = st.sidebar.selectbox("Kolom Pembayaran / Metode (Opsional)", ["(Tidak Ada)"] + columns_list, index=columns_list.index(default_payment) + 1 if default_payment in columns_list else 0)

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
        tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])

        with tab1:
            st.subheader("Rekap Harian Penyaluran BBM Subsidi (Data File Upload)")
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric(label="Total Volume Terjual", value=f"{total_vol:,.1f} L")
            with c2:
                st.metric(label="Total Transaksi", value=f"{total_transaksi:,} Baris")
            with c3:
                st.metric(label="Produk Aktif Filter", value=st.session_state.filter_produk)
            with c4:
                st.metric(label="SPBU ID", value="4150201")

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

            # Header Tabel
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
                if col_payment_opt != "(Tidak Ada)" and col_payment_opt in df_display.columns:
                    agg_dict['payment_method'] = (col_payment_opt, 'first')

                df_grouped = df_display.groupby(col_nopol_opt).agg(**agg_dict).reset_index()
                df_grouped = df_grouped.sort_values(by="total_volume", ascending=False).reset_index(drop=True)
                max_kuota = 200.0

                for index, row in df_grouped.iterrows():
                    plat = str(row[col_nopol_opt])
                    freq = int(row['total_transaksi'])
                    vol = row['total_volume']
                    pay_text = f"<span style='background-color: #f1f5f9; color: #334155; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; margin-right: 6px; border: 1px solid #cbd5e1;'>{row['payment_method']}</span>" if 'payment_method' in row and pd.notna(row['payment_method']) else ""
                    
                    plat_upper = plat.upper()
                    if any(char.isdigit() for char in plat_upper) and len(plat_upper) > 6:
                        jenis_kendaraan = "Bus" if vol > 160 else ("Mobil barang" if vol > 60 else "Mobil penumpang")
                    else:
                        jenis_kendaraan = "Mobil barang"

                    persen = int((vol / max_kuota) * 100) if max_kuota > 0 else 100
                    green_width = min(100, persen)

                    status_badge = "<span style='background-color: #fef3c7; color: #92400e; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Perlu Diperiksa</span>" if vol > 50 else "<span style='background-color: #def7ec; color: #03543f; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;'>● Normal</span>"

                    card_html = f"""
                    <div style="background-color: white; border: 1px solid #e2e8f0; padding: 12px 16px; margin-bottom: 8px; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="flex: 1.2; display: flex; align-items: center; flex-wrap: wrap;">
                            {pay_text}
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
                                <span>{vol:,.0f} L / {max_kuota:,.0f} L (batas terlonggar)</span>
                                <span style="font-weight: 600;">{persen}%</span>
                            </div>
                        </div>
                        <div style="flex: 1.5; text-align: right;">
                            {status_badge}
                        </div>
                    </div>
                    """
                    # PENTING: Gunakan unsafe_allow_html=True agar tidak tercetak sebagai teks HTML mentah
                    st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.warning("Kolom Plat Nomor tidak ditemukan pada file Anda.")

        with tab2:
            st.subheader("Tabel Mentah Data Upload")
            st.dataframe(df_raw, use_container_width=True)

        with tab3:
            st.subheader("Pengaturan Batas Kuota Referensi")
            st.number_input("Batas Wajar Referensi Harian (L)", value=60)

    except Exception as e:
        st.error(f"Gagal memproses file: {e}")
else:
    st.info("👈 Silakan unggah file transaksi Excel (.xlsx) atau CSV melalui panel di sebelah kiri.")
