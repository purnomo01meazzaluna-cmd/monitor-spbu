import io
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    page_icon="⛽",
    layout="wide",
)

# Custom CSS untuk merapikan tampilan & tombol di HP
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
    /* Memperkecil padding tombol agar pas di layar HP */
    .stButton button {
        width: 100%;
        font-size: 13px !important;
        padding: 6px 10px !important;
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

      # Tombol aksi atas dengan label yang lebih ringkas agar tidak terpotong di HP
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
          data_tab.to_excel(writer, index=False, sheet_name="Data")
        st.download_button(
            "📥 Unduh Excel",
            data=output_excel.getvalue(),
            file_name=f"tindak_lanjut_{nama_bbm}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{nama_bbm}",
        )
      with col_f4:
        st.write("")
        st.button("📸 Unduh + Foto", key=f"dl_foto_{nama_bbm}")

      if search_plat:
        data_tab = data_tab[
            data_tab[plat_col].astype(str).str.contains(search_plat, case=False)
        ]

      st.markdown(f"#### Rekap per Plat (Harian) — {nama_bbm}")
      st.caption(
          "Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang"
          " lewat kuota di atas."
      )

      # Agregasi per Plat Nomor secara aman
      agg_dict = {
          "Total_Volume": (vol_col, "sum"),
          "Frekuensi": (vol_col, "count"),
      }

      if id_col and id_col in data_tab.columns:
        agg_dict["Contoh_ID"] = (
            id_col,
            lambda x: x.iloc[0] if not x.empty else "N/A",
        )
      else:
        data_tab["Temp_ID"] = "N/A"
        agg_dict["Contoh_ID"] = ("Temp_ID", lambda x: "N/A")

      if time_col and time_col in data_tab.columns:
        agg_dict["Contoh_Waktu"] = (
            time_col,
            lambda x: x.iloc[0] if not x.empty else "N/A",
        )
      else:
        data_tab["Temp_Time"] = "N/A"
        agg_dict["Contoh_Waktu"] = ("Temp_Time", lambda x: "N/A")

      if prod_col and prod_col in data_tab.columns:
        agg_dict["Contoh_Product"] = (
            prod_col,
            lambda x: x.iloc[0] if not x.empty else "N/A",
        )
      else:
        data_tab["Temp_Prod"] = "N/A"
        agg_dict["Contoh_Product"] = ("Temp_Prod", lambda x: "N/A")

      rekap_plat = data_tab.groupby(plat_col).agg(**agg_dict).reset_index()

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
          st.markdown(f"{p_jenis}")
        with cols[2]:
          st.markdown(f"{p_freq}×")
        with cols[3]:
          st.progress(pct / 100)
          st.caption(f"{p_vol:.1f}L / {p_kuota}L · {pct}%")
        with cols[4]:
          if p_status == "Perlu Diperiksa":
            st.markdown(
                "<span"
                " style='background-color:#fef3c7;color:#d97706;padding:4px"
                " 8px;border-radius:10px;font-size:11px;font-weight:600;'>🟠"
                " Cek</span>",
                unsafe_allow_html=True,
            )
          else:
            st.markdown(
                "<span"
                " style='background-color:#d1fae5;color:#059669;padding:4px"
                " 8px;border-radius:10px;font-size:11px;font-weight:600;'>🟢"
                " Aman</span>",
                unsafe_allow_html=True,
            )
        st.markdown(
            "<hr style='margin:5px 0;opacity:0.3;'>", unsafe_allow_html=True
        )

      # Bagian Bawah: Kamera HP & Galeri File Terpusat
      st.markdown("---")
      st.markdown("**📷 LAMPIRAN BUKTI CCTV / FOTO LAPANGAN**")

      if f"foto_bukti_{nama_bbm}" not in st.session_state:
        st.session_state[f"foto_bukti_{nama_bbm}"] = {}

      anomali_rows = rekap_plat[rekap_plat["Status"] == "Perlu Diperiksa"]

      if not anomali_rows.empty:
        # Pilih plat nomor yang ingin diberi foto jika ada beberapa temuan
        list_plat_anomali = anomali_rows[plat_col].tolist()
        pilih_plat = st.selectbox(
            "Pilih Plat Nomor Kendaraan yang akan dilampirkan foto:",
            list_plat_anomali,
            key=f"select_plat_{nama_bbm}",
        )

        c_cam, c_prev = st.columns(2)
        with c_cam:
          opsi_sumber = st.radio(
              "Ambil dari:",
              ["Kamera HP", "Galeri HP/Laptop"],
              key=f"sumber_{nama_bbm}",
              horizontal=True,
          )

          uploaded_image = None
          if opsi_sumber == "Kamera HP":
            uploaded_image = st.camera_input(
                "Nyalakan Kamera", key=f"cam_input_{nama_bbm}"
            )
          else:
            uploaded_image = st.file_uploader(
                "Pilih File Foto",
                type=["jpg", "jpeg", "png"],
                key=f"gal_input_{nama_bbm}",
            )

          if uploaded_image is not None:
            st.session_state[f"foto_bukti_{nama_bbm}"][pilih_plat] = (
                uploaded_image
            )
            st.success(f"Foto untuk plat {pilih_plat} berhasil disimpan!")

        with c_prev:
          st.markdown(f"**Preview Bukti untuk: {pilih_plat}**")
          if pilih_plat in st.session_state[f"foto_bukti_{nama_bbm}"]:
            st.image(
                st.session_state[f"foto_bukti_{nama_bbm}"][pilih_plat],
                width=220,
                caption=f"Bukti CCTV - {pilih_plat}",
            )
          else:
            st.info("Belum ada foto yang diunggah untuk plat ini.")

        # Tampilkan detail transaksi anomali pertama
        sample_anomali = anomali_rows[
            anomali_rows[plat_col] == pilih_plat
        ].iloc[0]
        st.warning(
            f"⚠️ **Perhatian:** Total pengisian {sample_anomali['Total_Volume']:.1f}L"
            f" melebihi batas kuota untuk {sample_anomali['Perkiraan Jenis']}."
            " Mohon verifikasi melalui CCTV/SAMSAT."
        )
      else:
        st.info(
            "Tidak ada temuan anomali yang memerlukan verifikasi foto pada"
            " tab ini."
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
    
