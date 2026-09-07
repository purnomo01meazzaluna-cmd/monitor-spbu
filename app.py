import io
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    page_icon="⛽",
    layout="wide",
)

# Custom CSS untuk merapikan tampilan
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
    </style>
""",
    unsafe_allow_html=True,
)

# Header Sederhana
st.markdown("### 📊 MONITORING · DATA H-1 (KEMARIN)")
st.markdown("## ⛽ Monitor Subsidi Tepat Guna")
st.markdown("---")

# Sidebar Pengaturan
with st.sidebar:
  st.header("⚙️ Pengaturan Batas Kuota")
  limit_mobil_penumpang = st.number_input(
      "Batas Kuota Mobil Penumpang (Liter)", value=50, min_value=10, max_value=200
  )
  limit_mobil_barang = st.number_input(
      "Batas Kuota Mobil Barang (Liter)", value=80, min_value=10, max_value=300
  )
  limit_bus = st.number_input(
      "Batas Kuota Bus (Liter)", value=200, min_value=50, max_value=500
  )

# Area Unggah File
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

    # Filter produk Subsidi
    df_subsidi = df[
        df["Clean_Product"].str.contains("SOLAR|PERTALITE|JBT|JBKP|BIO", na=False)
    ].copy()

    # Pisahkan tab JBT (Solar) dan JBKP (Pertalite)
    df_jbt = df_subsidi[
        df_subsidi["Clean_Product"].str.contains("SOLAR|JBT|BIO", na=False)
    ]
    df_jbkp = df_subsidi[
        df_subsidi["Clean_Product"].str.contains("PERTALITE|JBKP", na=False)
    ]

    tab_jbt, tab_jbkp = st.tabs(
        [f"JBT - Solar ({len(df_jbt)})", f"JBKP - Pertalite ({len(df_jbkp)})"]
    )


    def render_dashboard_tab(data_tab, nama_bbm):
      if data_tab.empty:
        st.info(f"Tidak ada data transaksi untuk kategori {nama_bbm}.")
        return

      # Tombol aksi atas
      col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
      with col_f1:
        search_plat = st.text_input(
            "Cari plat nomor...", key=f"search_{nama_bbm}"
        )
      with col_f2:
        st.write("")
        if st.button("Analisis ulang", key=f"btn_analisis_{nama_bbm}"):
          st.rerun()
      with col_f3:
        st.write("")
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
          data_tab.to_excel(writer, index=False, sheet_name="Data")
        st.download_button(
            "Unduh tindak lanjut (Excel)",
            data=output_excel.getvalue(),
            file_name=f"tindak_lanjut_{nama_bbm}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{nama_bbm}",
        )
      with col_f4:
        st.write("")
        st.button("Unduh transaksi + foto (Excel)", key=f"dl_foto_{nama_bbm}")

      if search_plat:
        data_tab = data_tab[
            data_tab[plat_col].astype(str).str.contains(search_plat, case=False)
        ]

      st.markdown(f"#### Rekap per Plat (Harian) — {nama_bbm}")
      st.caption(
          "Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang"
          " lewat kuota di atas. Perkiraan jenis =, wajib dicek CCTV/SAMSAT."
      )

      # Buat kolom dummy jika kolom opsional tidak ditemukan di file
      local_data = data_tab.copy()
      non_existent_id = False
      non_existent_time = False

      if not id_col or id_col not in local_data.columns:
        local_data["Dummy_ID"] = "N/A"
        active_id_col = "Dummy_ID"
      else:
        active_id_col = id_col

      if not time_col or time_col not in local_data.columns:
        local_data["Dummy_Time"] = "N/A"
        active_time_col = "Dummy_Time"
      else:
        active_time_col = time_col

      # Agregasi per Plat Nomor menggunakan format tuple Pandas agg (kolom, fungsi)
      rekap_plat = (
          local_data.groupby(plat_col)
          .agg(
              Total_Volume=(vol_col, "sum"),
              Frekuensi=(vol_col, "count"),
              Contoh_ID=(active_id_col, "first"),
              Contoh_Waktu=(active_time_col, "first"),
              Contoh_Product=(prod_col, "first"),
          )
          .reset_index()
      )


      # Logika Sederhana Estimasi Jenis Kendaraan berdasarkan Plat / Pola Volume
      def estimasi_jenis(row):
        plat_str = str(row[plat_col]).upper()
        if "BUS" in plat_str or row["Total_Volume"] > 120:
          return "≈ Bus", limit_bus
        elif row["Total_Volume"] > 60:
          return "≈ Mobil barang", limit_mobil_barang
        else:
          return "≈ Mobil penumpang", limit_mobil_penumpang

      rekap_plat[["Perkiraan Jenis", "Batas_Kuota"]] = rekap_plat.apply(
          lambda r: pd.Series(estimasi_jenis(r)), axis=1
      )
      rekap_plat["Status"] = rekap_plat.apply(
          lambda r: (
              "Perlu Diperiksa"
              if r["Total_Volume"] > r["Batas_Kuota"]
              else "Normal"
          ),
          axis=1,
      )

      # Urutkan agar yang lewat kuota (Perlu Diperiksa) tampil di atas
      rekap_plat = rekap_plat.sort_values(
          by="Status", ascending=False
      ).reset_index(drop=True)

      # Tampilkan baris rekap per plat mirip tabel di gambar
      for idx, row in rekap_plat.iterrows():
        p_plat = row[plat_col]
        p_jenis = row["Perkiraan Jenis"]
        p_freq = int(row["Frekuensi"])
        p_vol = row["Total_Volume"]
        p_kuota = int(row["Batas_Kuota"])
        p_status = row["Status"]

        pct = min(int((p_vol / p_kuota) * 100), 100)

        cols = st.columns([1.2, 1.8, 0.8, 2.5, 1.2])
        with cols[0]:
          st.markdown(f"**{p_plat}**")
        with cols[1]:
          st.markdown(f"{p_jenis} `ESTIMASI PLAT`")
        with cols[2]:
          st.markdown(f"{p_freq}×")
        with cols[3]:
          st.progress(pct / 100)
          st.caption(f"{p_vol:.1f} L / {p_kuota} L (batas terlonggar) · {pct}%")
        with cols[4]:
          if p_status == "Perlu Diperiksa":
            st.markdown(
                "<span"
                " style='background-color:#fef3c7;color:#d97706;padding:4px"
                " 10px;border-radius:12px;font-size:12px;font-weight:600;'>🟠"
                " Perlu Diperiksa</span>",
                unsafe_allow_html=True,
            )
          else:
            st.markdown(
                "<span"
                " style='background-color:#d1fae5;color:#059669;padding:4px"
                " 10px;border-radius:12px;font-size:12px;font-weight:600;'>🟢"
                " Normal</span>",
                unsafe_allow_html=True,
            )
        st.markdown("<hr style='margin:5px 0;opacity:0.3;'>", unsafe_allow_html=True)

      # Bagian Bawah: Bukti CCTV & Detail Temuan
      st.markdown("---")
      c_cctv, c_info = st.columns([1, 4])
      with c_cctv:
        st.markdown("**BUKTI CCTV**")
        st.button("📷 Kamera", key=f"cam_{nama_bbm}")
        st.button("📁 Galeri", key=f"gal_{nama_bbm}")

      anomali_rows = rekap_plat[rekap_plat["Status"] == "Perlu Diperiksa"]
      if not anomali_rows.empty:
        sample_anomali = anomali_rows.iloc[0]
        with c_info:
          ic1, ic2, ic3, ic4, ic5, ic6 = st.columns([1, 1, 1.2, 1, 1, 2])
          with ic1:
            st.markdown("**ID**")
            st.write(str(sample_anomali["Contoh_ID"]))
          with ic2:
            st.markdown("**WAKTU**")
            st.write(str(sample_anomali["Contoh_Waktu"]))
          with ic3:
            st.markdown("**PRODUCT / NOZZLE**")
            st.write(str(sample_anomali["Contoh_Product"]))
          with ic4:
            st.markdown("**PLAT**")
            st.write(str(sample_anomali[plat_col]))
          with ic5:
            st.markdown("**VOLUME**")
            st.write(f"{sample_anomali['Total_Volume']:.2f}L")
          with ic6:
            st.markdown("**ALASAN TEMUAN**")
            st.error(
                f"Total harian {sample_anomali['Total_Volume']:.1f}L > jatah"
                f" mobil pribadi ({sample_anomali['Batas_Kuota']}L) —"
                " konfirmasi jenis"
            )
      else:
        with c_info:
          st.info(
              "Tidak ada temuan anomali menonjol yang memerlukan verifikasi"
              " CCTV mendesak pada tab ini."
          )

    with tab_jbt:
      render_dashboard_tab(df_jbt, "Solar / JBT")

    with tab_jbkp:
      render_dashboard_tab(df_jbkp, "Pertalite / JBKP")

  except Exception as e:
    st.error(
        f"Gagal membaca format file. Pastikan struktur kolom sesuai. Detail:"
        f" {e}"
    )

else:
  st.info(
      "Silakan unggah file laporan transaksi Anda pada area unggah di atas"
      " untuk memuat dashboard interaktif."
  )
