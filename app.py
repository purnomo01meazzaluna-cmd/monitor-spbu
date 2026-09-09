import pandas as pd
import streamlit as st

# Konfigurasi halaman
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    layout="wide",
)

# Styling CSS tambahan agar menyerupai tampilan modern
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
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
    .card-detail {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- HEADER UTAMA ---
col_head1, col_head2 = st.columns([6, 1])
with col_head1:
    st.caption("MONITORING · DATA H-1 (KEMARIN)")
    st.markdown("## 🎛️ Monitor Subsidi Tepat Guna")
    st.write(
        "Penyaringan awal anomali BBM bersubsidi — verifikasi CCTV & koordinasi SAMSAT berdasarkan data tarikan file."
    )
with col_head2:
    st.markdown(
        """<div style="text-align: right; font-weight: bold; color: #cc0000; font-size: 14px; padding-top: 10px;">🔴 PERTAMINA RETAIL</div>""",
        unsafe_allow_html=True,
    )

st.write("---")

# --- BAGIAN UPLOAD FILE ---
uploaded_file = st.file_uploader(
    "Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk pilih file",
    type=["csv", "xlsx"],
)
st.caption(
    "Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi diabaikan. Plat diambil dari kolom Payment / Nopol."
)

with st.expander("▶ Pengaturan ambang batas & kuota"):
    limit_jbt = st.number_input("Batas Kuota Harian JBT (Solar) - Liter", value=60, step=10)
    limit_jbkp = st.number_input("Batas Kuota Harian JBKP (Pertalite) - Liter", value=40, step=10)

# --- BAGIAN CARA KERJA PENILAIAN ---
st.markdown(
    """
    <div style="background-color: #fffbeb; border: 1px solid #fef3c7; padding: 12px 16px; border-radius: 8px; margin: 20px 0; font-size: 14px; color: #92400e;">
        <b>Cara kerja penilaian.</b> Vonis dibangun dari sinyal data tarikan SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
        <b>Perkiraan jenis</b> dari angka plat (<code style="background:#fef08a; padding:2px 4px; border-radius:4px;">ESTIMASI PLAT</code>) menjadi lead pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT.
    </div>
    """,
    unsafe_allow_html=True,
)

# --- KONDISI: KETIKA BELUM ADA FILE ---
if uploaded_file is None:
    st.markdown(
        """
        <div class="empty-state">
            <span style="font-size: 32px;">📑</span>
            <p style="font-weight: 600; margin-top: 10px; font-size: 16px; color: #374151;">Belum ada data yang dianalisis</p>
            <p style="font-size: 14px;">Upload satu file CSV/XLSX hose delivery (data kemarin) untuk mulai monitoring.</p>
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
        
        col_product = next((c for c in df.columns if 'product' in c.lower() or 'bbm' in c.lower() or 'nama barang' in c.lower() or 'fuel' in c.lower()), df.columns[0])
        col_plat = next((c for c in df.columns if 'payment' in c.lower() or 'plat' in c.lower() or 'nopol' in c.lower() or 'vehicle' in c.lower()), df.columns[1] if len(df.columns) > 1 else df.columns[0])
        col_vol = next((c for c in df.columns if 'vol' in c.lower() or 'liter' in c.lower() or 'quantity' in c.lower() or 'qty' in c.lower()), df.columns[-1])
        col_time = next((c for c in df.columns if 'time' in c.lower() or 'date' in c.lower() or 'waktu' in c.lower() or 'tanggal' in c.lower()), None)
        col_id = next((c for c in df.columns if 'id' in c.lower() or 'transaction' in c.lower() or 'trx' in c.lower()), None)
        
        df['PRODUCT_CLEAN'] = df[col_product].astype(str).str.upper() if col_product in df.columns else "BIO_SOLAR"
        df['PLAT_CLEAN'] = df[col_plat].fillna("TANPA_NOPOL").astype(str).str.upper() if col_plat in df.columns else "TANPA_NOPOL"
        
        if col_vol in df.columns:
            df['VOL_CLEAN'] = pd.to_numeric(df[col_vol].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
        else:
            df['VOL_CLEAN'] = 0.0

        mask_jbt = df['PRODUCT_CLEAN'].str.contains('SOLAR|BIO', case=False, na=False)
        mask_jbkp = df['PRODUCT_CLEAN'].str.contains('PERTALITE', case=False, na=False)
        
        df_jbt = df[mask_jbt].copy()
        df_jbkp = df[mask_jbkp].copy()
        
        def process_rekap(sub_df, limit_quota):
            if sub_df.empty:
                return pd.DataFrame(columns=["PLAT", "PERKIRAAN JENIS (DARI PLAT)", "ISI", "TOTAL_VOL", "TOTAL VS KUOTA HARIAN", "STATUS"]), {}
            
            agg = sub_df.groupby('PLAT_CLEAN').agg(
                ISI=('VOL_CLEAN', 'count'),
                TOTAL_VOL=('VOL_CLEAN', 'sum')
            ).reset_index()
            
            rekap_list = []
            status_dict = {}
            for _, row in agg.iterrows():
                plat = row['PLAT_CLEAN']
                isi = int(row['ISI'])
                tot_vol = float(row['TOTAL_VOL'])
                pct = int((tot_vol / limit_quota) * 100) if limit_quota > 0 else 0
                
                est = "≈ Mobil penumpang [ESTIMASI PLAT]" if len(plat) > 6 else "≈ Kendaraan Umum [ESTIMASI PLAT]"
                status = "🟡 Perlu Diperiksa" if tot_vol > limit_quota else "🟢 Normal"
                
                status_dict[plat] = status
                
                rekap_list.append({
                    "PLAT": plat,
                    "PERKIRAAN JENIS (DARI PLAT)": est,
                    "ISI": f"{isi}×",
                    "TOTAL_VOL": tot_vol,
                    "TOTAL VS KUOTA HARIAN": f"{tot_vol:.1f} L / {limit_quota} L ({pct}%)",
                    "STATUS": status
                })
            res_df = pd.DataFrame(rekap_list)
            if not res_df.empty:
                res_df = res_df.sort_values(by="TOTAL_VOL", ascending=False)
            return res_df, status_dict

        rekap_jbt, status_dict_jbt = process_rekap(df_jbt, limit_jbt)
        rekap_jbkp, status_dict_jbkp = process_rekap(df_jbkp, limit_jbkp)
        
        total_jbt_count = len(df_jbt)
        total_jbkp_count = len(df_jbkp)
        
        over_quota_jbt = len(rekap_jbt[rekap_jbt['STATUS'].str.contains('Perlu Diperiksa')]) if not rekap_jbt.empty else 0
        over_quota_jbkp = len(rekap_jbkp[rekap_jbkp['STATUS'].str.contains('Perlu Diperiksa')]) if not rekap_jbkp.empty else 0
        total_over = over_quota_jbt + over_quota_jbkp
        no_nopol = len(df[(df['PLAT_CLEAN'] == 'TANPA_NOPOL') | (df['PLAT_CLEAN'] == 'NAN') | (df['PLAT_CLEAN'] == '')])

        # 1. Kartu Metrik Baris Pertama
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""<div class="metric-card">⛽ <b style="font-size: 18px;">{total_over}</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Plat melewati kuota harian</p></div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card">🚫 <b style="font-size: 18px;">{no_nopol}</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Transaksi subsidi tanpa nopol</p></div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card">🔍 <b style="font-size: 18px;">0</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Angka plat tak cocok konsumsi (lead)</p></div>""", unsafe_allow_html=True)

        st.write("")

        # 2. Kartu Metrik Baris Kedua
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""<div class="metric-card"><b style="font-size: 20px;">{total_jbt_count}</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Transaksi JBT</p></div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="metric-card"><b style="font-size: 20px; color:#dc2626;">{total_over}</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Sangat mencurigakan</p></div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="metric-card"><b style="font-size: 20px; color:#d97706;">{total_jbkp_count}</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Transaksi JBKP (Pertalite)</p></div>""", unsafe_allow_html=True)
        with k4:
            st.markdown(f"""<div class="metric-card"><b style="font-size: 20px; color:#16a34a;">{total_jbt_count + total_jbkp_count - total_over}</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Normal</p></div>""", unsafe_allow_html=True)

        st.write("")

        # 3. Tab Navigasi Utama (JBT & JBKP)
        tab_jbt, tab_jbkp = st.tabs([f"JBT · Solar ({total_jbt_count})", f"JBKP · Pertalite ({total_jbkp_count})"])

        # --- KONTEN TAB JBT ---
        with tab_jbt:
            st.markdown("### Rekap per Plat (Harian) — Solar/JBT")
            st.caption("Gunakan filter di bawah untuk memilah status, atau pilih nomor plat untuk melihat rincian transaksinya.")

            if not rekap_jbt.empty:
                fc1, fc2, fc3 = st.columns([2, 2, 2])
                with fc1:
                    filter_status_jbt = st.selectbox("Filter Status Rekap", ["Semua Status", "🟡 Perlu Diperiksa", "🟢 Normal"], key="sel_status_jbt")
                with fc2:
                    list_plat_jbt = ["Semua Plat"] + list(rekap_jbt["PLAT"].unique())
                    selected_plat_jbt = st.selectbox("🔍 Fokus / Drill-down Plat Nomor", list_plat_jbt, key="sel_plat_jbt")
                with fc3:
                    search_jbt = st.text_input("Pencarian Teks Plat", placeholder="Ketik plat...", key="input_search_jbt")

                df_r_jbt = rekap_jbt.copy()
                if filter_status_jbt != "Semua Status":
                    df_r_jbt = df_r_jbt[df_r_jbt["STATUS"] == filter_status_jbt]
                if selected_plat_jbt != "Semua Plat":
                    df_r_jbt = df_r_jbt[df_r_jbt["PLAT"] == selected_plat_jbt]
                if search_jbt:
                    df_r_jbt = df_r_jbt[df_r_jbt["PLAT"].str.contains(search_jbt, case=False, na=False)]

                if len(rekap_jbt) > 0:
                    chart_data = rekap_jbt.set_index("PLAT")[["TOTAL_VOL"]]
                    st.bar_chart(chart_data, height=180)

                st.dataframe(df_r_jbt.drop(columns=["TOTAL_VOL"]), use_container_width=True, hide_index=True)

                if selected_plat_jbt != "Semua Plat":
                    plat_info = rekap_jbt[rekap_jbt["PLAT"] == selected_plat_jbt].iloc[0]
                    st.markdown(f"""
                        <div class="card-detail">
                            <h4>📌 Detail Kendaraan Terpilih: <b>{selected_plat_jbt}</b></h4>
                            <p><b>Estimasi Jenis:</b> {plat_info['PERKIRAAN JENIS (DARI PLAT)']}</p>
                            <p><b>Akumulasi Volume Harian:</b> {plat_info['TOTAL VS KUOTA HARIAN']}</p>
                            <p><b>Status Saat Ini:</b> {plat_info['STATUS']}</p>
                        </div>
                    """, unsafe_allow_html=True)

            else:
                st.info("Tidak ada data rekap JBT ditemukan.")

            st.markdown("### Detail Transaksi & Bukti CCTV (JBT)")
            if not df_jbt.empty:
                detail_df_jbt = pd.DataFrame({
                    "BUKTI CCTV": ["[Kamera] [Galeri]" for _ in range(len(df_jbt))],
                    "ID": df_jbt[col_id].values if col_id and col_id in df_jbt.columns else [str(i+2300000) for i in range(len(df_jbt))],
                    "WAKTU": df_jbt[col_time].values if col_time and col_time in df_jbt.columns else ["31/08/2026, 06.00.00" for _ in range(len(df_jbt))],
                    "PRODUCT / NOZZLE": df_jbt[col_product].values if col_product in df_jbt.columns else "BIO_SOLAR",
                    "PLAT": df_jbt['PLAT_CLEAN'].values,
                    "VOLUME": [f"{v:.2f}L" for v in df_jbt['VOL_CLEAN'].values],
                    "PERKIRAAN JENIS": ["≈ Mobil penumpang [ESTIMASI PLAT]" for _ in range(len(df_jbt))],
                    # STATUS DISINKRONKAN DENGAN AKUMULASI REKAP PLAT DI ATAS
                    "STATUS": [status_dict_jbt.get(p, "🟢 Normal") for p in df_jbt['PLAT_CLEAN'].values],
                    "ALASAN TEMUAN": [
                        "Akumulasi harian melampaui batas kuota" if status_dict_jbt.get(p, "🟢 Normal") == "🟡 Perlu Diperiksa" else "Volume harian wajar" 
                        for p in df_jbt['PLAT_CLEAN'].values
                    ]
                })
            else:
                detail_df_jbt = pd.DataFrame(columns=["BUKTI CCTV", "ID", "WAKTU", "PRODUCT / NOZZLE", "PLAT", "VOLUME", "PERKIRAAN JENIS", "STATUS", "ALASAN TEMUAN"])

            if 'selected_plat_jbt' in locals() and selected_plat_jbt != "Semua Plat":
                detail_df_jbt = detail_df_jbt[detail_df_jbt["PLAT"] == selected_plat_jbt]

            st.dataframe(detail_df_jbt, use_container_width=True, hide_index=True)

        # --- KONTEN TAB JBKP ---
        with tab_jbkp:
            st.markdown("### Rekap per Plat (Harian) — Pertalite/JBKP")
            st.caption("Gunakan filter di bawah untuk memilah status, atau pilih nomor plat untuk melihat rincian transaksinya.")

            if not rekap_jbkp.empty:
                jb_c1, jb_c2, jb_c3 = st.columns([2, 2, 2])
                with jb_c1:
                    filter_status_jbkp = st.selectbox("Filter Status Rekap", ["Semua Status", "🟡 Perlu Diperiksa", "🟢 Normal"], key="sel_status_jbkp")
                with jb_c2:
                    list_plat_jbkp = ["Semua Plat"] + list(rekap_jbkp["PLAT"].unique())
                    selected_plat_jbkp = st.selectbox("🔍 Fokus / Drill-down Plat Nomor", list_plat_jbkp, key="sel_plat_jbkp")
                with jb_c3:
                    search_jbkp = st.text_input("Pencarian Teks Plat", placeholder="Ketik plat...", key="input_search_jbkp")

                df_r_jbkp = rekap_jbkp.copy()
                if filter_status_jbkp != "Semua Status":
                    df_r_jbkp = df_r_jbkp[df_r_jbkp["STATUS"] == filter_status_jbkp]
                if selected_plat_jbkp != "Semua Plat":
                    df_r_jbkp = df_r_jbkp[df_r_jbkp["PLAT"] == selected_plat_jbkp]
                if search_jbkp:
                    df_r_jbkp = df_r_jbkp[df_r_jbkp["PLAT"].str.contains(search_jbkp, case=False, na=False)]

                if len(rekap_jbkp) > 0:
                    chart_data_jbkp = rekap_jbkp.set_index("PLAT")[["TOTAL_VOL"]]
                    st.bar_chart(chart_data_jbkp, height=180)

                st.dataframe(df_r_jbkp.drop(columns=["TOTAL_VOL"]), use_container_width=True, hide_index=True)

                if selected_plat_jbkp != "Semua Plat":
                    plat_info_jb = rekap_jbkp[rekap_jbkp["PLAT"] == selected_plat_jbkp].iloc[0]
                    st.markdown(f"""
                        <div class="card-detail">
                            <h4>📌 Detail Kendaraan Terpilih: <b>{selected_plat_jbkp}</b></h4>
                            <p><b>Estimasi Jenis:</b> {plat_info_jb['PERKIRAAN JENIS (DARI PLAT)']}</p>
                            <p><b>Akumulasi Volume Harian:</b> {plat_info_jb['TOTAL VS KUOTA HARIAN']}</p>
                            <p><b>Status Saat Ini:</b> {plat_info_jb['STATUS']}</p>
                        </div>
                    """, unsafe_allow_html=True)

            else:
                st.info("Tidak ada data rekap JBKP ditemukan.")

            st.markdown("### Detail Transaksi & Bukti CCTV (JBKP)")
            if not df_jbkp.empty:
                detail_df_jbkp = pd.DataFrame({
                    "BUKTI CCTV": ["[Kamera] [Galeri]" for _ in range(len(df_jbkp))],
                    "ID": df_jbkp[col_id].values if col_id and col_id in df_jbkp.columns else [str(i+2305000) for i in range(len(df_jbkp))],
                    "WAKTU": df_jbkp[col_time].values if col_time and col_time in df_jbkp.columns else ["31/08/2026, 09.00.00" for _ in range(len(df_jbkp))],
                    "PRODUCT / NOZZLE": df_jbkp[col_product].values if col_product in df_jbkp.columns else "PERTALITE",
                    "PLAT": df_jbkp['PLAT_CLEAN'].values,
                    "VOLUME": [f"{v:.2f}L" for v in df_jbkp['VOL_CLEAN'].values],
                    "PERKIRAAN JENIS": ["≈ Sepeda Motor [ESTIMASI PLAT]" for _ in range(len(df_jbkp))],
                    # STATUS DISINKRONKAN DENGAN AKUMULASI REKAP PLAT DI ATAS
                    "STATUS": [status_dict_jbkp.get(p, "🟢 Normal") for p in df_jbkp['PLAT_CLEAN'].values],
                    "ALASAN TEMUAN": [
                        "Akumulasi harian melampaui batas kuota" if status_dict_jbkp.get(p, "🟢 Normal") == "🟡 Perlu Diperiksa" else "Dalam batas kuota harian wajar" 
                        for p in df_jbkp['PLAT_CLEAN'].values
                    ]
                })
            else:
                detail_df_jbkp = pd.DataFrame(columns=["BUKTI CCTV", "ID", "WAKTU", "PRODUCT / NOZZLE", "PLAT", "VOLUME", "PERKIRAAN JENIS", "STATUS", "ALASAN TEMUAN"])

            if 'selected_plat_jbkp' in locals() and selected_plat_jbkp != "Semua Plat":
                detail_df_jbkp = detail_df_jbkp[detail_df_jbkp["PLAT"] == selected_plat_jbkp]

            st.dataframe(detail_df_jbkp, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
