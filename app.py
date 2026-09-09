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

        # Deteksi kolom otomatis termasuk kolom jeda waktu mentah jika ada di file PU (Pompa Ukur / Nozzle)
        col_product = next((c for c in df.columns if any(k in c.lower() for k in ['product', 'bbm', 'nama barang', 'fuel', 'item'])), df.columns[0])
        col_plat = next((c for c in df.columns if any(k in c.lower() for k in ['payment', 'plat', 'nopol', 'vehicle', 'police'])), df.columns[1] if len(df.columns) > 1 else df.columns[0])
        col_vol = next((c for c in df.columns if any(k in c.lower() for k in ['vol', 'liter', 'quantity', 'qty', 'jumlah'])), df.columns[-1])
        col_time = next((c for c in df.columns if any(k in c.lower() for k in ['time', 'date', 'waktu', 'tanggal', 'jam'])), None)
        col_nozzle = next((c for c in df.columns if any(k in c.lower() for k in ['nozzle', 'hose', 'pompa', 'dispenser'])), None)
        col_id = next((c for c in df.columns if any(k in c.lower() for k in ['id', 'transaction', 'trx', 'no trx'])), None)
        
        # Deteksi kolom jeda waktu bawaan file (misal: 'jeda', 'durasi', 'interval', 'diff_time', 'elapsed')
        col_jeda_raw = next((c for c in df.columns if any(k in c.lower() for k in ['jeda', 'durasi', 'interval', 'elapsed', 'delay'])), None)
        
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

        # Fungsi Klasifikasi Golongan Plat Berdasarkan ANGKA PERTAMA dari Seri Angka Plat (Bukan Angka Tengah/Seri Wilayah)
        def classify_vehicle_and_quota(plat_str, product_name):
            import re
            # Cari seluruh kelompok angka pada plat nomor (misal: B 1234 ABC -> ['1234'])
            numbers = re.findall(r'\d+', plat_str)
            if not numbers:
                return "R4 Pribadi / Umum", (jbt_r4_pribadi if "SOLAR" in product_name else jbkp_r4_pribadi)
            
            # Ambil kelompok angka nomor polisi (biasanya kelompok angka pertama setelah huruf wilayah)
            series_num_str = numbers[0]
            if len(series_num_str) == 0:
                return "R4 Pribadi / Umum", (jbt_r4_pribadi if "SOLAR" in product_name else jbkp_r4_pribadi)
            
            # STRICT: Ambil HANYA digit paling depan/pertama dari angka seri plat tersebut (indeks ke-0)
            prefix_val = int(series_num_str[0])
            is_jbt = "SOLAR" in product_name
            
            if prefix_val in [1, 2]:
                return "R4 Pribadi / Umum", (jbt_r4_pribadi if is_jbt else jbkp_r4_pribadi)
            elif prefix_val in [3, 4, 5, 6]:
                return "R2 Motor", (jbt_r2 if is_jbt else jbkp_r2)
            elif prefix_val == 7:
                return "Mini Bus / Bus Umum", (jbt_bus if is_jbt else jbkp_bus)
            else:
                return "Truck / Pick Up Barang / Khusus", (jbt_truck if is_jbt else jbkp_pickup)

        df['GOLONGAN'] = [classify_vehicle_and_quota(p, pr)[0] for p, pr in zip(df['PLAT_CLEAN'], df['PRODUCT_CLEAN'])]
        df['KUOTA_BATAS'] = [classify_vehicle_and_quota(p, pr)[1] for p, pr in zip(df['PLAT_CLEAN'], df['PRODUCT_CLEAN'])]

        df = df.sort_values(by=['NOZZLE_CLEAN', 'TIME_OBJ'])
        
        # Mengambil jeda waktu: Prioritas dari kolom file PU jika tersedia, jika tidak hitung selisih waktu antar transaksi nozzle yang sama
        if col_jeda_raw and col_jeda_raw in df.columns:
            df['DIFF_MINUTES'] = pd.to_numeric(df[col_jeda_raw].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(999)
        else:
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
                limit = row['KUOTA_BATAS']
                total_l = row['TOTAL_LITER']
                isi_cnt = row['ISI']
                status = row['STATUS']
                pct = min(int((total_l / limit) * 100), 100) if limit > 0 else 100
                
                b_color = "#fef3c7" if status == "⚠️ Perlu Diperiksa" else "#d1fae5"
                t_color = "#92400e" if status == "⚠️ Perlu Diperiksa" else "#065f46"

                with st.container():
                    st.markdown(f"""
                    <div class="card-container">
                        <table style="width:100%; border:none;">
                            <tr>
                                <td style="width:18%; font-weight:bold; font-size:16px;">{plat}<br><span style="font-size:11px; color:#6b7280; font-weight:normal;">📅 {tgl}</span></td>
                                <td style="width:25%;"><b>{gol}</b><br><span style="background:#e5e7eb; padding:2px 6px; border-radius:4px; font-size:11px;">GOLONGAN PLAT</span></td>
                                <td style="width:10%;">{isi_cnt}× isi</td>
                                <td style="width:32%;">
                                    <div style="font-size:13px; margin-bottom:4px;">{total_l:.1f} L / {limit} L (Batas Golongan)</div>
                                    <div style="background:#e5e7eb; border-radius:4px; width:100%; height:8px;">
                                        <div style="background:{'#dc2626' if total_l > limit else '#16a34a'}; width:{pct}%; height:8px; border-radius:4px;"></div>
                                    </div>
                                </td>
                                <td style="width:15%; text-align:right;">
                                    <span style="background:{b_color}; color:{t_color}; padding:4px 8px; border-radius:12px; font-size:12px; font-weight:600;">{status}</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    trx_detail = sub_df[(sub_df['PLAT_CLEAN'] == plat) & (sub_df['TANGGAL_SAJA'] == tgl)]
                    for _, trx in trx_detail.iterrows():
                        looping_badge = "<span style='color:red; font-weight:bold;'>(⚠️ Jeda Cepat)</span>" if trx['IS_LOOPING_RISK'] else ""
                        
                        col_cctv, col_id_trx, col_time_trx, col_prod_trx, col_plat_trx, col_vol_trx, col_type_trx, col_stat_trx, col_reason_trx = st.columns([1.2, 0.9, 1.3, 1.2, 1.0, 0.9, 1.2, 1.1, 1.8])
                        with col_cctv:
                            st.button("📷 Kamera", key=f"cam_{trx['ID_CLEAN']}_{plat}_{tgl}")
                            st.button("🖼️ Galeri", key=f"gal_{trx['ID_CLEAN']}_{plat}_{tgl}")
                        with col_id_trx:
                            st.write(trx['ID_CLEAN'])
                        with col_time_trx:
                            st.write(f"{trx['TIME_OBJ'].strftime('%H:%M:%S')} {looping_badge}", unsafe_allow_html=True)
                        with col_prod_trx:
                            st.write(f"{trx['PRODUCT_CLEAN']} ({trx['NOZZLE_CLEAN']})")
                        with col_plat_trx:
                            st.markdown(f"**{plat}**")
                        with col_vol_trx:
                            st.write(f"{trx['VOL_CLEAN']:.2f}L")
                        with col_type_trx:
                            st.markdown(f"<b>{gol}</b>", unsafe_allow_html=True)
                        with col_stat_trx:
                            st.markdown(f"<span style='background:{b_color}; color:{t_color}; padding:2px 6px; border-radius:10px; font-size:11px;'>{status}</span>", unsafe_allow_html=True)
                        with col_reason_trx:
                            reason_txt = f"Harian {total_l:.1f}L > Batas ({limit}L)" if total_l > limit else f"Jeda waktu {trx['DIFF_MINUTES']:.0f} menit"
                            st.markdown(f"<span style='color:#6b7280; font-size:12px;'>{reason_txt}</span>", unsafe_allow_html=True)
                        
                        st.markdown("<hr style='margin: 5px 0; border-top: 1px solid #f3f4f6;'>", unsafe_allow_html=True)

        tab_jbt, tab_jbkp = st.tabs([f"JBT · Solar ({total_jbt})", f"JBKP · Pertalite ({total_jbkp})"])
        with tab_jbt:
            render_tab_content(df_jbt, rekap_jbt, "Solar / JBT")
        with tab_jbkp:
            render_tab_content(df_jbkp, rekap_jbkp, "Pertalite / JBKP")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
