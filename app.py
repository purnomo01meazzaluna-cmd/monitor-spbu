import datetime
import io
import re
import tempfile
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PILImage
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    page_icon="⛽",
    layout="wide",
)

# Custom CSS untuk merapikan tampilan dan tombol khusus
st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        border: 1px solid #e5e7eb;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        border-color: #f59e0b !important;
        color: #d97706 !important;
    }
    .stButton button {
        width: 100%;
        font-size: 11px !important;
        padding: 4px 6px !important;
    }
    div[data-testid="stDownloadButton"] > button[kind="secondary"] {
        background-color: #e28743 !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDownloadButton"] > button[kind="secondary"]:hover {
        background-color: #cf7535 !important;
        color: white !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Inisialisasi Riwayat Unduhan di Session State
if "download_history" not in st.session_state:
    st.session_state["download_history"] = []

st.markdown("### 📊 MONITORING · DATA H-1 (KEMARIN)")
st.markdown("## 📁 Monitor Subsidi Tepat Guna & Bank Data")
st.markdown("---")

# Sidebar Pengaturan Batas Kuota & Bank Data Unduhan (Menggunakan Tabs di Sidebar)
with st.sidebar:
    st.header("⚙️ Menu Samping")

    sb_tab1, sb_tab2 = st.tabs(
        ["⚙️ Pengaturan Kuota", "📥 Bank Data Unduhan"]
    )

    with sb_tab1:
        st.subheader("Batas Kuota Harian")
        st.caption("Batas berdasarkan rentang angka pada plat nomor.")

        st.markdown("### ⛽ JBT (Solar)")
        limit_jbt_r4_pribadi = st.number_input(
            "1000-2999 | R4 Pribadi (L)", value=60, min_value=10, max_value=200
        )
        limit_jbt_bus = st.number_input(
            "7000-7999 | Bus Umum (L)", value=200, min_value=50, max_value=500
        )
        limit_jbt_truk_barang = st.number_input(
            "8000-8999 | Truk Barang (L)",
            value=200,
            min_value=50,
            max_value=500,
        )
        limit_jbt_truk_khusus = st.number_input(
            "9000-9999 | Truk Khusus (L)",
            value=200,
            min_value=50,
            max_value=500,
        )

        st.markdown("---")
        st.markdown("### ⛽ JBKP (Pertalite)")
        limit_jbkp_r4_pribadi = st.number_input(
            "1000-2999 | R4 Pribadi (L)", value=120, min_value=10, max_value=300
        )
        limit_jbkp_motor = st.number_input(
            "3000-6999 | Sepeda Motor (L)", value=8, min_value=1, max_value=20
        )
        limit_jbkp_umum_barang = st.number_input(
            "7000-9999 | R4 Umum/Barang (L)",
            value=120,
            min_value=10,
            max_value=300,
        )

    with sb_tab2:
        st.subheader("Bank Data Unduhan")
        st.caption(
            "Unduh rekapitulasi data transaksi dan laporan lengkap dengan bukti CCTV."
        )

        # Menampilkan Daftar Riwayat Unduhan di Bagian Atas Tab Bank Data
        st.markdown("#### 🕒 Riwayat Unduhan")
        if st.session_state["download_history"]:
            if st.button("🗑️ Bersihkan Riwayat", key="clear_history"):
                st.session_state["download_history"] = []
                st.rerun()

            for item in reversed(st.session_state["download_history"][-5:]):
                st.markdown(
                    f"<div style='font-size:11px; background:#f1f5f9; padding:6px; border-radius:6px; margin-bottom:5px;'>"
                    f"<b>{item['waktu']}</b><br>{item['nama_file']}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Belum ada riwayat unduhan.")

        st.markdown("---")
        sidebar_download_area = st.container()


# Fungsi Identifikasi Jenis Kendaraan & Batas Kuota Berdasarkan Angka Plat Nomor
def identifikasi_jenis_dan_kuota_dari_plat(plat_str, jenis_bbm):
    nopol_bersih = str(plat_str).upper().strip()
    match_angka = re.search(r"\d+", nopol_bersih)

    if not match_angka:
        if "SOLAR" in jenis_bbm.upper() or "JBT" in jenis_bbm.upper():
            return "Tanpa Nopol", limit_jbt_r4_pribadi
        else:
            return "Tanpa Nopol", limit_jbkp_r4_pribadi

    angka_nopol = int(match_angka.group(0))

    if "SOLAR" in jenis_bbm.upper() or "JBT" in jenis_bbm.upper():
        if 1000 <= angka_nopol <= 2999:
            return "R4 Pribadi", limit_jbt_r4_pribadi
        elif 3000 <= angka_nopol <= 6999:
            return "R2 (Sepeda Motor)", 0
        elif 7000 <= angka_nopol <= 7999:
            return "R4+ Bus (Umum)", limit_jbt_bus
        elif 8000 <= angka_nopol <= 8999:
            return "R4+ Truk Barang", limit_jbt_truk_barang
        elif 9000 <= angka_nopol <= 9999:
            return "R4+ Truk Khusus", limit_jbt_truk_khusus
        else:
            return "Di Luar Rentang", limit_jbt_r4_pribadi
    else:
        if 1000 <= angka_nopol <= 2999:
            return "R4 Pribadi", limit_jbkp_r4_pribadi
        elif 3000 <= angka_nopol <= 6999:
            return "R2 (Sepeda Motor)", limit_jbkp_motor
        elif 7000 <= angka_nopol <= 9999:
            return "R4 Umum / Barang", limit_jbkp_umum_barang
        else:
            return "Di Luar Rentang", limit_jbkp_umum_barang


# Area Unggah File Utama
uploaded_file = st.file_uploader(
    "Upload file laporan transaksi (CSV/XLSX)", type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Normalisasi nama kolom
        df.columns = df.columns.str.strip().str.title()

        # Deteksi nama kolom secara otomatis
        prod_col = next(
            (c for c in df.columns if "product" in c.lower() or "fuel" in c.lower()),
            df.columns[0],
        )
        vol_col = next(
            (c for c in df.columns if "volume" in c.lower() or "liter" in c.lower()),
            df.columns[1],
        )
        plat_col = next(
            (
                c
                for c in df.columns
                if "plat" in c.lower()
                or "nopol" in c.lower()
                or "vehicle" in c.lower()
                or "payment" in c.lower()
            ),
            df.columns[2],
        )
        time_col = next(
            (c for c in df.columns if "time" in c.lower() or "waktu" in c.lower()),
            None,
        )
        id_col = next(
            (c for c in df.columns if "id" in c.lower() or "trx" in c.lower()), None
        )

        df["Clean_Product"] = df[prod_col].astype(str).str.upper()

        if plat_col in df.columns:
            df[plat_col] = (
                df[plat_col]
                .astype(str)
                .str.replace(r"(?i)\bcash\b", "", regex=True)
                .str.strip()
            )

        # Filter produk Subsidi
        df_subsidi = df[
            df["Clean_Product"].str.contains("SOLAR|PERTALITE|JBT|JBKP|BIO", na=False)
        ].copy()

        df_jbt = df_subsidi[
            df_subsidi["Clean_Product"].str.contains("SOLAR|JBT|BIO", na=False)
        ]
        df_jbkp = df_subsidi[
            df_subsidi["Clean_Product"].str.contains("PERTALITE|JBKP", na=False)
        ]

        st.markdown(
            """
            <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #f59e0b; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; color: #334155;">
            Kolom <b>JENIS KENDARAAN</b> diidentifikasi dan dikelompokkan secara otomatis berdasarkan estimasi angka pada nomor polisi (plat nomor).
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_jbt, tab_jbkp = st.tabs(
            [f"JBT - Solar ({len(df_jbt)})", f"JBKP - Pertalite ({len(df_jbkp)})"]
        )

        def render_dashboard_tab(data_tab, nama_bbm):
            if data_tab.empty:
                st.info(f"Tidak ada data transaksi untuk kategori {nama_bbm}.")
                return

            if f"foto_dict_{nama_bbm}" not in st.session_state:
                st.session_state[f"foto_dict_{nama_bbm}"] = {}
            if f"noted_dict_{nama_bbm}" not in st.session_state:
                st.session_state[f"noted_dict_{nama_bbm}"] = {}

            total_trx_tab = len(data_tab)

            plat_totals = (
                data_tab.groupby(plat_col)[vol_col].sum().to_dict()
                if plat_col and vol_col in data_tab.columns
                else {}
            )

            count_plat_over = 0
            count_no_nopol = 0
            count_perlu_diperiksa = 0
            count_normal = 0

            for _, row in data_tab.iterrows():
                p = str(row[plat_col]) if plat_col in data_tab.columns else "N/A"
                v = float(row[vol_col]) if vol_col in data_tab.columns else 0.0
                tot_v = plat_totals.get(p, v)

                _, b_val = identifikasi_jenis_dan_kuota_dari_plat(p, nama_bbm)

                if p in ["N/A", "-", ""]:
                    count_no_nopol += 1
                    count_perlu_diperiksa += 1
                elif tot_v > b_val:
                    count_plat_over += 1
                    count_perlu_diperiksa += 1
                else:
                    count_normal += 1

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Plat melewati kuota harian", count_plat_over)
            with m2:
                st.metric("Transaksi subsidi tanpa nopol", count_no_nopol)
            with m3:
                st.metric(
                    "Angka plat tak cocok konsumsi",
                    count_perlu_diperiksa - count_plat_over - count_no_nopol,
                )

            m4, m5, m6, m7 = st.columns(4)
            with m4:
                st.metric("Total Transaksi Subsidi", total_trx_tab)
            with m5:
                st.metric("Sangat mencurigakan", 0)
            with m6:
                st.metric("Perlu diperiksa", count_perlu_diperiksa)
            with m7:
                st.metric("Normal", count_normal)

            st.markdown("<br>", unsafe_allow_html=True)

            col_f1, col_f2, col_f3, col_f4 = st.columns([1.8, 1.1, 1.3, 1.3])
            with col_f1:
                search_plat = st.text_input(
                    "Cari plat...", key=f"search_{nama_bbm}"
                )
            with col_f2:
                st.write("")
                if st.button("🔄 Refresh", key=f"btn_analisis_{nama_bbm}"):
                    st.rerun()
            with col_f3:
                st.write("")
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
                    df_export_base = data_tab.copy()
                    noted_dict = st.session_state[f"noted_dict_{nama_bbm}"]
                    df_export_base["Noted"] = [
                        noted_dict.get(idx, "") for idx in data_tab.index
                    ]
                    df_export_base.to_excel(writer, index=False, sheet_name="Data")

                file_name_1 = f"tindak_lanjut_{nama_bbm}.xlsx"
                if st.download_button(
                    "📥 Unduh Excel",
                    data=output_excel.getvalue(),
                    file_name=file_name_1,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{nama_bbm}",
                ):
                    w_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state["download_history"].append(
                        {"waktu": w_now, "nama_file": file_name_1}
                    )

            with col_f4:
                st.write("")
                if st.button(
                    "Unduh transaksi + foto (Excel)",
                    key=f"dl_foto_excel_{nama_bbm}",
                ):
                    with st.spinner("Menyiapkan file Excel beserta foto..."):
                        excel_foto_buffer = io.BytesIO()
                        foto_dict = st.session_state[f"foto_dict_{nama_bbm}"]
                        noted_dict = st.session_state[f"noted_dict_{nama_bbm}"]

                        export_rows = []
                        for idx, row in data_tab.iterrows():
                            trx_id = (
                                str(row[id_col])
                                if id_col and id_col in data_tab.columns
                                else "N/A"
                            )
                            trx_time = (
                                str(row[time_col])
                                if time_col and time_col in data_tab.columns
                                else "N/A"
                            )
                            trx_prod = (
                                str(row[prod_col])
                                if prod_col and prod_col in data_tab.columns
                                else "N/A"
                            )
                            trx_plat = (
                                str(row[plat_col])
                                if plat_col and plat_col in data_tab.columns
                                else "N/A"
                            )
                            trx_vol = (
                                float(row[vol_col])
                                if vol_col and vol_col in data_tab.columns
                                else 0.0
                            )

                            total_vol_plat = plat_totals.get(trx_plat, trx_vol)
                            (
                                jenis_kendaran,
                                batas_val,
                            ) = identifikasi_jenis_dan_kuota_dari_plat(
                                trx_plat, nama_bbm
                            )

                            if trx_plat in ["N/A", "-", ""]:
                                status = "Perlu Diperiksa"
                                alasan = (
                                    "Subsidi tanpa nopol — wajib dicatat per aturan"
                                )
                            elif total_vol_plat > batas_val:
                                status = "Perlu Diperiksa"
                                alasan = f"Total harian {total_vol_plat:.1f}L > jatah {jenis_kendaran} ({batas_val}L)"
                            else:
                                status = "Normal"
                                alasan = "Normal"

                            noted_val = noted_dict.get(idx, "")

                            export_rows.append(
                                {
                                    "Bukti CCTV": "",
                                    "ID Transaksi": trx_id,
                                    "Waktu": trx_time,
                                    "Product / Nozzle": trx_prod,
                                    "Plat Nomor": trx_plat,
                                    "Volume (L)": trx_vol,
                                    "Jenis Kendaraan": jenis_kendaran,
                                    "Status": status,
                                    "Alasan Temuan": alasan,
                                    "Noted": noted_val,
                                }
                            )

                        df_export = pd.DataFrame(export_rows)

                        with pd.ExcelWriter(
                            excel_foto_buffer, engine="openpyxl"
                        ) as writer:
                            df_export.to_excel(
                                writer, index=False, sheet_name="Laporan & Foto"
                            )

                        excel_foto_buffer.seek(0)
                        wb = openpyxl.load_workbook(excel_foto_buffer)
                        ws = wb.active

                        ws.column_dimensions["A"].width = 20
                        for col in [
                            "B",
                            "C",
                            "D",
                            "E",
                            "F",
                            "G",
                            "H",
                            "I",
                            "J",
                        ]:
                            ws.column_dimensions[col].width = 18

                        for i, (idx, row) in enumerate(data_tab.iterrows()):
                            row_idx = i + 2
                            ws.row_dimensions[row_idx].height = 80

                            foto_key = f"foto_trx_{nama_bbm}_{idx}"
                            if (
                                foto_key in foto_dict
                                and foto_dict[foto_key] is not None
                            ):
                                try:
                                    img_file = foto_dict[foto_key]
                                    pil_img = PILImage.open(img_file)
                                    pil_img.thumbnail((80, 80))

                                    with tempfile.NamedTemporaryFile(
                                        delete=False, suffix=".png"
                                    ) as tmp:
                                        pil_img.save(tmp.name)
                                        tmp_name = tmp.name

                                    img_to_excel = OpenpyxlImage(tmp_name)
                                    img_to_excel.anchor = f"A{row_idx}"
                                    ws.add_image(img_to_excel)
                                except Exception as ex:
                                    print(f"Gagal memuat gambar: {ex}")

                        final_output = io.BytesIO()
                        wb.save(final_output)
                        final_output.seek(0)

                        file_name_2 = f"laporan_transaksi_dan_foto_{nama_bbm}.xlsx"
                        st.session_state["download_history"].append(
                            {
                                "waktu": datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "nama_file": file_name_2,
                            }
                        )

                        st.download_button(
                            "📥 Klik Download File Final",
                            data=final_output.getvalue(),
                            file_name=file_name_2,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"final_dl_{nama_bbm}",
                        )

            # Bank Data Unduhan di Sidebar
            with sidebar_download_area:
                st.markdown(f"**Kategori Aktif:** `{nama_bbm}`")

                sidebar_excel = io.BytesIO()
                with pd.ExcelWriter(sidebar_excel, engine="openpyxl") as writer:
                    df_exp_sb = data_tab.copy()
                    noted_dict = st.session_state[f"noted_dict_{nama_bbm}"]
                    df_exp_sb["Noted"] = [
                        noted_dict.get(idx, "") for idx in data_tab.index
                    ]
                    df_exp_sb.to_excel(writer, index=False, sheet_name="Data")

                file_name_sb1 = (
                    f"bank_data_transaksi_{nama_bbm.replace('/', '_')}.xlsx"
                )
                if st.download_button(
                    label=f"📥 Unduh Transaksi ({nama_bbm})",
                    data=sidebar_excel.getvalue(),
                    file_name=file_name_sb1,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"sb_dl_{nama_bbm}",
                ):
                    st.session_state["download_history"].append(
                        {
                            "waktu": datetime.datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "nama_file": file_name_sb1,
                        }
                    )

                if st.button(
                    f"📥 Siapkan & Unduh + Foto ({nama_bbm})",
                    key=f"sb_btn_foto_{nama_bbm}",
                ):
                    with st.spinner("Menyiapkan bank data dengan foto..."):
                        excel_foto_buffer_sb = io.BytesIO()
                        foto_dict = st.session_state[f"foto_dict_{nama_bbm}"]
                        noted_dict = st.session_state[f"noted_dict_{nama_bbm}"]

                        export_rows_sb = []
                        for idx, row in data_tab.iterrows():
                            trx_id = (
                                str(row[id_col])
                                if id_col and id_col in data_tab.columns
                                else "N/A"
                            )
                            trx_time = (
                                str(row[time_col])
                                if time_col and time_col in data_tab.columns
                                else "N/A"
                            )
                            trx_prod = (
                                str(row[prod_col])
                                if prod_col and prod_col in data_tab.columns
                                else "N/A"
                            )
                            trx_plat = (
                                str(row[plat_col])
                                if plat_col and plat_col in data_tab.columns
                                else "N/A"
                            )
                            trx_vol = (
                                float(row[vol_col])
                                if vol_col and vol_col in data_tab.columns
                                else 0.0
                            )

                            total_vol_plat = plat_totals.get(trx_plat, trx_vol)
                            (
                                jenis_kendaran,
                                batas_val,
                            ) = identifikasi_jenis_dan_kuota_dari_plat(
                                trx_plat, nama_bbm
                            )

                            if trx_plat in ["N/A", "-", ""]:
                                status = "Perlu Diperiksa"
                                alasan = (
                                    "Subsidi tanpa nopol — wajib dicatat per aturan"
                                )
                            elif total_vol_plat > batas_val:
                                status = "Perlu Diperiksa"
                                alasan = f"Total harian {total_vol_plat:.1f}L > jatah {jenis_kendaran} ({batas_val}L)"
                            else:
                                status = "Normal"
                                alasan = "Normal"

                            noted_val = noted_dict.get(idx, "")

                            export_rows_sb.append(
                                {
                                    "Bukti CCTV": "",
                                    "ID Transaksi": trx_id,
                                    "Waktu": trx_time,
                                    "Product / Nozzle": trx_prod,
                                    "Plat Nomor": trx_plat,
                                    "Volume (L)": trx_vol,
                                    "Jenis Kendaraan": jenis_kendaran,
                                    "Status": status,
                                    "Alasan Temuan": alasan,
                                    "Noted": noted_val,
                                }
                            )

                        df_export_sb_final = pd.DataFrame(export_rows_sb)

                        with pd.ExcelWriter(
                            excel_foto_buffer_sb, engine="openpyxl"
                        ) as writer:
                            df_export_sb_final.to_excel(
                                writer, index=False, sheet_name="Laporan & Foto"
                            )

                        excel_foto_buffer_sb.seek(0)
                        wb_sb = openpyxl.load_workbook(excel_foto_buffer_sb)
                        ws_sb = wb_sb.active

                        ws_sb.column_dimensions["A"].width = 20
                        for col in [
                            "B",
                            "C",
                            "D",
                            "E",
                            "F",
                            "G",
                            "H",
                            "I",
                            "J",
                        ]:
                            ws_sb.column_dimensions[col].width = 18

                        for i, (idx, row) in enumerate(data_tab.iterrows()):
                            row_idx = i + 2
                            ws_sb.row_dimensions[row_idx].height = 80

                            foto_key = f"foto_trx_{nama_bbm}_{idx}"
                            if (
                                foto_key in foto_dict
                                and foto_dict[foto_key] is not None
                            ):
                                try:
                                    img_file = foto_dict[foto_key]
                                    pil_img = PILImage.open(img_file)
                                    pil_img.thumbnail((80, 80))

                                    with tempfile.NamedTemporaryFile(
                                        delete=False, suffix=".png"
                                    ) as tmp:
                                        pil_img.save(tmp.name)
                                        tmp_name = tmp.name

                                    img_to_excel = OpenpyxlImage(tmp_name)
                                    img_to_excel.anchor = f"A{row_idx}"
                                    ws_sb.add_image(img_to_excel)
                                except Exception as ex:
                                    print(f"Gagal memuat gambar: {ex}")

                        final_output_sb = io.BytesIO()
                        wb_sb.save(final_output_sb)
                        final_output_sb.seek(0)

                        file_name_sb2 = f"bank_data_transaksi_dan_foto_{nama_bbm.replace('/', '_')}.xlsx"
                        st.session_state["download_history"].append(
                            {
                                "waktu": datetime.datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "nama_file": file_name_sb2,
                            }
                        )

                        st.download_button(
                            label=f"📥 Download Final + Foto ({nama_bbm})",
                            data=final_output_sb.getvalue(),
                            file_name=file_name_sb2,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"sb_final_dl_{nama_bbm}",
                        )

                st.markdown("---")

            filtered_tab = data_tab.copy()
            if search_plat and plat_col in filtered_tab.columns:
                filtered_tab = filtered_tab[
                    filtered_tab[plat_col]
                    .astype(str)
                    .str.contains(search_plat, case=False, na=False)
                ]

            # --- 1. REKAP PER PLAT ---
            st.markdown(f"#### Rekap per Plat (Harian) — {nama_bbm}")
            st.caption(
                "Total pengisian plat sama dalam 1 hari vs batas kuota berdasarkan estimasi angka plat."
            )

            rekap_rows = []
            for p, total_v in plat_totals.items():
                jenis_kendaran, b_val = identifikasi_jenis_dan_kuota_dari_plat(
                    p, nama_bbm
                )
                stat = "Perlu Diperiksa" if total_v > b_val else "Normal"
                freq = (
                    len(filtered_tab[filtered_tab[plat_col] == p])
                    if plat_col in filtered_tab.columns
                    else 1
                )
                rekap_rows.append(
                    {
                        "Plat": p,
                        "Jenis": jenis_kendaran,
                        "Frekuensi": freq,
                        "Total": total_v,
                        "Batas": b_val,
                        "Status": stat,
                    }
                )

            df_rekap = pd.DataFrame(rekap_rows)
            if not df_rekap.empty:
                df_rekap = df_rekap.sort_values(by="Total", ascending=False)
                for _, r_row in df_rekap.iterrows():
                    pct = (
                        min(int((r_row["Total"] / r_row["Batas"]) * 100), 100)
                        if r_row["Batas"] > 0
                        else 100
                    )
                    rk_cols = st.columns([1.2, 1.8, 0.8, 2.5, 1.2])
                    with rk_cols[0]:
                        st.markdown(f"**{r_row['Plat']}**")
                    with rk_cols[1]:
                        st.markdown(
                            f"{r_row['Jenis']} <small>ESTIMASI PLAT</small>",
                            unsafe_allow_html=True,
                        )
                    with rk_cols[2]:
                        st.markdown(f"{r_row['Frekuensi']}×")
                    with rk_cols[3]:
                        st.progress(pct / 100)
                        st.caption(
                            f"{r_row['Total']:.1f} L / {r_row['Batas']} L · {pct}%"
                        )
                    with rk_cols[4]:
                        if r_row["Status"] == "Perlu Diperiksa":
                            st.markdown(
                                "<span style='background-color:#fef3c7;color:#d97706;padding:3px 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟠 Perlu Diperiksa</span>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                "<span style='background-color:#d1fae5;color:#059669;padding:3px 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟢 Normal</span>",
                                unsafe_allow_html=True,
                            )
                    st.markdown(
                        "<hr style='margin:3px 0;opacity:0.2;'>",
                        unsafe_allow_html=True,
                    )

            st.markdown("<br>", unsafe_allow_html=True)

            # --- 2. RINCIAN TRANSAKSI & BUKTI CCTV ---
            st.markdown(f"#### Rincian Transaksi & Bukti CCTV — {nama_bbm}")

            h_cols = st.columns([1.1, 0.8, 1.1, 1.2, 0.8, 0.8, 1.1, 1.0, 1.5, 1.3])
            with h_cols[0]:
                st.markdown("**BUKTI CCTV**")
            with h_cols[1]:
                st.markdown("**ID**")
            with h_cols[2]:
                st.markdown("**WAKTU**")
            with h_cols[3]:
                st.markdown("**PRODUCT / NOZZLE**")
            with h_cols[4]:
                st.markdown("**PLAT**")
            with h_cols[5]:
                st.markdown("**VOLUME**")
            with h_cols[6]:
                st.markdown("**JENIS KENDARAAN**")
            with h_cols[7]:
                st.markdown("**STATUS**")
            with h_cols[8]:
                st.markdown("**ALASAN TEMUAN**")
            with h_cols[9]:
                st.markdown("**NOTED**")
            st.markdown(
                "<hr style='margin:5px 0;opacity:0.5;'>", unsafe_allow_html=True
            )

            for idx, row in filtered_tab.iterrows():
                trx_id = (
                    str(row[id_col])
                    if id_col and id_col in filtered_tab.columns
                    else "N/A"
                )
                trx_time = (
                    str(row[time_col])
                    if time_col and time_col in filtered_tab.columns
                    else "N/A"
                )
                trx_prod = (
                    str(row[prod_col])
                    if prod_col and prod_col in filtered_tab.columns
                    else "N/A"
                )
                trx_plat = (
                    str(row[plat_col])
                    if plat_col and plat_col in filtered_tab.columns
                    else "N/A"
                )
                trx_vol = (
                    float(row[vol_col])
                    if vol_col and vol_col in filtered_tab.columns
                    else 0.0
                )

                total_vol_plat = plat_totals.get(trx_plat, trx_vol)
                jenis_kendaran, batas_val = identifikasi_jenis_dan_kuota_dari_plat(
                    trx_plat, nama_bbm
                )

                if trx_plat in ["N/A", "-", ""]:
                    status = "Perlu Diperiksa"
                    alasan = "Subsidi tanpa nopol — wajib dicatat per aturan"
                elif total_vol_plat > batas_val:
                    status = "Perlu Diperiksa"
                    alasan = f"Total harian {total_vol_plat:.1f}L > jatah {jenis_kendaran} ({batas_val}L)"
                else:
                    status = "Normal"
                    alasan = "Normal"

                r_cols = st.columns(
                    [1.1, 0.8, 1.1, 1.2, 0.8, 0.8, 1.1, 1.0, 1.5, 1.3]
                )
                foto_key = f"foto_trx_{nama_bbm}_{idx}"

                with r_cols[0]:
                    if foto_key in st.session_state[f"foto_dict_{nama_bbm}"]:
                        st.image(
                            st.session_state[f"foto_dict_{nama_bbm}"][foto_key],
                            width=55,
                        )
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            if st.button(
                                "📷", key=f"gc_{nama_bbm}_{idx}", help="Ganti Foto"
                            ):
                                st.session_state[
                                    f"edit_mode_{nama_bbm}_{idx}"
                                ] = "kamera"
                                st.rerun()
                        with rc2:
                            if st.button(
                                "🗑️", key=f"del_{nama_bbm}_{idx}", help="Hapus Foto"
                            ):
                                del st.session_state[f"foto_dict_{nama_bbm}"][
                                    foto_key
                                ]
                                if (
                                    f"edit_mode_{nama_bbm}_{idx}"
                                    in st.session_state
                                ):
                                    del st.session_state[
                                        f"edit_mode_{nama_bbm}_{idx}"
                                    ]
                                st.rerun()
                    else:
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            if st.button(
                                "📷", key=f"bc_{nama_bbm}_{idx}", help="Kamera"
                            ):
                                st.session_state[
                                    f"edit_mode_{nama_bbm}_{idx}"
                                ] = "kamera"
                                st.rerun()
                        with bc2:
                            if st.button(
                                "📁", key=f"bg_{nama_bbm}_{idx}", help="Galeri"
                            ):
                                st.session_state[
                                    f"edit_mode_{nama_bbm}_{idx}"
                                ] = "galeri"
                                st.rerun()

                    mode_edit = st.session_state.get(f"edit_mode_{nama_bbm}_{idx}")
                    if mode_edit == "kamera":
                        img_in = st.camera_input(
                            "Ambil Foto", key=f"cam_in_{nama_bbm}_{idx}"
                        )
                        if img_in is not None:
                            st.session_state[f"foto_dict_{nama_bbm}"][
                                foto_key
                            ] = img_in
                            del st.session_state[f"edit_mode_{nama_bbm}_{idx}"]
                            st.rerun()
                    elif mode_edit == "galeri":
                        img_in = st.file_uploader(
                            "Pilih Foto",
                            type=["jpg", "jpeg", "png"],
                            key=f"gal_in_{nama_bbm}_{idx}",
                        )
                        if img_in is not None:
                            st.session_state[f"foto_dict_{nama_bbm}"][
                                foto_key
                            ] = img_in
                            del st.session_state[f"edit_mode_{nama_bbm}_{idx}"]
                            st.rerun()

                with r_cols[1]:
                    st.write(trx_id)
                with r_cols[2]:
                    st.write(trx_time)
                with r_cols[3]:
                    st.write(trx_prod)
                with r_cols[4]:
                    st.markdown(f"**{trx_plat}**")
                with r_cols[5]:
                    st.write(f"{trx_vol:.2f}L")
                with r_cols[6]:
                    st.markdown(
                        f"{jenis_kendaran}<br><small>ESTIMASI PLAT</small>",
                        unsafe_allow_html=True,
                    )
                with r_cols[7]:
                    if status == "Perlu Diperiksa":
                        st.markdown(
                            "<span style='background-color:#fef3c7;color:#d97706;padding:3px 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟠 Perlu Diperiksa</span>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<span style='background-color:#d1fae5;color:#059669;padding:3px 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟢 Normal</span>",
                            unsafe_allow_html=True,
                        )
                with r_cols[8]:
                    if status == "Perlu Diperiksa":
                        st.error(alasan)
                    else:
                        st.success(alasan)
                with r_cols[9]:
                    noted_key = f"noted_input_{nama_bbm}_{idx}"
                    current_val = st.session_state[f"noted_dict_{nama_bbm}"].get(
                        idx, ""
                    )
                    val_input = st.text_input(
                        "Catatan",
                        value=current_val,
                        key=noted_key,
                        label_visibility="collapsed",
                        placeholder="Tulis catatan...",
                    )
                    st.session_state[f"noted_dict_{nama_bbm}"][idx] = val_input

                st.markdown(
                    "<hr style='margin:5px 0;opacity:0.3;'>", unsafe_allow_html=True
                )

        with tab_jbt:
            render_dashboard_tab(df_jbt, "Solar / JBT")

        with tab_jbkp:
            render_dashboard_tab(df_jbkp, "Pertalite / JBKP")

    except Exception as e:
        st.error(
            f"Gagal membaca format file. Pastikan struktur kolom sesuai. Detail: {e}"
        )

else:
    st.info(
        "Silakan unggah file laporan transaksi Anda pada area unggah di atas untuk memuat dashboard interaktif."
    )
