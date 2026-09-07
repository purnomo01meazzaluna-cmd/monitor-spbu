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
    .stButton button {
        width: 100%;
        font-size: 11px !important;
        padding: 4px 6px !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Header Sederhana
st.markdown("### 📊 MONITORING · DATA H-1 (KEMARIN)")
st.markdown("## ⛽ Monitor Subsidi Tepat Guna")
st.markdown("---")

# Sidebar Pengaturan Batas Kuota
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

    # Membersihkan awalan "Cash" pada kolom plat agar nomor polisi bersih (misal: "Cash H1460UW" -> "H1460UW")
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

    # --- KOTAK INFO SESUAI PERMINTAAN ---
    st.markdown(
        """
        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #f59e0b; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; color: #334155;">
        Sesuaikan batasan kuota sesuai dengan identifikasi anda di menu sebelah kiri.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Hitung metrik global keseluruhan untuk kartu di atas
    total_trx = len(df_subsidi)
    plat_all_totals = (
        df_subsidi.groupby(plat_col)[vol_col].sum().to_dict()
        if plat_col and vol_col
        else {}
    )

    count_plat_over = 0
    count_no_nopol = 0
    count_perlu_diperiksa = 0
    count_normal = 0

    for _, row in df_subsidi.iterrows():
      p = str(row[plat_col]) if plat_col in df_subsidi.columns else "N/A"
      v = float(row[vol_col]) if vol_col in df_subsidi.columns else 0.0
      tot_v = plat_all_totals.get(p, v)

      if "BUS" in p.upper() or tot_v > 120:
        b_val = limit_bus
      elif tot_v > 60:
        b_val = limit_mobil_barang
      else:
        b_val = limit_mobil_penumpang

      if p in ["N/A", "-", ""]:
        count_no_nopol += 1
        count_perlu_diperiksa += 1
      elif tot_v > b_val:
        count_plat_over += 1
        count_perlu_diperiksa += 1
      else:
        count_normal += 1

    # Tampilkan Kartu Metrik (Atas Tab)
    m1, m2, m3 = st.columns(3)
    with m1:
      st.metric("Plat melewati kuota harian", count_plat_over)
    with m2:
      st.metric("Transaksi subsidi tanpa nopol", count_no_nopol)
    with m3:
      st.metric("Angka plat tak cocok konsumsi (lead)", 0)

    m4, m5, m6, m7 = st.columns(4)
    with m4:
      st.metric("Total Transaksi Subsidi", total_trx)
    with m5:
      st.metric("Sangat mencurigakan", 0)
    with m6:
      st.metric("Perlu diperiksa", count_perlu_diperiksa)
    with m7:
      st.metric("Normal", count_normal)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TAB JBT DAN JBKP ---
    tab_jbt, tab_jbkp = st.tabs(
        [f"JBT - Solar ({len(df_jbt)})", f"JBKP - Pertalite ({len(df_jbkp)})"]
    )

    def render_dashboard_tab(data_tab, nama_bbm):
      if data_tab.empty:
        st.info(f"Tidak ada data transaksi untuk kategori {nama_bbm}.")
        return

      # Tombol aksi atas tab
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
            data_tab[plat_col]
            .astype(str)
            .str.contains(search_plat, case=False, na=False)
        ]

      # --- 1. BAGIAN ATAS TAB: REKAP PER PLAT (HARIAN) ---
      st.markdown(f"#### Rekap per Plat (Harian) — {nama_bbm}")
      st.caption(
          "Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang"
          " lewat kuota di atas. Perkiraan jenis = lead, wajib dicek"
          " CCTV/SAMSAT."
      )

      plat_totals = (
          data_tab.groupby(plat_col)[vol_col].sum().to_dict()
          if plat_col and vol_col
          else {}
      )

      rekap_rows = []
      for p, total_v in plat_totals.items():
        if "BUS" in str(p).upper() or total_v > 120:
          j_str = "≈ Bus"
          b_val = limit_bus
        elif total_v > 60:
          j_str = "≈ Mobil barang"
          b_val = limit_mobil_barang
        else:
          j_str = "≈ Mobil penumpang"
          b_val = limit_mobil_penumpang

        stat = (
            "Perlu Diperiksa"
            if (total_v > b_val or p in ["N/A", "-", ""])
            else "Normal"
        )
        freq = len(data_tab[data_tab[plat_col] == p])
        rekap_rows.append(
            {
                "Plat": p,
                "Jenis": j_str,
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
          pct = min(int((r_row["Total"] / r_row["Batas"]) * 100), 100)
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
                f"{r_row['Total']:.1f} L / {r_row['Batas']} L (batas"
                f" terlonggar) · {pct}%"
            )
          with rk_cols[4]:
            if r_row["Status"] == "Perlu Diperiksa":
              st.markdown(
                  "<span"
                  " style='background-color:#fef3c7;color:#d97706;padding:3px"
                  " 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟠"
                  " Perlu Diperiksa</span>",
                  unsafe_allow_html=True,
              )
            else:
              st.markdown(
                  "<span"
                  " style='background-color:#d1fae5;color:#059669;padding:3px"
                  " 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟢"
                  " Normal</span>",
                  unsafe_allow_html=True,
              )
          st.markdown(
              "<hr style='margin:3px 0;opacity:0.2;'>", unsafe_allow_html=True
          )

      st.markdown("<br>", unsafe_allow_html=True)

      # --- 2. BAGIAN BAWAH TAB: RINCIAN TRANSAKSI & BUKTI CCTV ---
      st.markdown(f"#### Rincian Transaksi & Bukti CCTV — {nama_bbm}")

      h_cols = st.columns([1.2, 0.9, 1.2, 1.3, 0.9, 0.9, 1.2, 1.1, 1.8])
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
        st.markdown("**PERKIRAAN JENIS**")
      with h_cols[7]:
        st.markdown("**STATUS**")
      with h_cols[8]:
        st.markdown("**ALASAN TEMUAN**")
      st.markdown(
          "<hr style='margin:5px 0;opacity:0.5;'>", unsafe_allow_html=True
      )

      if f"foto_dict_{nama_bbm}" not in st.session_state:
        st.session_state[f"foto_dict_{nama_bbm}"] = {}

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
        if "BUS" in trx_plat.upper() or total_vol_plat > 120:
          jenis_str = "≈ Bus"
          batas_val = limit_bus
          jenis_label = "mobil besar/bus"
        elif total_vol_plat > 60:
          jenis_str = "≈ Mobil barang"
          batas_val = limit_mobil_barang
          jenis_label = "mobil barang"
        else:
          jenis_str = "≈ Mobil penumpang"
          batas_val = limit_mobil_penumpang
          jenis_label = "mobil pribadi"

        if trx_plat in ["N/A", "-", ""]:
          status = "Perlu Diperiksa"
          alasan = "Subsidi tanpa nopol — wajib dicatat per aturan"
        elif total_vol_plat > batas_val:
          status = "Perlu Diperiksa"
          alasan = (
              f"Total harian {total_vol_plat:.1f}L > jatah {jenis_label}"
              f" ({batas_val}L) — konfirmasi jenis"
          )
        else:
          status = "Normal"
          alasan = "Normal"

        r_cols = st.columns([1.2, 0.9, 1.2, 1.3, 0.9, 0.9, 1.2, 1.1, 1.8])
        foto_key = f"foto_trx_{nama_bbm}_{idx}"

        with r_cols[0]:
          if foto_key in st.session_state[f"foto_dict_{nama_bbm}"]:
            st.image(
                st.session_state[f"foto_dict_{nama_bbm}"][foto_key], width=65
            )
            rc1, rc2 = st.columns(2)
            with rc1:
              if st.button("📷 Ganti", key=f"gc_{nama_bbm}_{idx}"):
                st.session_state[f"edit_mode_{nama_bbm}_{idx}"] = "kamera"
                st.rerun()
            with rc2:
              if st.button("🗑️ Hapus", key=f"del_{nama_bbm}_{idx}"):
                del st.session_state[f"foto_dict_{nama_bbm}"][foto_key]
                if f"edit_mode_{nama_bbm}_{idx}" in st.session_state:
                  del st.session_state[f"edit_mode_{nama_bbm}_{idx}"]
                st.rerun()
          else:
            bc1, bc2 = st.columns(2)
            with bc1:
              if st.button("📷 Kamera", key=f"bc_{nama_bbm}_{idx}"):
                st.session_state[f"edit_mode_{nama_bbm}_{idx}"] = "kamera"
                st.rerun()
            with bc2:
              if st.button("📁 Galeri", key=f"bg_{nama_bbm}_{idx}"):
                st.session_state[f"edit_mode_{nama_bbm}_{idx}"] = "galeri"
                st.rerun()

          mode_edit = st.session_state.get(f"edit_mode_{nama_bbm}_{idx}")
          if mode_edit == "kamera":
            img_in = st.camera_input(
                "Ambil Foto", key=f"cam_in_{nama_bbm}_{idx}"
            )
            if img_in is not None:
              st.session_state[f"foto_dict_{nama_bbm}"][foto_key] = img_in
              del st.session_state[f"edit_mode_{nama_bbm}_{idx}"]
              st.rerun()
          elif mode_edit == "galeri":
            img_in = st.file_uploader(
                "Pilih Foto",
                type=["jpg", "jpeg", "png"],
                key=f"gal_in_{nama_bbm}_{idx}",
            )
            if img_in is not None:
              st.session_state[f"foto_dict_{nama_bbm}"][foto_key] = img_in
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
              f"{jenis_str}<br><small>ESTIMASI PLAT</small>",
              unsafe_allow_html=True,
          )
        with r_cols[7]:
          if status == "Perlu Diperiksa":
            st.markdown(
                "<span style='background-color:#fef3c7;color:#d97706;padding:3px"
                " 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟠"
                " Perlu Diperiksa</span>",
                unsafe_allow_html=True,
            )
          else:
            st.markdown(
                "<span style='background-color:#d1fae5;color:#059669;padding:3px"
                " 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟢"
                " Normal</span>",
                unsafe_allow_html=True,
            )
        with r_cols[8]:
          if status == "Perlu Diperiksa":
            st.error(alasan)
          else:
            st.success(alasan)

        st.markdown(
            "<hr style='margin:5px 0;opacity:0.3;'>", unsafe_allow_html=True
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
