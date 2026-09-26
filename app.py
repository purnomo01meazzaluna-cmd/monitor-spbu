import io
import pandas as pd
from PIL import Image as PILImage
import streamlit as st

# Konfigurasi Halaman Wide
st.set_page_config(
    layout="wide", page_title="Q & Q CHECK"
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-title {
        background-color: #003366;
        color: white;
        padding: 12px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .audit-card {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #dcdcdc;
        border-left: 4px solid #003366;
        margin-bottom: 10px;
        font-size: 13px;
    }
    .section-header {
        font-size: 18px;
        font-weight: bold;
        color: #003366;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    </style>
    <div class="main-title">SPBU Q & Q CHECK</div>
""",
    unsafe_allow_html=True,
)

audit_points = {
    "2.2.f": (
        "Berat Jenis (densitas) Pertalite (Oktan 90) diukur selama audit dalam "
        "rentang +/-0.03 dengan merujuk pada densitas dari penerimaan "
        "terakhir, yang diambil minimal 2 jam setelah pembongkaran",
        ["A", "F", "X"],
    ),
    "2.2.g": (
        "Berat Jenis (densitas) Pertamax (Oktan 92) diukur selama audit dalam "
        "rentang +/-0.03 dengan merujuk pada densitas dari penerimaan "
        "terakhir, yang diambil minimal 2 jam setelah pembongkaran",
        ["A", "F", "X"],
    ),
    "2.2.h": (
        "Berat Jenis (densitas) Pertamax Green (Oktan 95) diukur selama audit "
        "dalam rentang +/-0.03 dengan merujuk pada densitas dari penerimaan "
        "terakhir, yang diambil minimal 2 jam setelah pembongkaran",
        ["A", "F", "X"],
    ),
    "2.2.i": (
        "Berat Jenis (densitas) Pertamax Turbo (Oktan 98) diukur selama audit "
        "dalam rentang +/-0.03 dengan merujuk pada densitas dari penerimaan "
        "terakhir, yang diambil minimal 2 jam setelah pembongkaran",
        ["A", "F", "X"],
    ),
    "2.2.j": (
        "Berat Jenis (densitas) Bio Solar/Solar diukur selama audit dalam "
        "rentang +/-0.03 dengan merujuk pada densitas dari penerimaan "
        "terakhir, yang diambil minimal 2 jam setelah pembongkaran",
        ["A", "F", "X"],
    ),
    "2.2.k": (
        "Berat Jenis (densitas) Pertamina Dex diukur selama audit dalam rentang "
        "+/-0.03 dengan merujuk pada densitas dari penerimaan terakhir, yang "
        "diambil minimal 2 jam setelah pembongkaran",
        ["A", "F", "X"],
    ),
    "2.2.l": (
        "Berat Jenis (densitas) Dexlite diukur selama audit dalam rentang "
        "+/-0.03 dengan merujuk pada densitas dari penerimaan terakhir, yang "
        "diambil minimal 2 jam setelah pembongkaran",
        ["A", "F", "X"],
    ),
    "2.2.m": (
        "Volume BBM yang dikeluarkan dari nozzle yang diperiksa secara manual "
        "dan program berada dalam rentang toleransi (- 60 ml dengan bejana "
        "ukur 20 liter). (100% dari jumlah nozzle yang ada untuk SPBU "
        "Excellent dan 50% dari jumlah nozzle yang ada untuk SPBU Good, dari "
        "masing-masing produk diperiksa oleh Auditor secara acak)",
        ["A", "B", "C", "F"],
    ),
}

audit_data_rows = []

for code, (desc, options) in audit_points.items():
    st.markdown(
        f"""
        <div class="audit-card">
            <b>{code}</b> {desc}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Status & Catatan di Atas
    default_status_index = 0
    default_note = ""

    rc1, rc2 = st.columns([1, 3])
    with rc1:
        status_val = st.selectbox(
            f"Status {code}", 
            options, 
            index=default_status_index, 
            key=f"status_{code}", 
            label_visibility="collapsed"
        )
    with rc2:
        note_val = st.text_input(
            f"Catatan {code}",
            placeholder=f"Catatan / temuan untuk {code}...",
            key=f"note_{code}",
            label_visibility="collapsed",
        )

    # KONDISI 1: 2.2.f s.d. 2.2.l (FORM DENSITAS TUNGGAL)
    if code != "2.2.m":
        st.markdown(
            "<small style='color: #003366; font-weight: bold;'>Parameter Densitas (Input Asli):</small>",
            unsafe_allow_html=True,
        )

        dcol1, dcol2, dcol3, dcol4, dcol5, dcol6 = st.columns(6)

        with dcol1:
            val_tank = st.text_input("Tank No.", key=f"tank_{code}", placeholder="Tank No.", label_visibility="collapsed")
        with dcol2:
            val_ref_15 = st.text_input("Density@15 (Acuan)", key=f"ref_15_{code}", placeholder="Density@15 (Acuan)", label_visibility="collapsed")
        with dcol3:
            val_obs_temp = st.text_input("Obs. Temp. (°C)", key=f"temp_{code}", placeholder="Obs. Temp.", label_visibility="collapsed")
        with dcol4:
            val_obs_dens = st.text_input("Hasil Obs. Density", key=f"obs_dens_{code}", placeholder="Hasil Obs. Density", label_visibility="collapsed")
        with dcol5:
            val_actual = st.text_input("Aktual di Lapangan", key=f"act_{code}", placeholder="Aktual di Lapangan", label_visibility="collapsed")

        calc_dens_var = 0.0
        is_out_of_tolerance = False
        try:
            if val_actual and val_obs_dens:
                clean_act = val_actual.strip().replace(",", ".")
                clean_obs = val_obs_dens.strip().replace(",", ".")
                act_d = float(clean_act)
                obs_d = float(clean_obs)
                calc_dens_var = act_d - obs_d
                
                if abs(calc_dens_var) > 0.03:
                    is_out_of_tolerance = True
        except Exception:
            calc_dens_var = 0.0

        with dcol6:
            st.markdown(
                f"""
                <div style="background-color: #e9ecef; padding: 6px 10px; border-radius: 4px; border: 1px solid #ced4da; font-size: 13px; color: #333; text-align: center;">
                    <b>{calc_dens_var:.4f}</b><br><span style="font-size: 9px; color: #666;">Density Var.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if is_out_of_tolerance:
            if "F" in options:
                status_val = "F"
            if not note_val:
                note_val = "Densitas melebihi batas toleransi (+/- 0.03)"

        row_data = {
            "Kode": code,
            "Parameter / Item Audit": desc,
            "Status": status_val,
            "Catatan / Temuan": note_val,
            "Tank No.": val_tank,
            "Density@15 (Acuan)": val_ref_15,
            "Obs. Temp. (°C)": val_obs_temp,
            "Hasil Obs. Density": val_obs_dens,
            "Aktual di Lapangan": val_actual,
            "Density Var.": round(calc_dens_var, 4),
            "Nozzle No.": "-",
            "DU Make": "-",
            "DU Serial No.": "-",
            "Product": "-",
            "Preset/Manual Mode": "-",
            "Quantity Variation (ml)": "-",
            "file_obj": None
        }
        audit_data_rows.append(row_data)

        st.write("")
        file_val = st.file_uploader(
            f"Unggah Bukti ({code})",
            type=["png", "jpg", "jpeg", "mp4", "mov"],
            key=f"file_{code}",
        )
        if file_val is not None and "image" in file_val.type:
            st.image(file_val, caption=f"Bukti Foto {code}", width=250)
            row_data["file_obj"] = file_val

    else:
        # --- KONDISI 2: 2.2.m (MULTIPLE NOZZLE ROWS - BISA DITAMBAH SEBANYAK KEBUTUHAN) ---
        st.markdown(
            "<small style='color: #003366; font-weight: bold;'>Parameter Nozzle & Volume (Dapat Menambahkan Banyak Baris Nozzle):</small>",
            unsafe_allow_html=True,
        )

        # Inisialisasi State Session untuk menyimpan jumlah baris nozzle
        if "num_nozzles" not in st.session_state:
            st.session_state.num_nozzles = 3  # Default awal 3 baris

        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("➕ Tambah Baris Nozzle", key="add_nozzle_btn"):
                st.session_state.num_nozzles += 1
                st.rerun()
        with col_btn2:
            if st.button("➖ Kurangi Baris Terakhir", key="remove_nozzle_btn") and st.session_state.num_nozzles > 1:
                st.session_state.num_nozzles -= 1
                st.rerun()

        # Perulangan untuk setiap baris nozzle
        for i in range(st.session_state.num_nozzles):
            st.markdown(f"<div style='font-size: 11px; font-weight: bold; color: #555; margin-top: 5px;'>Nozzle #{i+1}</div>", unsafe_allow_html=True)
            mcol1, mcol2, mcol3, mcol4, mcol5, mcol6 = st.columns(6)

            with mcol1:
                val_nozzle = st.text_input("Nozzle No.", key=f"nozzle_{code}_{i}", placeholder="Nozzle No.", label_visibility="collapsed")
            with mcol2:
                val_du_make = st.text_input("DU Make", key=f"dumake_{code}_{i}", placeholder="DU Make", label_visibility="collapsed")
            with mcol3:
                val_du_serial = st.text_input("DU Serial No.", key=f"duserial_{code}_{i}", placeholder="DU Serial No.", label_visibility="collapsed")
            with mcol4:
                val_product = st.text_input("Product", key=f"prod_{code}_{i}", placeholder="Product", label_visibility="collapsed")
            with mcol5:
                val_mode = st.text_input("Preset/Manual Mode", key=f"mode_{code}_{i}", placeholder="Preset/Manual", label_visibility="collapsed")
            with mcol6:
                val_qty_var = st.text_input("Var. (ml) / 20000", key=f"qtyvar_{code}_{i}", placeholder="Var. (ml)", label_visibility="collapsed")

            is_volume_out = False
            try:
                if val_qty_var:
                    clean_qty = val_qty_var.strip().replace(",", ".")
                    qty_val = float(clean_qty)
                    if qty_val < -60:
                        is_volume_out = True
            except Exception:
                pass

            if is_volume_out and not note_val:
                note_val = f"Volume Nozzle {val_nozzle or (i+1)} melebihi batas toleransi (-60 ml)"

            # Upload Foto per baris nozzle
            file_val_nozzle = st.file_uploader(
                f"Unggah Bukti Nozzle #{i+1} (2.2.m)",
                type=["png", "jpg", "jpeg", "mp4", "mov"],
                key=f"file_{code}_{i}",
            )
            if file_val_nozzle is not None and "image" in file_val_nozzle.type:
                st.image(file_val_nozzle, caption=f"Bukti Foto Nozzle #{i+1}", width=200)

            row_data_nozzle = {
                "Kode": f"{code} (Nozzle #{i+1})",
                "Parameter / Item Audit": desc,
                "Status": status_val,
                "Catatan / Temuan": note_val,
                "Tank No.": "-",
                "Density@15 (Acuan)": "-",
                "Obs. Temp. (°C)": "-",
                "Hasil Obs. Density": "-",
                "Aktual di Lapangan": "-",
                "Density Var.": "-",
                "Nozzle No.": val_nozzle,
                "DU Make": val_du_make,
                "DU Serial No.": val_du_serial,
                "Product": val_product,
                "Preset/Manual Mode": val_mode,
                "Quantity Variation (ml)": val_qty_var,
                "file_obj": file_val_nozzle if (file_val_nozzle and "image" in file_val_nozzle.type) else None
            }
            audit_data_rows.append(row_data_nozzle)

    st.markdown("---")

# ---------------------------------------------------------
# FITUR UNDUH LAPORAN KESELURUHAN KE EXCEL
# ---------------------------------------------------------
st.markdown(
    '<div class="section-header">📥 Unduh Laporan Keseluruhan ke Excel</div>',
    unsafe_allow_html=True,
)

if st.button("📊 Generate & Download Laporan Excel", use_container_width=True):
    from openpyxl import Workbook
    from openpyxl.drawing.image import Image as OpenpyxlImage
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    wb = Workbook()
    ws = wb.active
    ws.title = "Audit_Parameter"

    ws.views.sheetView[0].showGridLines = True

    header_fill = PatternFill(start_color="003366", end_color="003366", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="D3D3D3"),
        right=Side(style="thin", color="D3D3D3"),
        top=Side(style="thin", color="D3D3D3"),
        bottom=Side(style="thin", color="D3D3D3"),
    )

    headers = [
        "Kode",
        "Parameter / Item Audit",
        "Status",
        "Catatan / Temuan",
        "Tank No.",
        "Density@15 (Acuan)",
        "Obs. Temp. (°C)",
        "Hasil Obs. Density",
        "Aktual di Lapangan",
        "Density Var.",
        "Nozzle No.",
        "DU Make",
        "DU Serial No.",
        "Product",
        "Preset/Manual Mode",
        "Quantity Variation (ml)",
        "Bukti Foto",
    ]
    ws.append(headers)
    ws.row_dimensions[1].height = 30

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = thin_border

    for idx, row in enumerate(audit_data_rows, start=2):
        ws.append(
            [
                row["Kode"],
                row["Parameter / Item Audit"],
                row["Status"],
                row["Catatan / Temuan"],
                row["Tank No."],
                row["Density@15 (Acuan)"],
                row["Obs. Temp. (°C)"],
                row["Hasil Obs. Density"],
                row["Aktual di Lapangan"],
                row["Density Var."],
                row["Nozzle No."],
                row["DU Make"],
                row["DU Serial No."],
                row["Product"],
                row["Preset/Manual Mode"],
                row["Quantity Variation (ml)"],
                "",
            ]
        )

        ws.row_dimensions[idx].height = 110

        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=idx, column=col_num)
            cell.border = thin_border
            cell.font = Font(name="Calibri", size=10)
            if col_num in [1, 3, 5, 6, 7, 8, 9, 10, 11, 15, 16]:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

        if row["file_obj"] is not None:
            try:
                img_bytes = io.BytesIO(row["file_obj"].getvalue())
                img = PILImage.open(img_bytes)

                img_buffer = io.BytesIO()
                img.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                xl_img = OpenpyxlImage(img_buffer)
                xl_img.width = 130
                xl_img.height = 100
                ws.add_image(xl_img, f"Q{idx}")
            except Exception:
                pass

    column_widths = {
        "A": 15, "B": 45, "C": 10, "D": 30, "E": 12, "F": 18, 
        "G": 15, "H": 18, "I": 18, "J": 15, "K": 12, "L": 15, 
        "M": 15, "N": 18, "O": 18, "P": 22, "Q": 22
    }
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    excel_io = io.BytesIO()
    wb.save(excel_io)
    excel_data = excel_io.getvalue()

    st.download_button(
        label="📥 Klik di Sini untuk Download File Excel Lengkap (.xlsx)",
        data=excel_data,
        file_name="Laporan_Audit_Parameter_SPBU_Professional.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.success("Laporan Excel profesional beserta foto bukti tersusun rapi!")
