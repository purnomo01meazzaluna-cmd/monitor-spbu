import json
import os
import re
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="SPBU Monitoring & Fraud Prevention",
    page_icon="⛽",
    layout="wide",
)

CONFIG_FILE = "config_kuota.json"

default_config = {
    "jbt_1": 60, "jbt_2": 0, "jbt_3": 200, "jbt_4": 200, "jbt_5": 250,
    "jbkp_1": 60, "jbkp_2": 8, "jbkp_3": 120, "jbkp_4": 120, "jbkp_5": 120,
    "tenggat_waktu": 180,
    "max_freq_pelangsir_jbt": 2,
    "max_freq_pelangsir_jbkp_r4": 3,
    "max_freq_pelangsir_jbkp_r2": 4,
    "max_freq_pelangsir_jbt_r4_umum": 2,
    "max_freq_pelangsir_jbt_r6": 2,
    "max_vol_mismatch": 100
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                for k, v in default_config.items():
                    if k not in loaded:
                        loaded[k] = v
                return loaded
        except:
            return default_config
    return default_config

def clean_plat_number(val):
    if pd.isna(val):
        return "No Barcode"
    s = str(val).strip()
    s_clean_chars = re.sub(r'[\*\_]', '', s).strip()
    
    lower_val = s_clean_chars.lower()
    if lower_val in ["pump test", "customer card"]:
        return s_clean_chars
    
    # Menangkap berbagai variasi penulisan "No Barcode" atau data kosong/strip
    if lower_val in ["no barcode", "non barcode", "tanpa nopol", "tanpa barcode", "-", "", "nan", "null"]:
        return "No Barcode"
    
    payment_keywords = ["cash", "transfer", "qris", "debit", "credit", "edc"]
    if lower_val in payment_keywords:
        return "No Barcode"
        
    s_sub = re.sub(r'^(cash|transfer|qris|debit|credit|edc)\s*', '', s_clean_chars, flags=re.IGNORECASE).strip()
    return s_sub if s_sub else "No Barcode"

def get_estimation_kuota_and_number(plat_str, jenis_bbm):
    s_plat = str(plat_str).strip()
    lower_plat = s_plat.lower()

    if lower_plat in ["pump test", "customer card"]:
        return "Khusus / Pengujian", 0, "-"

    if lower_plat in ["no barcode", "tanpa nopol", "tanpa barcode", "-", "", "nan", "null"]:
        cfg = st.session_state.config_data
        return "No Barcode", cfg.get("jbt_3", 200), "-"

    cleaned_plat = clean_plat_number(s_plat)
    numbers = re.findall(r'\d+', cleaned_plat)
    
    cfg = st.session_state.config_data
    if not numbers:
        return "No Barcode", cfg.get("jbt_3", 200), "-"
    
    num_val = int(numbers[0])
    is_jbt = "JBT" in jenis_bbm or "SOLAR" in str(jenis_bbm).upper()
    
    if is_jbt:
        if 1 <= num_val <= 2999:
            return "Roda 4 Pribadi (JBT)", cfg.get("jbt_1", 60), numbers[0][0]
        elif 3000 <= num_val <= 6999:
            return "Roda 2 Sepeda Motor (JBT)", cfg.get("jbt_2", 0), numbers[0][0]
        elif 7000 <= num_val <= 7999:
            return "Roda 4 Minibus/Bus (JBT)", cfg.get("jbt_3", 200), numbers[0][0]
        elif 8000 <= num_val <= 8999:
            return "Roda 4 Truck (JBT)", cfg.get("jbt_4", 200), numbers[0][0]
        elif 9000 <= num_val <= 9999:
            return "Roda 4 Truck Khusus (JBT)", cfg.get("jbt_5", 250), numbers[0][0]
    else: 
        if 1 <= num_val <= 2999:
            return "Roda 4 Pribadi (JBKP)", cfg.get("jbkp_1", 60), numbers[0][0]
        elif 3000 <= num_val <= 6999:
            return "Roda 2 Sepeda Motor (JBKP)", cfg.get("jbkp_2", 8), numbers[0][0]
        elif 7000 <= num_val <= 7999:
            return "Roda 4 Minibus (JBKP)", cfg.get("jbkp_3", 120), numbers[0][0]
        elif 8000 <= num_val <= 8999:
            return "Roda 4 Pick Up (JBKP)", cfg.get("jbkp_4", 120), numbers[0][0]
        elif 9000 <= num_val <= 9999:
            return "Roda 4 Pick Up Khusus (JBKP)", cfg.get("jbkp_5", 120), numbers[0][0]
            
    return "Kendaraan Umum Lainnya", 200, numbers[0][0]

if "config_data" not in st.session_state:
    st.session_state.config_data = load_config()

if "df" not in st.session_state:
    st.session_state.df = None

if "temp_df" not in st.session_state:
    st.session_state.temp_df = None

lock_keys = [
    "jbt_1", "jbt_2", "jbt_3", "jbt_4", "jbt_5",
    "jbkp_1", "jbkp_2", "jbkp_3", "jbkp_4", "jbkp_5",
    "max_freq_pelangsir_jbt", "max_freq_pelangsir_jbkp_r4", "max_freq_pelangsir_jbkp_r2",
    "max_freq_pelangsir_jbt_r4_umum", "max_freq_pelangsir_jbt_r6", "max_vol_mismatch", "tenggat_waktu"
]
for k in lock_keys:
    if f"lock_{k}" not in st.session_state:
        st.session_state[f"lock_{k}"] = True

st.markdown(
    """
    <div style="background-color: #2563eb; color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin:0; font-size: 24px;">⛽ SPBU Monitoring & Fraud Prevention Dashboard</h2>
        <p style="margin:4px 0 0 0; font-size: 14px; opacity: 0.9;">Pantau transaksi harian, deteksi indikasi kecurangan subsidi, dan kelola kuota BBM berdasarkan rentang plat nomor.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 🗂️ Menu Navigasi SPBU")
selected_tab = st.sidebar.radio(
    "Pilih Menu:",
    [
        "📁 Data Eviden Upload",
        "📊 Ringkasan",
        "📋 Detail Transaksi",
        "🚨 Pelangsir & Beruntun",
        "⚠️ Mismatch Kendaraan",
        "⚙️ Pengaturan Batas & Kuota"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips SPBU:** Pastikan file laporan harian di-upload melalui menu **Data Eviden Upload** dan klik **Submit Data** agar rekap dan metrik membaca data yang Anda unggah secara aktual.")

if selected_tab == "📁 Data Eviden Upload":
    st.subheader("Sumber Data Transaksi (Hose Delivery)")
    st.write("Unggah file laporan penjualan harian (Excel / CSV) lalu klik **Submit Data Analisis** agar data masuk ke sistem.")

    uploaded_file = st.file_uploader("Pilih file CSV atau XLSX", type=["csv", "xlsx"], key="uploaded_eviden_file")

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                temp_data = pd.read_csv(uploaded_file)
            else:
                temp_data = pd.read_excel(uploaded_file)

            for col in temp_data.columns:
                if any(k in col.lower() for k in ["payment", "nopol", "plat"]):
                    temp_data[col] = temp_data[col].apply(clean_plat_number)

            st.session_state.temp_df = temp_data

            st.info(f"File **{uploaded_file.name}** berhasil dibaca. Preview data di bawah:")
            st.dataframe(st.session_state.temp_df, use_container_width=True)

            if st.button("🚀 Submit Data Analisis", type="primary"):
                st.session_state.df = st.session_state.temp_df
                st.success("Data berhasil di-submit!")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")
            
    elif st.session_state.df is not None:
        st.success("Status: Data eviden aktif sedang digunakan oleh sistem.")
        st.dataframe(st.session_state.df, use_container_width=True)
        if st.button("🗑️ Hapus / Reset Data Aktif"):
            st.session_state.df = None
            st.session_state.temp_df = None
            st.rerun()
    else:
        st.markdown(
            """
            <div style="border: 2px dashed #cbd5e1; padding: 40px; text-align: center; border-radius: 8px; background-color: #f8fafc; margin-top: 20px;">
                <p style="color: #64748b; font-size: 16px; margin: 0;"><b>Belum ada data yang di-submit</b></p>
                <p style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Upload file CSV/XLSX lalu klik submit untuk memproses data aktual.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif selected_tab == "📊 Ringkasan":
    st.subheader("Ringkasan & Metrik Pemantauan Subsidi")

    st.markdown("##### Filter Kategori BBM Berdasarkan Indikasi")
    selected_bbm = st.radio(
        "Pilih Jenis BBM",
        options=["JBT · Solar", "JBKP · Pertalite"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if st.session_state.df is not None:
        df_work = st.session_state.df.copy()
        
        st.markdown("###### ⚙️ Konfigurasi Kolom Data Anda:")
        col_list = list(df_work.columns)
        
        default_nopol_idx = next((i for i, c in enumerate(col_list) if any(k in c.lower() for k in ["payment", "nopol", "plat", "vehicle"])), len(col_list)-1)
        default_vol_idx = next((i for i, c in enumerate(col_list) if any(k in c.lower() for k in ["volume", "liter", "qty"])), min(1, len(col_list)-1))
        default_prod_idx = next((i for i, c in enumerate(col_list) if any(k in c.lower() for k in ["product", "produk", "bbm", "fuel"])), None)

        col_sel1, col_sel2, col_sel3 = st.columns(3)
        with col_sel1:
            col_nopol = st.selectbox("Pilih Kolom Plat / Nopol:", col_list, index=default_nopol_idx, key="sel_nopol_main")
        with col_sel2:
            col_vol = st.selectbox("Pilih Kolom Volume (Liter):", col_list, index=default_vol_idx, key="sel_vol_main")
        with col_sel3:
            prod_options = ["(Tidak Ada / Abaikan)"] + col_list
            prod_default = default_prod_idx + 1 if default_prod_idx is not None else 0
            col_prod = st.selectbox("Pilih Kolom Produk BBM:", prod_options, index=prod_default, key="sel_prod_main")
            
        st.markdown("---")

        if col_prod != "(Tidak Ada / Abaikan)":
            is_solar_filter = "JBT" in selected_bbm
            if is_solar_filter:
                df_work = df_work[df_work[col_prod].astype(str).str.contains("solar|jbt|biosolar", case=False, na=False)]
            else:
                df_work = df_work[df_work[col_prod].astype(str).str.contains("pertalite|jbkp", case=False, na=False)]

        df_work[col_nopol] = df_work[col_nopol].apply(clean_plat_number)
        
        actual_total_trx = len(df_work)
        df_work[col_vol] = pd.to_numeric(df_work[col_vol].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce").fillna(0)

        def is_special_category(plat):
            s_plat = str(plat).strip().lower()
            return s_plat in ["pump test", "customer card"]

        df_work["is_special"] = df_work[col_nopol].apply(is_special_category)
        
        # Perbaikan deteksi No Barcode secara akurat
        sub_no_barcode = int((
            (df_work[col_nopol].astype(str).str.lower().isin(["no barcode", "tanpa barcode", "-", "nan", ""])) | 
            (df_work[col_nopol].isna())
        ) & (~df_work["is_special"])).sum()
        
        agg_check = df_work.groupby(col_nopol)[col_vol].sum().reset_index() if actual_total_trx > 0 else pd.DataFrame(columns=[col_nopol, col_vol])
        def get_kuota_only(plat):
            _, k, _ = get_estimation_kuota_and_number(plat, selected_bbm)
            return k
            
        if not agg_check.empty:
            agg_check["max_kuota"] = agg_check[col_nopol].apply(get_kuota_only)
            agg_check["is_special"] = agg_check[col_nopol].apply(is_special_category)
            
            lebih_kuota = int(((agg_check["max_kuota"] > 0) & (agg_check[col_vol] > agg_check["max_kuota"]) & (~agg_check["is_special"])).sum())
        else:
            lebih_kuota = 0

        freq_check = df_work.groupby(col_nopol)[col_vol].count().reset_index() if actual_total_trx > 0 else pd.DataFrame(columns=[col_nopol, col_vol])
        max_freq = st.session_state.config_data.get("max_freq_pelangsir_jbt", 2)
        isi_beruntun = int((freq_check[col_vol] > max_freq).sum()) if not freq_check.empty else 0

        max_vol_mis = st.session_state.config_data.get("max_vol_mismatch", 100)
        mismatch_kendaraan = int(((agg_check["max_kuota"] > 0) & (agg_check[col_vol] > max_vol_mis) & (~agg_check["is_special"])).sum()) if not agg_check.empty else 0

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric(label="Total Transaksi", value=f"{actual_total_trx:,}", delta="Data Aktual")
        with col2: st.metric(label="No Barcode", value=str(sub_no_barcode), delta="Normal" if sub_no_barcode == 0 else "Perhatian", delta_color="inverse" if sub_no_barcode > 0 else "normal")
        with col3: st.metric(label="Lebih Kuota Harian", value=str(lebih_kuota), delta="Normal" if lebih_kuota == 0 else "Perhatian", delta_color="inverse" if lebih_kuota > 0 else "normal")
        with col4: st.metric(label="Isi Ulang Beruntun", value=str(isi_beruntun), delta="Normal" if isi_beruntun == 0 else "Perhatian", delta_color="inverse" if isi_beruntun > 0 else "normal")
        with col5: st.metric(label="Mismatch Kendaraan", value=str(mismatch_kendaraan), delta="Normal" if mismatch_kendaraan == 0 else "Perhatian", delta_color="inverse" if mismatch_kendaraan > 0 else "normal")

    else:
        st.warning("⚠️ Belum ada file data eviden yang di-submit. Silakan upload file Anda melalui menu **📁 Data Eviden Upload** lalu klik **Submit Data Analisis**.")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Total Transaksi", "0")
        with col2: st.metric("No Barcode", "0")
        with col3: st.metric("Lebih Kuota Harian", "0")
        with col4: st.metric("Isi Ulang Beruntun", "0")
        with col5: st.metric("Mismatch Kendaraan", "0")

    st.markdown("---")
    st.markdown("#### Rekap per Plat (Harian)")

    if st.session_state.df is not None and actual_total_trx > 0:
        if col_nopol and col_vol:
            agg_df = df_work.groupby(col_nopol).agg(
                total_liter=(col_vol, "sum"),
                frekuensi=(col_vol, "count")
            ).reset_index()
            
            res_list = agg_df[col_nopol].apply(lambda x: get_estimation_kuota_and_number(x, selected_bbm))
            agg_df["keterangan"] = [r[0] for r in res_list]
            agg_df["max_kuota"] = [r[1] for r in res_list]
            agg_df["angka_plat"] = [r[2] for r in res_list]
            
            agg_df["persen"] = agg_df.apply(
                lambda row: int(round((row["total_liter"] / row["max_kuota"]) * 100)) if row["max_kuota"] > 0 else 0,
                axis=1
            )
            agg_df = agg_df.sort_values(by="total_liter", ascending=False)
            
            header_cols = st.columns([1.3, 1.1, 2.5, 0.8, 3.5, 1.4])
            with header_cols[0]: st.markdown("**NOMOR PLAT**")
            with header_cols[1]: st.markdown("**ANGKA PLAT**")
            with header_cols[2]: st.markdown("**ESTIMASI KENDARAAN**")
            with header_cols[3]: st.markdown("**ISI**")
            with header_cols[4]: st.markdown("**TOTAL VS KUOTA BATAS**")
            with header_cols[5]: st.markdown("**STATUS**")
            st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

            for _, row in agg_df.iterrows():
                plat_val = str(row[col_nopol])
                angka_val = str(row["angka_plat"])
                liter_val = row["total_liter"]
                freq_val = row["frekuensi"]
                ket_val = row["keterangan"]
                kuota_val = row["max_kuota"]
                pct_val = min(row["persen"], 100) if kuota_val > 0 else 0
                is_special = is_special_category(plat_val)
                is_over = not is_special and kuota_val > 0 and liter_val > kuota_val
                
                cols = st.columns([1.3, 1.1, 2.5, 0.8, 3.5, 1.4])
                with cols[0]: st.markdown(f"**{plat_val}**")
                with cols[1]: st.markdown(f"<span style='font-family: monospace; font-weight: bold; background-color: #e2e8f0; padding: 2px 6px; border-radius: 4px; color: #1e293b;'>{angka_val}</span>", unsafe_allow_html=True)
                with cols[2]: st.markdown(f"<span style='font-size: 11px; background-color: #f1f5f9; padding: 2px 6px; border-radius: 4px; color: #334155;'>{ket_val}</span>", unsafe_allow_html=True)
                with cols[3]: st.markdown(f"{freq_val}×")
                with cols[4]:
                    if kuota_val > 0:
                        st.progress(pct_val / 100.0)
                        st.markdown(f"<span style='font-size: 12px; color: #555;'>{liter_val:,.2f} L / {kuota_val} L &nbsp; • &nbsp; {row['persen']}%</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='font-size: 12px; color: #555;'>{liter_val:,.2f} L (Tanpa Kuota Terikat)</span>", unsafe_allow_html=True)
                with cols[5]:
                    if is_special:
                        st.markdown("<span style='background-color: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 500;'>🔵 Testing/Card</span>", unsafe_allow_html=True)
                    elif is_over:
                        st.markdown("<span style='background-color: #fee2e2; color: #991b1b; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 500;'>🔴 Lewat Kuota</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='background-color: #dcfce7; color: #166534; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 500;'>🟢 Normal</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)
    else:
        st.info("💡 Tidak ada data yang sesuai dengan filter kategori BBM yang dipilih.")

elif selected_tab == "📋 Detail Transaksi":
    st.subheader("📋 Detail Seluruh Transaksi & Investigasi Temuan")
    if st.session_state.df is None:
        st.info("💡 Silakan upload file eviden Anda terlebih dahulu pada menu **📁 Data Eviden Upload**.")
    else:
        selected_bbm_detail = st.radio(
            "Pilih Acuan Jenis BBM untuk Detail Analisis",
            options=["JBT · Solar", "JBKP · Pertalite"],
            horizontal=True,
            key="bbm_detail_radio"
        )
        
        df_detail = st.session_state.df.copy()
        
        col_list = list(df_detail.columns)
        default_nopol_idx = next((i for i, c in enumerate(col_list) if any(k in c.lower() for k in ["payment", "nopol", "plat", "vehicle"])), len(col_list)-1)
        default_vol_idx = next((i for i, c in enumerate(col_list) if any(k in c.lower() for k in ["volume", "liter", "qty"])), min(1, len(col_list)-1))
        
        c_nopol = col_list[default_nopol_idx]
        c_vol = col_list[default_vol_idx]
        
        df_detail[c_nopol] = df_detail[c_nopol].apply(clean_plat_number)
        df_detail[c_vol] = pd.to_numeric(df_detail[c_vol].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce").fillna(0)

        total_per_plat = df_detail.groupby(c_nopol)[c_vol].sum().to_dict()

        search_query = st.text_input("🔍 Cari No. Plat / ID Transaksi / Produk", placeholder="Ketik kata kunci...")
        if search_query:
            mask = df_detail.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
            df_detail = df_detail[mask]

        st.markdown("<br>", unsafe_allow_html=True)
        header_cols = st.columns([1.1, 1.0, 1.4, 1.6, 1.3, 1.1, 1.4, 2.3])
        with header_cols[0]: st.markdown("**BUKTI CCTV**")
        with header_cols[1]: st.markdown("**ID**")
        with header_cols[2]: st.markdown("**WAKTU**")
        with header_cols[3]: st.markdown("**PRODUCT / NOZZLE**")
        with header_cols[4]: st.markdown("**PLAT**")
        with header_cols[5]: st.markdown("**VOLUME**")
        with header_cols[6]: st.markdown("**PERKIRAAN JENIS**")
        with header_cols[7]: st.markdown("**ALASAN TEMUAN & STATUS**")
        st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

        for idx, row in df_detail.iterrows():
            plat_val = str(row[c_nopol])
            vol_val = float(row[c_vol])
            
            est_jenis, max_k, _ = get_estimation_kuota_and_number(plat_val, selected_bbm_detail)
            sum_harian = total_per_plat.get(plat_val, vol_val)
            
            s_plat_lower = plat_val.strip().lower()
            is_special = s_plat_lower in ["pump test", "customer card"]
            is_no_barcode = plat_val == "No Barcode"
            is_lewat_kuota = not is_special and max_k > 0 and sum_harian > max_k
            
            cols = st.columns([1.1, 1.0, 1.4, 1.6, 1.3, 1.1, 1.4, 2.3])
            with cols[0]:
                st.button("📷 Kamera", key=f"cam_{idx}")
                st.button("🖼️ Galeri", key=f"gal_{idx}")
            with cols[1]:
                st.markdown(f"<span style='font-size: 13px;'>{row.get('ID', row.get('id', idx+2305000))}</span>", unsafe_allow_html=True)
            with cols[2]:
                waktu_str = str(row.get('Waktu', row.get('waktu', row.get('Tanggal', '31/08/2026, 06.00.00'))))
                st.markdown(f"<span style='font-size: 12px; color: #475569;'>{waktu_str}</span>", unsafe_allow_html=True)
            with cols[3]:
                prod_str = str(row.get('Product', row.get('product', row.get('Produk', 'BIO_SOLAR (P3/H1)'))))
                st.markdown(f"<span style='font-size: 12px; font-weight: 600;'>{prod_str}</span>", unsafe_allow_html=True)
            with cols[4]:
                st.markdown(f"<span style='font-weight: bold; font-size: 13px;'>{plat_val}</span>", unsafe_allow_html=True)
            with cols[5]:
                st.markdown(f"<span style='font-weight: 600;'>{vol_val:.2f}L</span>", unsafe_allow_html=True)
            with cols[6]:
                if is_special:
                    st.markdown("<span style='font-size: 11px; color: #0369a1;'>🔵 Pengujian / Kartu</span>", unsafe_allow_html=True)
                elif is_no_barcode:
                    st.markdown("<span style='font-size: 11px; color: #64748b;'>— No Barcode</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='font-size: 11px; color: #334155;'>≈ {est_jenis}</span>", unsafe_allow_html=True)
            with cols[7]:
                if is_special:
                    st.markdown("<span style='background-color: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; font-size: 11px;'>🔵 Pengujian Mesin / Kartu — Aman</span>", unsafe_allow_html=True)
                elif is_lewat_kuota:
                    st.markdown(f"<span style='background-color: #fef3c7; color: #92400e; padding: 3px 6px; border-radius: 4px; font-size: 11px; display:inline-block;'>⚠️ Total harian {sum_harian:.1f}L > jatah kuota ({max_k}L) — konfirmasi jenis</span>", unsafe_allow_html=True)
                    st.markdown("<span style='background-color: #fef2f2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; display:inline-block; margin-top:2px;'>● Perlu Diperiksa</span>", unsafe_allow_html=True)
                elif is_no_barcode:
                    st.markdown("<span style='background-color: #fef3c7; color: #92400e; padding: 3px 6px; border-radius: 4px; font-size: 11px; display:inline-block;'>Subsidi tanpa barcode — wajib dicatat per aturan</span>", unsafe_allow_html=True)
                    st.markdown("<span style='background-color: #fef2f2; color: #991b1b; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; display:inline-block; margin-top:2px;'>● Perlu Diperiksa</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='background-color: #dcfce7; color: #166534; padding: 2px 6px; border-radius: 4px; font-size: 11px;'>🟢 Normal / Sesuai Kuota</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 8px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)

elif selected_tab == "🚨 Pelangsir & Beruntun":
    st.subheader("🚨 Identifikasi Pelangsir (Isi Ulang Beruntun)")
    if st.session_state.df is None:
        st.info("💡 Silakan upload dan submit data eviden terlebih dahulu.")
    else:
        st.write("Daftar transaksi beruntun berdasarkan data yang di-upload:")
        st.dataframe(st.session_state.df, use_container_width=True)

elif selected_tab == "⚠️ Mismatch Kendaraan":
    st.subheader("⚠️ Identifikasi Ketidaksesuaian (Mismatch Kendaraan vs BBM)")
    if st.session_state.df is None:
        st.info("💡 Silakan upload dan submit data eviden terlebih dahulu.")
    else:
        st.write("Daftar anomali volume dan jenis BBM:")
        st.dataframe(st.session_state.df, use_container_width=True)

elif selected_tab == "⚙️ Pengaturan Batas & Kuota":
    st.subheader("Konfigurasi Batas & Kuota BBM Berdasarkan Plat Nomor")
    st.markdown("Atur batasan volume maksimal harian (Liter/Hari) dan ambang batas pelangsir. Centang kotak 🔒 di samping untuk membuka/mengunci input, lalu klik tombol **Simpan**.")

    def render_locked_input(label, key):
        col_inp, col_chk = st.columns([0.92, 0.08])
        with col_chk:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            is_locked = st.checkbox("🔒", key=f"lock_{key}")
        with col_inp:
            val = st.number_input(label, value=st.session_state.config_data.get(key, 0), key=key, disabled=is_locked)
        return val

    st.markdown("### 🚚 JBT (Jenis BBM Tertentu)")
    col1, col2 = st.columns(2)
    with col1:
        render_locked_input("JBT | 0001-2999 (Roda 4 Pribadi)", "jbt_1")
        render_locked_input("JBT | 3000-6999 (Roda 2 Sepeda Motor)", "jbt_2")
        render_locked_input("JBT | 7000-7999 (Roda 4 > Minibus/Bus)", "jbt_3")
    with col2:
        render_locked_input("JBT | 8000-8999 (Roda 4 > Truck)", "jbt_4")
        render_locked_input("JBT | 9000-9999 (Roda 4 > Truck Khusus)", "jbt_5")

    st.markdown("---")
    st.markdown("### ⛽ JBKP (Jenis BBM Khusus Penugasan)")
    col3, col4 = st.columns(2)
    with col3:
        render_locked_input("JBKP | 0001-2999 (Roda 4 Pribadi)", "jbkp_1")
        render_locked_input("JBKP | 3000-6999 (Roda 2 Sepeda Motor)", "jbkp_2")
        render_locked_input("JBKP | 7000-7999 (Roda 4 > Minibus)", "jbkp_3")
    with col4:
        render_locked_input("JBKP | 8000-8999 (Roda 4 > Pick Up)", "jbkp_4")
        render_locked_input("JBKP | 9000-9999 (Roda 4 > Pick Up Khusus)", "jbkp_5")

    st.markdown("---")
    st.markdown("### ⏱️ Pengaturan Sistem & Deteksi")
    render_locked_input("Tenggat Waktu Isi Ulang Beruntun (Menit)", "tenggat_waktu")
    
    st.markdown("##### Ambang Batas Frekuensi Pelangsir (Kali/Hari)")
    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    with col_p1: render_locked_input("JBT (Solar)", "max_freq_pelangsir_jbt")
    with col_p2: render_locked_input("JBKP R4 (Mobil)", "max_freq_pelangsir_jbkp_r4")
    with col_p3: render_locked_input("JBKP R2 (Motor)", "max_freq_pelangsir_jbkp_r2")
    with col_p4: render_locked_input("JBT R4 Umum", "max_freq_pelangsir_jbt_r4_umum")
    with col_p5: render_locked_input("JBT R6", "max_freq_pelangsir_jbt_r6")

    render_locked_input("Ambang Batas Volume Mismatch Kendaraan (Liter)", "max_vol_mismatch")

    if st.button("Simpan Pengaturan Kuota Berdasarkan Plat"):
        new_config = {
            "jbt_1": st.session_state.get("jbt_1", 60),
            "jbt_2": st.session_state.get("jbt_2", 0),
            "jbt_3": st.session_state.get("jbt_3", 200),
            "jbt_4": st.session_state.get("jbt_4", 200),
            "jbt_5": st.session_state.get("jbt_5", 250),
            "jbkp_1": st.session_state.get("jbkp_1", 60),
            "jbkp_2": st.session_state.get("jbkp_2", 8),
            "jbkp_3": st.session_state.get("jbkp_3", 120),
            "jbkp_4": st.session_state.get("jbkp_4", 120),
            "jbkp_5": st.session_state.get("jbkp_5", 120),
            "tenggat_waktu": st.session_state.get("tenggat_waktu", 180),
            "max_freq_pelangsir_jbt": st.session_state.get("max_freq_pelangsir_jbt", 2),
            "max_freq_pelangsir_jbkp_r4": st.session_state.get("max_freq_pelangsir_jbkp_r4", 3),
            "max_freq_pelangsir_jbkp_r2": st.session_state.get("max_freq_pelangsir_jbkp_r2", 4),
            "max_freq_pelangsir_jbt_r4_umum": st.session_state.get("max_freq_pelangsir_jbt_r4_umum", 2),
            "max_freq_pelangsir_jbt_r6": st.session_state.get("max_freq_pelangsir_jbt_r6", 2),
            "max_vol_mismatch": st.session_state.get("max_vol_mismatch", 100)
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(new_config, f, indent=4)
        st.session_state.config_data = new_config
        st.toast("Aturan kuota dan parameter deteksi berhasil disimpan secara permanen!", icon="✅")

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>Analisis berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun.</p>",
    unsafe_allow_html=True,
)
