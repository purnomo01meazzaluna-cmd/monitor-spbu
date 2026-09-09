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
    st.markdown("## 🎛️ Monitor Subsidi Tepat Guna")
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

with st.expander("▶ Pengaturan ambang batas & kuota harian"):
    limit_jbt = st.number_input("Batas Kuota Harian JBT (Solar) - Liter", value=200, step=10)
    limit_jbkp = st.number_input("Batas Kuota Harian JBKP (Pertalite) - Liter", value=120, step=10)

# --- KONDISI: KETIKA BELUM ADA FILE ---
if uploaded_file is None:
    st.markdown(
        """
        <div class="empty-state">
            <span style="font-size: 32px;">📑</span>
            <p style="font-weight: 600; margin-top: 10px; font-size: 16px; color: #374151;">Belum ada data file yang dimuat</p>
            <p style="font-size: 14px;">Silakan upload file CSV/XLSX tarikan hose delivery untuk melihat rekapitulasi dan metrik yang akurat.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- KONDISI: KETIKA FILE SUDAH DI-UPLOAD ---
else:
    try:
        # Pembacaan file dinamis
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Bersihkan spasi pada nama kolom
        df.columns = [str(c).strip() for c in df.columns]

        # Deteksi otomatis kolom penting dari file tarikan
        col_product = next((c for c in df.columns if any(k in c.lower() for k in ['product', 'bbm', 'nama barang', 'fuel', 'item', 'barang'])), df.columns[0])
        col_plat = next((c for c in df.columns if any(k in c.lower() for k in ['payment', 'plat', 'nopol', 'vehicle', 'police', 'nomor polisi'])), df.columns[1] if len(df.columns) > 1 else df.columns[0])
        col_vol = next((c for c in df.columns if any(k in c.lower() for k in ['vol', 'liter', 'quantity', 'qty', 'jumlah'])), df.columns[-1])
        col_time = next((c for c in df.columns if any(k in c.lower() for k in ['time', 'date', 'waktu', 'tanggal', 'jam'])), None)
        col_id = next((c for c in df.columns if any(k in c.lower() for k in ['id', 'transaction', 'trx', 'no trx', 'nomor'])), None)
        
        # Normalisasi data ke dalam dataframe bersih
        df['PRODUCT_CLEAN'] = df[col_product].astype(str).str.upper() if col_product in df.columns else "BIO_SOLAR"
        df['PLAT_CLEAN'] = df[col_plat].fillna("TANPA_NOPOL").astype(str).str.upper() if col_plat in df.columns else "TANPA_NOPOL"
        
        if col_vol in df.columns:
            df['VOL_CLEAN'] = pd.to_numeric(df[col_vol].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
        else:
            df['VOL_CLEAN'] = 0.0

        df['TIME_CLEAN'] = df[col_time].astype(str) if col_time and col_time in df.columns else "-"
        df['ID_CLEAN'] = df[col_id].astype(str) if col_id and col_id in df.columns else [str(i + 1) for i in range(len(df))]

        # Pemisahan kategori JBT (Solar / Bio Solar) dan JBKP (Pertalite)
        mask_jbt = df['PRODUCT_CLEAN'].str.contains('SOLAR|BIO', case=False, na=False)
        mask_jbkp = df['PRODUCT_CLEAN'].str.contains('PERTALITE', case=False, na=False)
        
        df_jbt = df[mask_jbt].copy()
        df_jbkp = df[mask_jbkp].copy()
        
        # Fungsi menghitung rekap per plat secara akurat dari data file
        def get_rekap(sub_df, limit_quota):
            if sub_df.empty:
                return pd.DataFrame(columns=["PLAT", "ESTIMASI JENIS", "ISI", "TOTAL_LITER", "STATUS"])
            agg = sub_df.groupby('PLAT_CLEAN').agg(
                ISI=('VOL_CLEAN', 'count'),
                TOTAL_LITER=('VOL_CLEAN', 'sum')
            ).reset_index()
            agg.rename(columns={'PLAT_CLEAN': 'PLAT'}, inplace=True)
            agg['ESTIMASI JENIS'] = "≈ Mobil penumpang"
            agg['STATUS'] = agg['TOTAL_LITER'].apply(lambda x: "⚠️ Perlu Diperiksa" if x > limit_quota else "✅ Normal")
            return agg.sort_values(by='ISI', ascending=False)

        rekap_jbt = get_rekap(df_jbt, limit_jbt)
        rekap_jbkp = get_rekap(df_jbkp, limit_jbkp)

        # Perhitungan Metrik Akurat Berdasarkan Data Aktual File
        total_jbt = len(df_jbt)
        total_jbkp = len(df_jbkp)
        
        # Transaksi subsidi tanpa nopol (plat kosong / tanpa nomor polisi)
        no_nopol_count = len(df[df['PLAT_CLEAN'].str.contains('TANPA|KOSONG|-|NAN|^$', regex=True, na=False)])
        
        # Plat yang melewati kuota harian
        plat_over_jbt = len(rekap_jbt[rekap_jbt['TOTAL_LITER'] > limit_jbt]) if not rekap_jbt.empty else 0
        plat_over_jbkp = len(rekap_jbkp[rekap_jbkp['TOTAL_LITER'] > limit_jbkp]) if not rekap_jbkp.empty else 0
        total_over = plat_over_jbt + plat_over_jbkp

        total_plat_unik = len(rekap_jbt) + len(rekap_jbkp)
        normal_val = max(0, total_plat_unik - total_over)

        # --- TAMPILKAN KARTU METRIK ATAS ---
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"""
            <div class="metric-card-top">
                <span style="font-size: 18px; font-weight: bold; color: #111827;">⛽ {total_over}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Plat melewati kuota harian</p>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
            <div class="metric-card-top">
                <span style="font-size: 18px; font-weight: bold; color: #111827;">🚫 {no_nopol_count}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Transaksi subsidi tanpa nopol</p>
            </div>
            """, unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""
            <div class="metric-card-top">
                <span style="font-size: 18px; font-weight: bold; color: #111827;">🔍 0</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Angka plat tak cocok konsumsi (lead)</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # --- TAMPILKAN KARTU METRIK BAWAH ---
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.markdown(f"""
            <div class="metric-card-bottom">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_jbt}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Transaksi JBT</p>
            </div>
            """, unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""
            <div class="metric-card-bottom">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_over}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Sangat mencurigakan</p>
            </div>
            """, unsafe_allow_html=True)
        with col_s3:
            st.markdown(f"""
            <div class="metric-card-bottom">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_plat_unik}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Perlu diperiksa</p>
            </div>
            """, unsafe_allow_html=True)
        with col_s4:
            st.markdown(f"""
            <div class="metric-card-bottom">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{normal_val}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Normal</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        
        # Tombol Filter & Aksi
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1.5, 1.5])
        with col_f1:
            search_input = st.text_input("Cari plat nomor...", placeholder="Ketik plat nomor...")
        with col_f2:
            st.write("")
            st.button("Analisis ulang")
        with col_f3:
            st.write("")
            st.button("Unduh tindak lanjut (Excel)")
        with col_f4:
            st.write("")
            st.button("Unduh transaksi + foto (Excel)", type="primary")

        st.write("")

        def render_dynamic_tab(sub_df, limit_quota, product_label, rekap_df):
            st.markdown(f"#### Rekap per Plat (Harian) — {product_label}")
            st.caption("Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT.")
            
            if sub_df.empty or rekap_df.empty:
                st.info(f"Tidak ada data transaksi {product_label} pada file ini.")
                return

            # Filter pencarian plat jika diisi
            filtered_rekap = rekap_df
            if search_input:
                filtered_rekap = rekap_df[rekap_df['PLAT'].str.contains(search_input.upper(), na=False)]

            for _, row in filtered_rekap.iterrows():
                plat = row['PLAT']
                total_liter = row['TOTAL_LITER']
                isi_count = row['ISI']
                pct = min(int((total_liter / limit_quota) * 100), 100)
                
                with st.container():
                    st.markdown(f"""
                    <div class="card-container">
                        <table style="width:100%; border:none;">
                            <tr>
                                <td style="width:15%; font-weight:bold; font-size:16px;">{plat}</td>
                                <td style="width:25%;">≈ Mobil penumpang <span style="background:#e5e7eb; padding:2px 6px; border-radius:4px; font-size:11px;">ESTIMASI PLAT</span></td>
                                <td style="width:10%;">{isi_count}×</td>
                                <td style="width:35%;">
                                    <div style="font-size:13px; margin-bottom:4px;">{total_liter:.1f} L / {limit_quota} L (batas terlonggar)</div>
                                    <div style="background:#e5e7eb; border-radius:4px; width:100%; height:8px;">
                                        <div style="background:#16a34a; width:{pct}%; height:8px; border-radius:4px;"></div>
                                    </div>
                                </td>
                                <td style="width:15%; text-align:right;">
                                    <span style="background:#fef3c7; color:#92400e; padding:4px 8px; border-radius:12px; font-size:12px; font-weight:600;">⚠️ Perlu Diperiksa</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    transactions = sub_df[sub_df['PLAT_CLEAN'] == plat]
                    for _, trx in transactions.iterrows():
                        col_cctv, col_id_trx, col_time_trx, col_prod_trx, col_plat_trx, col_vol_trx, col_type_trx, col_stat_trx, col_reason_trx = st.columns([1.2, 0.9, 1.3, 1.2, 1.0, 0.9, 1.2, 1.1, 1.8])
                        
                        with col_cctv:
                            st.button("📷 Kamera", key=f"cam_{trx['ID_CLEAN']}_{plat}")
                            st.button("🖼️ Galeri", key=f"gal_{trx['ID_CLEAN']}_{plat}")
                        with col_id_trx:
                            st.write(trx['ID_CLEAN'])
                        with col_time_trx:
                            st.write(trx['TIME_CLEAN'])
                        with col_prod_trx:
                            st.write(f"{trx['PRODUCT_CLEAN']}")
                        with col_plat_trx:
                            st.markdown(f"**{plat}**")
                        with col_vol_trx:
                            st.write(f"{trx['VOL_CLEAN']:.2f}L")
                        with col_type_trx:
                            st.markdown("≈ Mobil penumpang<br><span style='background:#e5e7eb; padding:1px 4px; border-radius:3px; font-size:10px;'>ESTIMASI PLAT</span>", unsafe_allow_html=True)
                        with col_stat_trx:
                            st.markdown("<span style='background:#fef3c7; color:#92400e; padding:2px 6px; border-radius:10px; font-size:11px;'>⚠️ Perlu Diperiksa</span>", unsafe_allow_html=True)
                        with col_reason_trx:
                            st.markdown(f"<span style='color:#6b7280; font-size:12px;'>Total harian {total_liter:.1f}L > jatah ({limit_quota}L)</span>", unsafe_allow_html=True)
                        
                        st.markdown("<hr style='margin: 5px 0; border-top: 1px solid #f3f4f6;'>", unsafe_allow_html=True)

        tab_jbt, tab_jbkp = st.tabs([f"JBT · Solar ({total_jbt})", f"JBKP · Pertalite ({total_jbkp})"])
        
        with tab_jbt:
            render_dynamic_tab(df_jbt, limit_jbt, "Solar/JBT", rekap_jbt)
        with tab_jbkp:
            render_dynamic_tab(df_jbkp, limit_jbkp, "Pertalite/JBKP", rekap_jbkp)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
