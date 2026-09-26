import io
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import streamlit as st

# --- HALAMAN KONFIGURASI ---
st.set_page_config(
    page_title="Simulasi Audit Pertamina Way",
    page_icon="⛽",
    layout="wide",
)

# --- DATA CHECKLIST PERTAMINA WAY ---
# Format item: (Kode, Pertanyaan, Opsi Valid, Bobot, Label Alert / None)
CHECKLIST_DATA = {
    "1. ASPEK KESELAMATAN & LINGKUNGAN (HSSE)": {
        "1.1 Keselamatan Kerja & Prosedur Operasi": {
            "1.1.1 Area Pompa (Dispenser)": [
                (
                    "1.1.1.a",
                    (
                        "Operator mematikan mesin kendaraan dan melarang"
                        " penggunaan handphone (HP) saat pengisian BBM."
                    ),
                    ["A", "B", "C", "F"],
                    1.5,
                    "HP",
                ),
                (
                    "1.1.1.b",
                    (
                        "Operator memastikan posisi Nozzle sudah pas dan tidak"
                        " ada tumpahan saat pengisian."
                    ),
                    ["A", "B", "C", "F"],
                    1.5,
                    None,
                ),
                (
                    "1.1.1.c",
                    (
                        "Tersedia alat pemadam api ringan (APAR) yang siap pakai"
                        " dan mudah dijangkau di dekat pulau pompa."
                    ),
                    ["A", "B", "C", "F"],
                    2.0,
                    "APAR",
                ),
            ],
            "1.1.2 Prosedur Penerimaan BBM (Bongkar BBM)": [
                (
                    "1.1.2.a",
                    (
                        "Pemeriksaan tera dan densitas BBM dilakukan bersama"
                        " pengawas sebelum bongkar."
                    ),
                    ["A", "B", "C", "F"],
                    2.5,
                    "TARA",
                ),
                (
                    "1.1.2.b",
                    (
                        "Grounding/kabel arde terpasang sempurna pada mobil"
                        " tangki sebelum proses bongkar dimulai."
                    ),
                    ["A", "B", "C", "F"],
                    2.5,
                    "GROUNDING",
                ),
            ],
        }
    },
    "2. ASPEK PELAYANAN & KEPUASAN PELANGGAN": {
        "2.1 Standar Layanan (3S & Pengecekan Nol)": {
            "2.1.1 Keramahan & Kejujuran Operator": [
                (
                    "2.1.1.a",
                    (
                        "Operator menyambut konsumen dengan salam, senyum, dan"
                        " sapa (3S)."
                    ),
                    ["A", "B", "C", "F"],
                    1.5,
                    None,
                ),
                (
                    "2.1.1.b",
                    (
                        "Operator menunjuk layar dispenser menunjuk angka NOL"
                        " (0.00) sebelum pengisian dimulai."
                    ),
                    ["A", "B", "C", "F"],
                    2.0,
                    "NOL",
                ),
            ]
        }
    },
}

# Mapping Nilai Huruf ke Pengali Bobot
WEIGHT_MAP = {"A": 1.0, "B": 0.75, "C": 0.5, "F": 0.0}


def parse_item(raw_item):
  """Mengekstrak tuple item checklist."""
  return (
      raw_item[0],
      raw_item[1],
      raw_item[2],
      float(raw_item[3]),
      raw_item[4] if len(raw_item) > 4 else None,
  )


def check_is_valid_option(opt, valid_opts):
  return opt in valid_opts


# --- HEADER UTAMA APLIKASI ---
st.title("⛽ SIMULASI AUDIT SPBU - PERTAMINA WAY")
st.markdown(
    "Aplikasi web interaktif untuk audit mandiri operasional SPBU. Pastikan"
    " seluruh item penalty/kritis terpantau dengan baik."
)
st.divider()

# --- INFORMASI SPBU ---
col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
  nomor_spbu = st.text_input("Nomor SPBU", value="4150201")
with col_info2:
  nama_spbu = st.text_input("Lokasi / Nama SPBU", value="Semarang")
with col_info3:
  nama_auditor = st.text_input("Nama Auditor", value="Tim HSSE & Retail")

st.markdown("---")

# Inisialisasi Session State untuk menyimpan jawaban
if "answers" not in st.session_state:
  st.session_state.answers = {}

# --- RENDER FORM CHECKLIST & PERHITUNGAN ---
has_critical_failure = False
failed_alert_names = []
total_achieved_score = 0.00
total_max_score = 0.00

for elemen_name, sub_elements in CHECKLIST_DATA.items():
  st.header(elemen_name)
  for sub_name, items_dict in sub_elements.items():
    st.subheader(sub_name)

    items_to_loop = []
    if isinstance(items_dict, dict):
      for group_name, item_list in items_dict.items():
        st.markdown(f"**{group_name}**")
        items_to_loop = item_list
        for raw_item in items_to_loop:
          code, question, valid_options, weight, alert_label = parse_item(
              raw_item
          )
          total_max_score += weight

          # Label tampilan untuk item yang punya alert khusus
          alert_badge = (
              f" 🔥 **[Alert: {alert_label}]**" if alert_label else ""
          )
          display_label = f"**{code}** - {question}{alert_badge} *(Bobot: {weight})*"

          # Opsi pilihan radio
          current_val = st.session_state.answers.get(code, "A")
          selected_opt = st.radio(
              display_label,
              options=valid_options,
              index=(
                  valid_options.index(current_val)
                  if current_val in valid_options
                  else 0
              ),
              key=f"radio_{code}",
          )
          st.session_state.answers[code] = selected_opt

          # Hitung skor tercapai
          multiplier = WEIGHT_MAP.get(selected_opt, 0.00)
          total_achieved_score += multiplier * weight

          # Pengecekan Item Penalty (Hanya item tertentu dengan alert_label yang jika bernilai F memicu kegagalan total)
          if (
              alert_label
              and selected_opt
              and selected_opt.startswith("F")
              and alert_label in ["HP", "APAR", "TARA", "GROUNDING", "NOL"]
          ):
            has_critical_failure = True
            failed_alert_names.append(f"{code} ({alert_label})")
        st.markdown("")
    st.markdown("---")

total_max_score = round(total_max_score, 2)
total_achieved_score = round(total_achieved_score, 2)
score_percentage = (
    (total_achieved_score / total_max_score * 100)
    if total_max_score > 0
    else 0.0
)

# --- DASHBOARD HASIL & STATUS DI ATAS ---
st.markdown("### 📊 Ringkasan Hasil Audit")
m1, m2, m3 = st.columns(3)
m1.metric("Total Score", f"{total_achieved_score:.2f} / {total_max_score:.2f}")
m2.metric("Pencapaian (%)", f"{score_percentage:.1f}%")

if has_critical_failure:
  m3.error("STATUS: NOT CERTIFIED 🚨")
  alert_list_str = ", ".join(failed_alert_names)
  st.error(
      f"🚨 **STATUS AUDIT: GAGAL (NOT CERTIFIED)** — Ditemukan pelanggaran"
      f" pada item penalty/kritis tertentu: **[{alert_list_str}]**! Meskipun"
      " skor tinggi, adanya item penalty ber-nilai 'F' menggagalkan seluruh"
      " kelulusan audit."
  )
else:
  m3.success("STATUS: CERTIFIED ✅")
  st.success(
      "✅ **STATUS AUDIT: CERTIFIED** — Seluruh item penalty dan standar"
      " terpenuhi."
  )


# --- FUNGSI GENERATE EXCEL ---
def generate_full_excel():
  wb = openpyxl.Workbook()
  ws = wb.active
  ws.title = "Laporan Audit"

  # Styling standar
  primary_fill = PatternFill(
      start_color="1F4E78", end_color="1F4E78", fill_type="solid"
  )
  white_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
  bold_font = Font(name="Arial", size=10, bold=True)
  normal_font = Font(name="Arial", size=10)
  thin_border = Border(
      left=Side(style="thin", color="CCCCCC"),
      right=Side(style="thin", color="CCCCCC"),
      top=Side(style="thin", color="CCCCCC"),
      bottom=Side(style="thin", color="CCCCCC"),
  )

  # Judul Laporan
  ws["A1"] = "LAPORAN RESMI SIMULASI AUDIT SPBU - PERTAMINA WAY"
  ws["A1"].font = Font(name="Arial", size=14, bold=True, color="1F4E78")
  ws.append([])

  ws.append(["Nomor SPBU", nomor_spbu])
  ws.append(["Lokasi / Nama", nama_spbu])
  ws.append(["Auditor", nama_auditor])
  ws.append([
      "Status Akhir",
      "NOT CERTIFIED (GAGAL PENALTY)" if has_critical_failure else "CERTIFIED",
  ])
  ws.append([])

  # Header Tabel
  headers = [
      "Kode",
      "Pertanyaan / Item Audit",
      "Label Alert",
      "Bobot",
      "Pilihan",
      "Nilai Didapat",
  ]
  ws.append(headers)
  for col_num in range(1, len(headers) + 1):
    cell = ws.cell(row=ws.max_row, column=col_num)
    cell.fill = primary_fill
    cell.font = white_font
    cell.alignment = Alignment(horizontal="center", vertical="center")

  # Masukkan Data Checklist ke Excel
  for elemen_name, sub_elements in CHECKLIST_DATA.items():
    ws.append([elemen_name, "", "", "", "", ""])
    ws.cell(row=ws.max_row, column=1).font = bold_font

    for sub_name, items_dict in sub_elements.items():
      ws.append([f"  {sub_name}", "", "", "", "", ""])
      ws.cell(row=ws.max_row, column=1).font = bold_font

      items_to_loop = []
      if isinstance(items_dict, dict):
        for group_name, item_list in items_dict.items():
          items_to_loop = item_list
          for raw_item in items_to_loop:
            code, question, valid_options, weight, alert_label = parse_item(
                raw_item
            )
            selected_opt = st.session_state.answers.get(code, "A")
            mult = WEIGHT_MAP.get(selected_opt, 0.0)
            score_got = mult * weight

            row_data = [
                code,
                question,
                alert_label if alert_label else "-",
                weight,
                selected_opt,
                round(score_got, 2),
            ]
            ws.append(row_data)

            # Border sel tabel
            for c_idx in range(1, 7):
              cell = ws.cell(row=ws.max_row, column=c_idx)
              cell.font = normal_font
              cell.border = thin_border

  # Lebar kolom otomatis
  col_widths = {"A": 12, "B": 45, "C": 15, "D": 10, "E": 10, "F": 15}
  for col, width in col_widths.items():
    ws.column_dimensions[col].width = width

  output = io.BytesIO()
  wb.save(output)
  output.seek(0)
  return output


# --- BAGIAN DOWNLOAD EXCEL ---
st.subheader("📥 Unduh Laporan Excel")
excel_data = generate_full_excel()
st.download_button(
    label="Download Laporan Audit Lengkap (.xlsx)",
    data=excel_data,
    file_name=f"Laporan_Audit_SPBU_{nomor_spbu}.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
    use_container_width=True,
)
