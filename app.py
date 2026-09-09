import pandas as pd
import streamlit as st

# Konfigurasi halaman
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    layout="wide",
)

# Styling CSS tambahan
st.markdown(
    """
    <style>
    .metric-card-top {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        text-align: left;
    }
    .metric-card-bottom {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 14px;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        text-align: left;
    }
    .empty-state {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 40px;
        border-radius: 8px;
        text-align: center;
        color: #6b7280;
        margin-top: 20px;
    }
    .card-container {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- HEADER UTAMA ---
col_head1, col_head2 = st.columns([6, 1])
with col_head1:
    st.markdown("## 🎛️ Monitor Subsidi & Deteksi Looping Nozzle")
with col_head2:
    st.markdown(
        """<div style="text-align: right; font-weight: bold; color: #cc0000; font-size: 14px; padding-top: 5px;">🔴 PERTAMINA RETAIL</div>""",
        unsafe_allow_html=True,
    )

st.write("---")

# --- BAGIAN UPLOAD FILE ---
uploaded_file = st.file_uploader(
    "Upload file data transaksi (CSV atau XLSX) tarikan SPBU",
    type=["csv", "xlsx"],
)

with st.expander("⚙️ Konfigurasi Aturan Kuota & Deteksi Rentang Waktu"):
    st.markdown("##### ⛽ Batas Kuota JBT (Solar)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        jbt_r4_pribadi = st.number_input("R4 Pribadi (1000-2999)", value=60)
    with c2:
        jbt_r2 = st.number_input("R2 Motor (3000-6999)", value=0)
    with c3:
        jbt_bus = st.number_input("Mini Bus/Bus (7000-7999)", value=200)
    with c4:
        jbt_truck = st.number_input("Truck/Khusus (8000-9999)", value=200)

    st.markdown("##### ⛽ Batas Kuota JBKP (Pertalite)")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        jbkp_r4_pribadi = st.number_input("R4 Pribadi / Umum (1000-2999)", value=80)
    with d2:
        jbkp_r2 = st.number_input("R2 Motor (3000-6999)", value=8)
    with d3:
        jbkp_bus = st.number_input("Mini Bus Umum (7000-7999)", value=100)
    with d4:
        jbkp_pickup = st.number_input("Pick Up Barang (8000-9999)", value=100)

    st.markdown("##### ⏱️ Deteksi Waktu Pengisian Singkat (Looping / Pengelens)")
    time_threshold_minutes = st.number_input(
        "Ambang Batas Jarak Waktu Pengisian Beruntun (Menit) pada Nozzle yang Sama", 
        value=15, 
        help="Jika plat berbeda atau sama mengisi pada nozzle yang sama dalam rentang waktu ini, sistem akan menandainya sebagai indikasi looping."
    )

# --- KONDISI: KETIKA BELUM ADA FILE ---
if uploaded_file is None:
    st.markdown(
        """
        <div class="empty-state">
            <span style="font-size: 32px;">📑</span>
            <p style="font-weight: 600; margin-top: 10px; font-size: 16px; color: #374151;">Belum ada data file yang dimuat</p>
            <p style="font-size: 14px;">Silakan upload file CSV/XLSX tarikan hose delivery untuk memulai analisis kuota dan deteksi waktu pengisian.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- KONDISI: KETIKA FILE SUDAH DI-UPLOAD ---
else:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        df.columns = [str(c).strip() for c in df.columns]

        # Deteksi kolom otomatis
        col_product = next((c for c in df.columns if any(k in c.lower() for k in ['product', 'bbm', 'nama barang', 'fuel', 'item'])), df.columns[0])
        col_plat = next((c for c in df.columns if any(k in c.lower() for k in ['payment', 'plat', 'nopol', 'vehicle', 'police'])), df.columns[1] if len(df.columns) > 1 else df.columns[0])
        col_vol = next((c for c in df.columns if any(k in c.lower() for k in ['vol', 'liter', 'quantity', 'qty', 'jumlah'])), df.columns[-1])
        col_time = next((c for c in df.columns if any(k in c.lower() for k in ['time', 'date', 'waktu', 'tanggal', 'jam'])), None)
        col_nozzle = next((c for c in df.columns if any(k in c.lower() for k in ['nozzle', 'hose', 'pompa', 'dispenser'])), None)
        col_id = next((c for c in df.columns if any(k in c.lower() for k in ['id', 'transaction', 'trx', 'no trx'])), None)
        
        df['PRODUCT_CLEAN'] = df[col_product].astype(str).str.upper() if col_product in df.columns else "BIO_SOLAR"
        df['PLAT_CLEAN'] = df[col_plat].fillna("TANPA_NOPOL").astype(str).str.upper() if col_plat in df.columns else "TANPA_NOPOL"
        df['NOZZLE_CLEAN'] = df[col_nozzle].astype(str).str.upper() if col_nozzle and col_nozzle in df.columns else "NOZZLE_1"
        
        if col_vol in df.columns:
            df['VOL_CLEAN'] = pd.to_numeric(df[col_vol].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
        else:
            df['VOL_CLEAN'] = 0.0

        df['TIME_OBJ'] = pd.to_datetime(df[col_time], errors='coerce') if col_time and col_time in df.columns else pd.date_range('2026-09-01', periods=len(df), freq='H')
        df['TANGGAL_SAJA'] = df['TIME_OBJ'].dt.strftime('%Y-%m-%d')
        df['ID_CLEAN'] = df[col_id].astype(str) if col_id and col_id in df.columns else [str(i + 1) for i in range(len(df))]

        # Fungsi Klasifikasi Golongan Plat Berdasarkan Angka Pertama Seri Plat / Kategori
        def classify_vehicle_and_quota(plat_str, product_name):
            import re
            numbers = re.findall(r'\d+', plat_str)
            if not numbers:
                # Default jika tidak ada angka
                return "R4 Pribadi / Umum", (jbt_r4_pribadi if "SOLAR" in product_name else jbkp_r4_pribadi)
            
            first_num_str = numbers[0]
            prefix_val = int(first_num_str[0]) if len(first_num_str) > 0 else 1
            
            is_jbt = "SOLAR" in product_name
            
            if prefix_val in [1, 2]:
                return "R4 Pribadi / Umum", (jbt_r4_pribadi if is_jbt else jbkp_r4_pribadi)
            elif prefix_val in [3, 4, 5, 6]:
                return "R2 Motor", (jbt_r2 if is_jbt else jbkp_r2)
            elif prefix_val == 7:
                return "Mini Bus / Bus Umum", (jbt_bus if is_jbt else jbkp_bus)
            else: # 8, 9
                return "Truck / Pick Up Barang / Khusus", (jbt_truck if is_jbt else jbkp_pickup)

        # Terapkan klasifikasi ke dataframe
        df['GOLONGAN'] = [classify_vehicle_and_quota(p, pr)[0] for p, pr in zip(df['PLAT_CLEAN'], df['PRODUCT_CLEAN'])]
        df['KUOTA_BATAS'] = [classify_vehicle_and_quota(p, pr)[1] for p, pr in zip(df['PLAT_CLEAN'], df['PRODUCT_CLEAN'])]

        # Urutkan berdasarkan waktu untuk mendeteksi jeda singkat antar transaksi di nozzle yang sama (looping/pengelens)
        df = df.sort_values(by=['NOZZLE_CLEAN', 'TIME_OBJ'])
        df['DIFF_MINUTES'] = df.groupby('NOZZLE_CLEAN')['TIME_OBJ'].diff().dt.total_seconds().div(60).fillna(999)
        df['IS_LOOPING_RISK'] = df['DIFF_MINUTES'] <= time_threshold_minutes

        mask_jbt = df['PRODUCT_CLEAN'].str.contains('SOLAR|BIO', case=False, na=False)
        mask_jbkp = df['PRODUCT_CLEAN'].str.contains('PERTALITE', case=False, na=False)
        
        df_jbt = df[mask_jbt].copy()
        df_jbkp = df[mask_jbkp].copy()

        def get_rekap_advanced(sub_df):
            if sub_df.empty:
                return pd.DataFrame(columns=["PLAT", "TANGGAL", "GOLONGAN", "ISI", "TOTAL_LITER", "KUOTA_BATAS", "STATUS"])
            
            agg = sub_df.groupby(['PLAT_CLEAN', 'TANGGAL_SAJA', 'GOLONGAN', 'KUOTA_BATAS']).agg(
                ISI=('VOL_CLEAN', 'count'),
                TOTAL_LITER=('VOL_CLEAN', 'sum'),
                HAS_LOOPING=('IS_LOOPING_RISK', 'any')
            ).reset_index()
            
            agg.rename(columns={'PLAT_CLEAN': 'PLAT', 'TANGGAL_SAJA': 'TANGGAL'}, inplace=True)
            
            def check_status(r):
                if r['TOTAL_LITER'] > r['KUOTA_BATAS'] or r['HAS_LOOPING']:
                    return "⚠️ Perlu Diperiksa"
                return "✅ Normal"

            agg['STATUS'] = agg.apply(check_status, axis=1)
            return agg.sort_values(by='TOTAL_LITER', ascending=False)

        rekap_jbt = get_rekap_advanced(df_jbt)
        rekap_jbkp = get_rekap_advanced(df_jbkp)

        total_jbt = len(df_jbt)
        total_jbkp = len(df_jbkp)
        no_nopol_count = len(df[df['PLAT_CLEAN'].str.contains('TANPA|KOSONG|-|NAN|^$', regex=True, na=False)])
        
        over_jbt = len(rekap_jbt[rekap_jbt['STATUS'] == "⚠️ Perlu Diperiksa"]) if not rekap_jbt.empty else 0
        over_jbkp = len(rekap_jbkp[rekap_jbkp['STATUS'] == "⚠️ Perlu Diperiksa"]) if not rekap_jbkp.empty else 0
        total_over = over_jbt + over_jbkp
        total_plat_unik = len(rekap_jbt) + len(rekap_jbkp)
        normal_val = max(0, total_plat_unik - total_over)

        # --- KARTU METRIK ATAS ---
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.markdown(f"""
            <div class="metric-card-top">
                <span style="font-size: 18px; font-weight: bold; color: #111827;">⛽ {total_over}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Plat melewati kuota / indikasi looping nozzle</p>
            </div>
            """, unsafe_allow_html=True)
        with c_m2:
            st.markdown(f"""
            <div class="metric-card-top">
                <span style="font-size: 18px; font-weight: bold; color: #111827;">🚫 {no_nopol_count}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Transaksi subsidi tanpa nopol</p>
            </div>
            """, unsafe_allow_html=True)
        with c_m3:
            st.markdown(f"""
            <div class="metric-card-top">
                <span style="font-size: 18px; font-weight: bold; color: #111827;">⏱️ {int(df['IS_LOOPING_RISK'].sum())}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Frekuensi jeda waktu < {time_threshold_minutes} mnt</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # --- KARTU METRIK BAWAH ---
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f"""
            <div class="metric-card-bottom">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_jbt + total_jbkp}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Total Transaksi</p>
            </div>
            """, unsafe_allow_html=True)
        with s2:
            st.markdown(f"""
            <div class="metric-card-bottom">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_over}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Sangat mencurigakan</p>
            </div>
            """, unsafe_allow_html=True)
        with s3:
            st.markdown(f"""
            <div class="metric-card-bottom">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_plat_unik}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Perlu diperiksa</p>
            </div>
            """, unsafe_allow_html=True)
        with s4:
            st.markdown(f"""
            <div class="metric-card-bottom">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{normal_val}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Normal</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        
        search_input = st.text_input("Cari plat nomor...", placeholder="Ketik plat nomor...")
        st.write("")

        def render_tab_content(sub_df, rekap_df, label_prod):
            st.markdown(f"#### Rekapitulasi Berdasarkan Golongan Plat & Rentang Waktu — {label_prod}")
            st.caption("Deteksi otomatis rentang plat nomor, kuota spesifik, dan peringatan jeda waktu singkat antar pengisian pada hose nozzle.")
            
            if sub_df.empty or rekap_df.empty:
                st.info(f"Tidak ada data transaksi {label_prod}.")
                return

            filtered = rekap_df
            if search_input:
                filtered = rekap_df[rekap_df['PLAT'].str.contains(search_input.upper(), na=False)]

            for _, row in filtered.iterrows():
                plat = row['PLAT']
                tgl = row['TANGGAL']
                gol = row['GOLONGAN']
                limit
