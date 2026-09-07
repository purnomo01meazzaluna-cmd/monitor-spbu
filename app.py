import io
import os
from PIL import Image as PILImage
from fpdf import FPDF
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    page_icon="⛽",
    layout="wide",
)


# Fungsi dummy untuk identifikasi jenis kendaraan dan kuota (sesuaikan jika ada fungsi aslinya)
def identifikasi_jenis_dan_kuota_dari_plat(plat, nama_bbm):
  # Contoh logika sederhana
  return "Mobil Pribadi", 60.0


# Inisialisasi state jika belum ada (Simulasi variabel global untuk contoh struktur)
if "foto_dict_Pertalite" not in st.session_state:
  st.session_state["foto_dict_Pertalite"] = {}
if "noted_dict_Pertalite" not in st.session_state:
  st.session_state["noted_dict_Pertalite"] = {}

# Contoh DataFrame dummy untuk pengujian
if "df_transaksi" not in st.session_state:
  st.session_state["df_transaksi"] = pd.DataFrame({
      "ID_Trx": ["TX001", "TX002"],
      "Waktu": ["2026-06-07 10:00:00", "2026-06-07 11:30:00"],
      "Produk": ["Pertalite", "Pertalite"],
      "Plat_Nomor": ["H1234AB", "H5678CD"],
      "Volume": [20.0, 45.0],
  })

nama_bbm = "Pertalite"
data_tab = st.session_state["df_transaksi"]
plat_tab_totals = {"H1234AB": 20.0, "H5678CD": 45.0}

id_col = "ID_Trx"
time_col = "Waktu"
prod_col = "Produk"
plat_col = "Plat_Nomor"
vol_col = "Volume"

st.title("Dashboard Monitor Subsidi Tepat Guna - SPBU 4150201 Semarang")

col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 3])

with col_f4:
  st.write("")
  if data_tab.empty:
    st.button(
        "Unduh transaksi + foto (PDF)",
        key=f"dl_foto_empty_{nama_bbm}",
        disabled=True,
    )
  else:

    class PDFReport(FPDF):

      def header(self):
        self.set_font("Arial", "B", 11)
        self.cell(
            0,
            8,
            f"Laporan Transaksi & Bukti CCTV - {nama_bbm}",
            0,
            1,
            "C",
        )
        self.ln(2)

      def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "I", 8)
        self.cell(
            0,
            10,
            f"Halaman {self.page_no()}",
            0,
            0,
            "C",
        )

    pdf = PDFReport(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "", 7)

    headers = [
        "Foto CCTV",
        "ID",
        "Waktu",
        "Produk/Nozzle",
        "Plat",
        "Volume",
        "Jenis Kendaraan",
        "Status",
        "Alasan",
        "Noted",
    ]
    # Total lebar tabel pas di kertas A4 Landscape (277 mm)
    col_widths = [22, 14, 24, 28, 22, 14, 28, 24, 61, 40]

    pdf.set_font("Arial", "B", 7)
    for i, h in enumerate(headers):
      pdf.cell(col_widths[i], 7, h, 1, 0, "C")
    pdf.ln()

    pdf.set_font("Arial", "", 7)
    foto_dict = st.session_state[f"foto_dict_{nama_bbm}"]
    noted_dict = st.session_state[f"noted_dict_{nama_bbm}"]

    for idx, row in data_tab.iterrows():
      trx_id = (
          str(row[id_col]) if id_col and id_col in data_tab.columns else "N/A"
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
          float(row[vol_col]) if vol_col and vol_col in data_tab.columns else 0.0
      )

      total_vol_plat = plat_tab_totals.get(trx_plat, trx_vol)
      jenis_kendaran, batas_val = identifikasi_jenis_dan_kuota_dari_plat(
          trx_plat, nama_bbm
      )

      if trx_plat in ["N/A", "-", ""]:
        st_val = "Perlu Diperiksa"
        alasan_val = "Subsidi tanpa nopol"
      elif total_vol_plat > batas_val:
        st_val = "Perlu Diperiksa"
        alasan_val = f"Total > jatah ({batas_val}L)"
      else:
        st_val = "Normal"
        alasan_val = "Normal"

      noted_val = noted_dict.get(idx, "")

      # Tinggi baris tabel disesuaikan agar cukup untuk menampung gambar CCTV
      row_h = 18

      # Cek apakah ada foto untuk baris ini
      f_key = f"foto_trx_{nama_bbm}_{idx}"
      has_foto = f_key in foto_dict and foto_dict[f_key] is not None

      # Simpan posisi koordinat awal baris
      x_pos = pdf.get_x()
      y_pos = pdf.get_y()

      # 1. Cetak kolom pertama (Kotak Kosong untuk Gambar)
      pdf.cell(col_widths[0], row_h, "", 1, 0, "C")
      # Cetak sisa kolom data teks
      pdf.cell(col_widths[1], row_h, str(trx_id), 1, 0, "C")
      pdf.cell(col_widths[2], row_h, str(trx_time), 1, 0, "C")
      pdf.cell(col_widths[3], row_h, str(trx_prod)[:16], 1, 0, "L")
      pdf.cell(col_widths[4], row_h, str(trx_plat), 1, 0, "C")
      pdf.cell(col_widths[5], row_h, f"{trx_vol:.1f}L", 1, 0, "C")
      pdf.cell(col_widths[6], row_h, str(jenis_kendaran)[:16], 1, 0, "L")
      pdf.cell(col_widths[7], row_h, str(st_val), 1, 0, "C")
      pdf.cell(col_widths[8], row_h, str(alasan_val)[:35], 1, 0, "L")
      pdf.cell(col_widths[9], row_h, str(noted_val)[:22], 1, 1, "L")

      # 2. Jika ada foto, sisipkan gambar persis di dalam kotak kolom pertama
      if has_foto:
        try:
          img_file = foto_dict[f_key]
          pil_img = PILImage.open(img_file)
          temp_img_path = f"temp_pdf_{nama_bbm}_{idx}.jpg"
          # Konversi ke RGB untuk memastikan kompatibilitas format JPEG
          if pil_img.mode in ("RGBA", "P"):
            pil_img = pil_img.convert("RGB")
          pil_img.save(temp_img_path, "JPEG")

          # Masukkan gambar pas di dalam sel kolom pertama
          pdf.image(
              temp_img_path,
              x=x_pos + 1,
              y=y_pos + 1,
              w=col_widths[0] - 2,
              h=row_h - 2,
          )

          if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
        except Exception:
          pass

    pdf_output_bytes = pdf.output(dest="S").encode("latin1")

    st.download_button(
        "Unduh transaksi + foto (PDF)",
        data=pdf_output_bytes,
        file_name=f"laporan_transaksi_dan_foto_{nama_bbm}.pdf",
        mime="application/pdf",
        key=f"dl_foto_pdf_{nama_bbm}",
    )
