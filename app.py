import io
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    page_icon="⛽",
    layout="wide",
)

# Custom CSS untuk styling kartu metrik & tab
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
    .metric-card {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
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


    def render_dashboard_tab(data_tab, nama_bbm, label_transaksi):
      if data_tab.empty:
        st.info(f"Tidak ada data transaksi untuk kategori {nama_bbm}.")
        return

      # Buat kolom dummy jika kolom opsional tidak ditemukan di file
      local_data = data_tab.copy()
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

      # Agregasi per Plat Nomor
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

      # Kalkulasi Nilai untuk Kartu Metrik (KPI)
      jumlah_plat_lewat_kuota = len(
          rekap_plat[rekap_plat["Status"] == "Perlu Diperiksa"]
      )
      jumlah_tanpa_nopol = len(
          local_data[
              local_data[plat_col].isna()
              | (local_data[plat_col].astype(str).str.strip() == "")
              | (local_data[plat_col].astype(str).str.upper() == "CASH")
          ]
      )
      jumlah_tak_cocok = 0
      jumlah_total_transaksi = len(local_data)
      jumlah_sangat_mencurigakan = len(
          rekap_plat[rekap_plat["Total_Volume"] > (rekap_plat["Batas_Kuota"] * 1.5)]
      )
      jumlah_perlu_diperiksa = jumlah_plat_lewat_kuota
      jumlah_normal = len(rekap_plat) - jumlah_perlu_diperiksa

      st.markdown("<br>", unsafe_allow_html=True)

      # Render Baris Kartu Metrik Atas (3 Kolom)
      m1, m2, m3 = st.columns(3)
      with m1:
        st.markdown(
            f"""<div class="metric-card">
            <span style="font-size:22px; font-weight:700; color:#1f2937;">⛽ {jumlah_plat_lewat_kuota}</span><br>
            <span style="font-size:12px; color:#6b7280;">Plat melewati kuota harian</span>
            </div>""",
            unsafe_allow_html=True,
        )
      with m2:
        st.markdown(
            f"""<div class="metric-card">
            <span style="font-size:22px; font-weight:700; color:#1f2937;">🚫 {jumlah_tanpa_nopol}</span><br>
            <span style="font-size:12px; color:#6b7280;">Transaksi subsidi tanpa nopol</span>
            </div>""",
            unsafe_allow_html=True,
        )
      with m3:
        st.markdown(
            f"""<div class="metric-card">
            <span style="font-size:22px; font-weight:700; color:#1f2937;">🔍 {jumlah_tak_cocok}</span><br>
            <span style="font-size:12px; color:#6b7280;">Angka plat tak cocok konsumsi (lead)</span>
            </div>""",
            unsafe_allow_html=True,
        )

      # Render Baris Kartu Metrik Bawah (4 Kolom)
      b1, b2, b3, b4 = st.columns(4)
      with b1:
        st.markdown(
            f"""<div class="metric-card">
            <span style="font-size:22px; font-weight:700; color:#1f2937;">{jumlah_total_transaksi}</span><br>
            <span style="font-size:12px; color:#6b7280;">Transaksi {label_transaksi}</span>
            </div>""",
            unsafe_allow_html=True,
        )
      with b2:
        st.markdown(
            f"""<div class="metric-card">
            <span style="font-size:22px; font-weight:700; color:#dc2626;">{jumlah_sangat_mencurigakan}</span><br>
            <span style="font-size:12px; color:#6b7280;">Sangat mencurigakan</span>
            </div>""",
            unsafe_allow_html=True,
        )
      with b3:
        st.markdown(
            f"""<div class="metric-card">
            <span style="font-size:22px; font-weight:700; color:#d97706;">{jumlah_perlu_diperiksa}</span><br>
            <span style="font-size:12px; color:#6b7280;">Perlu diperiksa</span>
            </div>""",
            unsafe_allow_html=True,
        )
      with b4:
        st.markdown(
            f"""<div class="metric-card">
            <span style="font-size:22px; font-weight:700; color:#059669;">{jumlah_normal}</span><br>
            <span style="font-size:12px; color:#6b7280;">Normal</span>
            </div>""",
            unsafe_allow_html=True,
        )

      st.markdown("<br>", unsafe_allow_html=True)

      # Tombol aksi & pencarian plat
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
        rekap_plat = rekap_plat[
            rekap_plat[plat_col].astype(str).str.contains(search_plat, case=False)
        ]

      st.markdown(f"#### Rekap per Plat (Harian) — {nama_bbm}")
      st.caption(
          "Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang"
          " lewat kuota di atas. Perkiraan jenis =, wajib dicek CCTV/SAMSAT."
      )

      # Urutkan agar yang lewat kuota tampil di atas
      rekap_plat = rekap_plat.sort_values(
          by="Status", ascending=False
      ).reset_index(drop=True)

      # Tampilkan baris rekap per plat
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

      # Bagian Bawah: Bukti CCTV & Detail Temuan (Dengan Fitur Kamera & Galeri Aktif)
      st.markdown("---")
      c_cctv, c_info = st.columns([1.2, 3.8])

      with c_cctv:
        st.markdown("**BUKTI CCTV / FOTO**")

        # Inisialisasi session_state untuk menyimpan foto terpilih
        if f"uploaded_photo_{nama_bbm}" not in st.session_state:
          st.session_state[f"uploaded_photo_{nama_bbm}"] = None

        # Tombol Kamera (Menggunakan st.camera_input untuk langsung ambil foto via HP/Laptop)
        img_camera = st.camera_input("📷 Ambil dari Kamera", key=f"cam_{nama_bbm}")
        if img_camera is not None:
          st.session_state[f"uploaded_photo_{nama_bbm}"] = img_camera

        # Tombol Galeri (Menggunakan st.file_uploader untuk upload foto dari HP/Laptop)
        img_gallery = st.file_uploader(
            "📁 Ambil dari Galeri",
            type=["jpg", "jpeg", "png"],
            key=f"gal_{nama_bbm}",
        )
        if img_gallery is not None:
          st.session_state[f"uploaded_photo_{nama_bbm}"] = img_gallery

        # Tampilkan hasil foto yang telah dipilih/diambil
        current_photo = st.session_state[f"uploaded_photo_{nama_bbm}"]
        if current_photo is not None:
          st.success("Foto berhasil dilampirkan!")
          st.image(current_photo, caption="Pratinjau Bukti Foto", use_column_width=True)

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
      render_dashboard_tab(df_jbt, "Solar / JBT", "JBT")

    with tab_jbkp:
      render_dashboard_tab(df_jbkp, "Pertalite / JBKP", "JBKP")

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
