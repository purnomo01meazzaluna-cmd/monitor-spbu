import re as regex_lib
from io import BytesIO
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
import openpyxl.utils
import pandas as pd
from PIL import Image as PILImage
import streamlit as st

# Konfigurasi halaman
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    layout="wide",
)

# Styling CSS
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

# Header
col_head1, col_head2 = st.columns([6, 1])
with col_head1:
    st.markdown("## 🎛️ Monitor Subsidi & Deteksi Looping Nozzle")
with col_head2:
    st.markdown(
        """<div style="text-align: right; font-weight: bold; color: #cc0000; font-size: 14px; padding-top: 5px;">🔴 PERTAMINA RETAIL</div>""",
        unsafe_allow_html=True,
    )

st.write("---")

uploaded_file = st.file_uploader(
    "Upload file data transaksi (CSV atau XLSX) tarikan SPBU",
    type=["csv", "xlsx"],
)

with st.expander("⚙️ Konfigurasi Aturan Kuota & Deteksi Rentang Waktu"):
    st.markdown("##### ⛽ Batas Kuota JBT (Solar)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        jbt_r4_pribadi = st.number_input("R4 Pribadi (1000-2999)", value=60, key="jbt_r4")
    with c2:
        jbt_r2 = st.number_input("R2 Motor (3000-6999)", value=0, key="jbt_r2")
    with c3:
        jbt_bus = st.number_input("Mini Bus/Bus (7000-7999)", value=200, key="jbt_bus")
    with c4:
        jbt_truck = st.number_input("Truck/Khusus (8000-9999)", value=200, key="jbt_truck")

    st.markdown("##### ⛽ Batas Kuota JBKP (Pertalite)")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        jbkp_r4_pribadi = st.number_input("R4 Pribadi / Umum (1000-2999)", value=80, key="jbkp_r4")
    with d2:
        jbkp_r2 = st.number_input("R2 Motor (3000-6999)", value=8, key="jbkp_r2")
    with d3:
        jbkp_bus = st.number_input("Mini Bus Umum (7000-7999)", value=100, key="jbkp_bus")
    with d4:
        jbkp_pickup = st.number_input("Pick Up Barang (8000-9999)", value=100, key="jbkp_pickup")

    st.markdown("##### ⏱️ Deteksi Waktu Pengisian Singkat (Looping)")
    time_threshold_minutes = st.number_input(
        "Ambang Batas Jarak Waktu Pengisian Beruntun Plat Sama (Menit)",
        value=15,
        help="Jika plat nomor yang sama mengisi dalam rentang waktu kurang dari nilai ini, ditandai sebagai looping.",
        key="time_thresh_input",
    )

if uploaded_file is None:
    st.markdown(
        """
        <div class="empty-state">
            <span style="font-size: 32px;">📑</span>
            <p style="font-weight: 600; margin-top: 10px; font-size: 16px; color: #374151;">Belum ada data file yang dimuat</p>
            <p style="font-size: 14px;">Silakan upload file CSV/XLSX tarikan hose delivery untuk memulai analisis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df.columns = [str(c).strip() if pd.notna(c) else f"Unnamed_{i}" for i, c in enumerate(df.columns)]
        cols_lower = {str(c).lower(): c for c in df.columns}

        def find_col(keywords):
            for kw in keywords:
                for c_lower, c_orig in cols_lower.items():
                    if kw in c_lower:
                        return c_orig
            return None

        col_product = find_col(["product", "bbm", "nama barang", "fuel", "item"]) or df.columns[0]
        col_payment = find_col(["payment", "bayar", "metode"]) or df.columns[1]
        col_vol = find_col(["vol", "liter", "quantity", "qty", "jumlah", "volume"]) or df.columns[-1]
        col_time = find_col(["time", "waktu", "jam"])
        col_date = find_col(["date", "tanggal"])
        col_nozzle = find_col(["nozzle", "hose", "pompa", "dispenser"])
        col_id = find_col(["id", "transaction", "trx", "no trx"])

        # Standarisasi Nilai
        df["PRODUCT_CLEAN"] = df[col_product].fillna("BIO_SOLAR").astype(str).str.upper() if col_product in df.columns else "BIO_SOLAR"
        
        raw_plat_series = df[col_payment].fillna("TANPA_NOPOL").astype(str).str.upper() if col_payment in df.columns else pd.Series(["TANPA_NOPOL"] * len(df))
        df["PLAT_CLEAN"] = raw_plat_series.apply(
            lambda x: regex_lib.sub(r"^(CASH|DEBIT|QRIS|TRANSFER|EDC|NON[\s_-]CASH|PUMP\s*TES)\s*", "", str(x)).strip()
        )
        df["PLAT_CLEAN"] = df["PLAT_CLEAN"].replace("", "TANPA_NOPOL")

        df["NOZZLE_CLEAN"] = df[col_nozzle].fillna("NOZZLE_1").astype(str).str.upper() if col_nozzle and col_nozzle in df.columns else "NOZZLE_1"

        if col_vol in df.columns:
            df["VOL_CLEAN"] = pd.to_numeric(
                df[col_vol].astype(str).str.replace(r"[^0-9.]", "", regex=True),
                errors="coerce",
            ).fillna(0.0)
        else:
            df["VOL_CLEAN"] = 0.0

        # Penanganan Tanggal dan Waktu
        if col_date and col_time and col_date in df.columns and col_time in df.columns:
            df["DATETIME_STR"] = df[col_date].astype(str) + " " + df[col_time].astype(str)
            df["TIME_OBJ"] = pd.to_datetime(df["DATETIME_STR"], errors="coerce").fillna(pd.Timestamp("2026-08-31 00:00:00"))
        elif col_time and col_time in df.columns:
            df["TIME_OBJ"] = pd.to_datetime(df[col_time], errors="coerce").fillna(pd.Timestamp("2026-08-31 00:00:00"))
        else:
            df["TIME_OBJ"] = pd.date_range("2026-08-31 05:00:00", periods=len(df), freq="min")

        df["TANGGAL_CLEAN"] = df["TIME_OBJ"].dt.strftime("%Y-%m-%d")
        df["ID_CLEAN"] = df[col_id].fillna("").astype(str) if col_id and col_id in df.columns else [str(2305800 + i) for i in range(len(df))]

        # Klasifikasi Golongan dan Kuota Batas
        def classify_vehicle_and_quota(plat_str, product_name):
            numbers = regex_lib.findall(r"\d+", str(plat_str))
            is_jbt = "SOLAR" in str(product_name) or "BIO" in str(product_name)

            if not numbers:
                return "R4 Pribadi / Umum", (jbt_r4_pribadi if is_jbt else jbkp_r4_pribadi)

            prefix_val = int(numbers[0][0])
            if prefix_val in [1, 2]:
                return "R4 Pribadi / Umum", (jbt_r4_pribadi if is_jbt else jbkp_r4_pribadi)
            elif prefix_val in [3, 4, 5, 6]:
                return "R2 Motor", (jbt_r2 if is_jbt else jbkp_r2)
            elif prefix_val == 7:
                return "Mini Bus / Bus Umum", (jbt_bus if is_jbt else jbkp_bus)
            else:
                return "Truck / Pick Up Barang / Khusus", (jbt_truck if is_jbt else jbkp_pickup)

        df["GOLONGAN"] = [classify_vehicle_and_quota(p, pr)[0] for p, pr in zip(df["PLAT_CLEAN"], df["PRODUCT_CLEAN"])]
        df["KUOTA_BATAS"] = [classify_vehicle_and_quota(p, pr)[1] for p, pr in zip(df["PLAT_CLEAN"], df["PRODUCT_CLEAN"])]

        # Urutkan berdasarkan Plat dan Waktu untuk menghitung DIFF_MIN secara akurat
        df = df.sort_values(by=["PLAT_CLEAN", "TANGGAL_CLEAN", "TIME_OBJ"]).reset_index(drop=True)

        # Hitung Selisih Menit (DIFF_MIN) per Plat & Tanggal
        df["PREV_TIME"] = df.groupby(["PLAT_CLEAN", "TANGGAL_CLEAN"])["TIME_OBJ"].shift(1)
        df["DIFF_MIN"] = (df["TIME_OBJ"] - df["PREV_TIME"]).dt.total_seconds() / 60.0
        df["DIFF_MIN"] = df["DIFF_MIN"].fillna(999).round(2)
        
        # Penanda Looping
        df["IS_LOOPING"] = (df["DIFF_MIN"] <= time_threshold_minutes) & (df["DIFF_MIN"] > 0)

        # Pisahkan dataset berdasarkan produk JBT / JBKP
        mask_jbt = df["PRODUCT_CLEAN"].str.contains("SOLAR|BIO", case=False, na=False)
        mask_jbkp = df["PRODUCT_CLEAN"].str.contains("PERTALITE", case=False, na=False)

        df_jbt = df[mask_jbt].copy()
        df_jbkp = df[mask_jbkp].copy()

        def get_rekap_advanced(sub_df):
            if sub_df.empty:
                return pd.DataFrame(columns=["PLAT", "TANGGAL", "GOLONGAN", "ISI", "TOTAL_LITER", "KUOTA_BATAS", "STATUS"])

            agg = (
                sub_df.groupby(["PLAT_CLEAN", "TANGGAL_CLEAN", "GOLONGAN", "KUOTA_BATAS"])
                .agg(
                    ISI=("VOL_CLEAN", "count"),
                    TOTAL_LITER=("VOL_CLEAN", "sum"),
                    HAS_LOOPING=("IS_LOOPING", "any"),
                )
                .reset_index()
            )

            agg.rename(columns={"PLAT_CLEAN": "PLAT", "TANGGAL_CLEAN": "TANGGAL"}, inplace=True)

            def check_status(r):
                if r["TOTAL_LITER"] > r["KUOTA_BATAS"] or r["HAS_LOOPING"]:
                    return "⚠️ Perlu Diperiksa"
                return "✅ Normal"

            agg["STATUS"] = agg.apply(check_status, axis=1)
            return agg.sort_values(by="TOTAL_LITER", ascending=False)

        rekap_jbt = get_rekap_advanced(df_jbt)
        rekap_jbkp = get_rekap_advanced(df_jbkp)

        total_jbt = len(df_jbt)
        total_jbkp = len(df_jbkp)
        no_nopol_count = len(df[df["PLAT_CLEAN"].str.contains("TANPA|KOSONG|-|NAN|^$", regex=True, na=False)])

        over_jbt = len(rekap_jbt[rekap_jbt["STATUS"] == "⚠️ Perlu Diperiksa"]) if not rekap_jbt.empty else 0
        over_jbkp = len(rekap_jbkp[rekap_jbkp["STATUS"] == "⚠️ Perlu Diperiksa"]) if not rekap_jbkp.empty else 0
        total_over = over_jbt + over_jbkp
        total_plat_unik = len(rekap_jbt) + len(rekap_jbkp)
        normal_val = max(0, total_plat_unik - total_over)

        # Kartu Metrik Top
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.markdown(f"""<div class="metric-card-top"><span style="font-size: 18px; font-weight: bold; color: #111827;">⛽ {total_over}</span><p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Plat melewati kuota / indikasi looping</p></div>""", unsafe_allow_html=True)
        with c_m2:
            st.markdown(f"""<div class="metric-card-top"><span style="font-size: 18px; font-weight: bold; color: #111827;">🚫 {no_nopol_count}</span><p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Transaksi subsidi tanpa nopol</p></div>""", unsafe_allow_html=True)
        with c_m3:
            st.markdown(f"""<div class="metric-card-top"><span style="font-size: 18px; font-weight: bold; color: #111827;">⏱️ {int(df['IS_LOOPING'].sum())}</span><p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Frekuensi jeda waktu < {time_threshold_minutes} mnt</p></div>""", unsafe_allow_html=True)

        st.write("")

        # Kartu Metrik Bottom
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f"""<div class="metric-card-bottom"><span style="font-size: 20px; font-weight: bold; color: #111827;">{total_jbt + total_jbkp}</span><p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Total Transaksi</p></div>""", unsafe_allow_html=True)
        with s2:
            st.markdown(f"""<div class="metric-card-bottom"><span style="font-size: 20px; font-weight: bold; color: #111827;">{total_over}</span><p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Sangat mencurigakan</p></div>""", unsafe_allow_html=True)
        with s3:
            st.markdown(f"""<div class="metric-card-bottom"><span style="font-size: 20px; font-weight: bold; color: #111827;">{total_plat_unik}</span><p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Perlu diperiksa</p></div>""", unsafe_allow_html=True)
        with s4:
            st.markdown(f"""<div class="metric-card-bottom"><span style="font-size: 20px; font-weight: bold; color: #111827;">{normal_val}</span><p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Normal</p></div>""", unsafe_allow_html=True)

        st.write("")

        search_input = st.text_input("Cari plat nomor...", placeholder="Ketik plat nomor...", key="main_search_input")
        st.write("")

        def render_tab_content(sub_df, rekap_df, label_prod):
            st.markdown(f"#### Rekapitulasi Berdasarkan Golongan Plat & Rentang Waktu — {label_prod}")
            st.caption("Deteksi otomatis rentang plat nomor, kuota spesifik, dan peringatan jeda waktu singkat antar pengisian.")

            if sub_df.empty or rekap_df.empty:
                st.info(f"Tidak ada data transaksi {label_prod}.")
                return

            col_btn1, col_btn2, col_space = st.columns([2, 2.5, 5.5])

            def to_excel(df_data):
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_data.to_excel(writer, index=False, sheet_name="Laporan")
                return output.getvalue()

            def to_excel_with_full_columns(sub_df_trx, label_category):
                output = BytesIO()
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Transaksi & Foto"

                export_df = sub_df_trx.copy()
                
                # Format Tanggal/Waktu
                if "TIME_OBJ" in export_df.columns:
                    export_df["TIME_OBJ_STR"] = export_df["TIME_OBJ"].dt.strftime("%Y-%m-%d %H:%M:%S")

                # Ambil seluruh kolom asli + kolom analisis tambahan secara presisi
                cols_to_exclude = ["TIME_OBJ", "DATETIME_STR", "PREV_TIME"]
                base_cols = [c for c in export_df.columns if c not in cols_to_exclude]
                
                clean_export_df = export_df[base_cols].copy()

                headers = list(clean_export_df.columns) + ["BUKTI_FOTO"]
                ws.append(headers)
                ws.row_dimensions[1].height = 25
                
                col_letter_foto = openpyxl.utils.get_column_letter(len(headers))
                ws.column_dimensions[col_letter_foto].width = 24

                for row_idx, (idx, row_data) in enumerate(clean_export_df.iterrows(), start=2):
                    ws.append(list(row_data))
                    ws.row_dimensions[row_idx].height = 65

                    cam_file = st.session_state.get(f"cam_{label_category}_{idx}")
                    gal_file = st.session_state.get(f"gal_{label_category}_{idx}")
                    matched_file = cam_file or gal_file

                    if matched_file is not None:
                        try:
                            # Pembacaan byte gambar aman tanpa mengubah penunjuk berkas
                            if hasattr(matched_file, "getvalue"):
                                img_bytes = matched_file.getvalue()
                            else:
                                matched_file.seek(0)
                                img_bytes = matched_file.read()

                            if img_bytes:
                                pil_img = PILImage.open(BytesIO(img_bytes))
                                
                                # Konversi ke mode RGB jika mode gambar RGBA / P
                                if pil_img.mode in ("RGBA", "P"):
                                    pil_img = pil_img.convert("RGB")
                                
                                pil_img.thumbnail((120, 75))

                                img_io = BytesIO()
                                pil_img.save(img_io, format="PNG")
                                img_io.seek(0)

                                xl_img = OpenpyxlImage(img_io)
                                cell_coordinate = f"{col_letter_foto}{row_idx}"
                                ws.add_image(xl_img, cell_coordinate)
                        except Exception as e:
                            st.error(f"Gagal memuat gambar pada baris {row_idx}: {e}")

                wb.save(output)
                return output.getvalue()

            with col_btn1:
                st.download_button(
                    label="📥 Unduh tindak lanjut (Excel)",
                    data=to_excel(rekap_df),
                    file_name=f"laporan_tindak_lanjut_{label_prod.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"btn_tindak_{label_prod}",
                )

            with col_btn2:
                st.download_button(
                    label="📥 Unduh transaksi + foto (Excel)",
                    data=to_excel_with_full_columns(sub_df, label_prod),
                    file_name=f"laporan_transaksi_foto_{label_prod.lower()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"btn_foto_{label_prod}",
                )

            st.write("")

            filtered = rekap_df
            if search_input:
                filtered = rekap_df[rekap_df["PLAT"].str.contains(search_input.upper(), na=False)]

            for _, row in filtered.iterrows():
                plat = row["PLAT"]
                tgl = row["TANGGAL"]
                gol = row["GOLONGAN"]
                limit = row["KUOTA_BATAS"]
                total_l = row["TOTAL_LITER"]
                isi_cnt = row["ISI"]
                status = row["STATUS"]
                pct = min(int((total_l / limit) * 100), 100) if limit > 0 else 100

                b_color = "#fef3c7" if status == "⚠️ Perlu Diperiksa" else "#d1fae5"
                t_color = "#92400e" if status == "⚠️ Perlu Diperiksa" else "#065f46"

                with st.container():
                    st.markdown(
                        f"""
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
                        """,
                        unsafe_allow_html=True,
                    )

                th_c1, th_c2, th_c3, th_c4, th_c5, th_c6, th_c7, th_c8, th_c9, th_c10 = st.columns([1.1, 0.8, 1.1, 1.1, 0.9, 0.8, 1.0, 1.0, 1.5, 1.5])
                with th_c1: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>BUKTI FOTO</span>", unsafe_allow_html=True)
                with th_c2: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>ID TRX</span>", unsafe_allow_html=True)
                with th_c3: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>WAKTU</span>", unsafe_allow_html=True)
                with th_c4: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>NOZZLE/PROD</span>", unsafe_allow_html=True)
                with th_c5: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>NOPOL</span>", unsafe_allow_html=True)
                with th_c6: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>VOL</span>", unsafe_allow_html=True)
                with th_c7: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>GOLONGAN</span>", unsafe_allow_html=True)
                with th_c8: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>STATUS</span>", unsafe_allow_html=True)
                with th_c9: st.markdown("<span style='font-size:11px; font-weight:bold; color:#4b5563;'>KETERANGAN</span>", unsafe_allow_html=True)
                with th_c10: st.markdown("<span style='font-size:11px; font-weight:bold; color:#cc5500;'>📝 CATATAN OPERATOR</span>", unsafe_allow_html=True)
                
                st.markdown("<hr style='margin: 4px 0 8px 0; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

                trx_detail = sub_df[(sub_df["PLAT_CLEAN"] == plat) & (sub_df["TANGGAL_CLEAN"] == tgl)]
                for trx in trx_detail.itertuples():
                    trx_idx = trx.Index
                    looping_badge = "<span style='color:red; font-weight:bold;'>(⚠️ Jeda Cepat)</span>" if trx.IS_LOOPING else ""

                    col_cctv, col_id_trx, col_time_trx, col_prod_trx, col_plat_trx, col_vol_trx, col_type_trx, col_stat_trx, col_reason_trx, col_note = st.columns([1.1, 0.8, 1.1, 1.1, 0.9, 0.8, 1.0, 1.0, 1.5, 1.5])
                    
                    with col_cctv:
                        cam_file = st.file_uploader("📷", type=["jpg", "png", "jpeg"], key=f"cam_{label_prod}_{trx_idx}", label_visibility="collapsed")
                        if cam_file is not None:
                            st.image(cam_file, width=110)

                        gal_file = st.file_uploader("🖼️", type=["jpg", "png", "jpeg"], key=f"gal_{label_prod}_{trx_idx}", label_visibility="collapsed")
                        if gal_file is not None:
                            st.image(gal_file, width=110)

                    with col_id_trx:
                        st.write(trx.ID_CLEAN)
                    with col_time_trx:
                        st.write(f"{trx.TIME_OBJ.strftime('%H:%M:%S')} {looping_badge}", unsafe_allow_html=True)
                    with col_prod_trx:
                        st.write(f"{trx.PRODUCT_CLEAN}")
                    with col_plat_trx:
                        st.markdown(f"**{plat}**")
                    with col_vol_trx:
                        st.write(f"{trx.VOL_CLEAN:.2f}L")
                    with col_type_trx:
                        st.markdown(f"<b>{trx.GOLONGAN}</b>", unsafe_allow_html=True)
                    with col_stat_trx:
                        st.markdown(f"<span style='background:{b_color}; color:{t_color}; padding:2px 6px; border-radius:10px; font-size:11px;'>{status}</span>", unsafe_allow_html=True)
                    with col_reason_trx:
                        reason_txt = f"Harian {total_l:.1f}L > Batas ({limit}L)" if total_l > limit else f"Jeda waktu {trx.DIFF_MIN:.1f} mnt"
                        st.markdown(f"<span style='color:#6b7280; font-size:12px;'>{reason_txt}</span>", unsafe_allow_html=True)
                    with col_note:
                        st.text_input("Catatan", placeholder="Tulis catatan...", key=f"note_{label_prod}_{trx_idx}", label_visibility="collapsed")

                    st.markdown("<hr style='margin: 5px 0; border-top: 1px solid #f3f4f6;'>", unsafe_allow_html=True)

        tab_jbt, tab_jbkp = st.tabs([f"JBT · Solar ({total_jbt})", f"JBKP · Pertalite ({total_jbkp})"])
        with tab_jbt:
            render_tab_content(df_jbt, rekap_jbt, "Solar")
        with tab_jbkp:
            render_tab_content(df_jbkp, rekap_jbkp, "Pertalite")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
