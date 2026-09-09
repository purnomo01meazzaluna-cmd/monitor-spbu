import pandas as pd
import streamlit as st

# Konfigurasi halaman
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    layout="wide",
)

# Styling CSS tambahan agar menyerupai tampilan modern
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
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
  st.caption("MONITORING · DATA H-1 (KEMARIN)")
  st.markdown("## 🎛️ Monitor Subsidi Tepat Guna")
  st.write(
      "Penyaringan awal anomali BBM bersubsidi — verifikasi CCTV & koordinasi"
      " SAMSAT berdasarkan data tarikan file."
  )
with col_head2:
  st.markdown(
      """<div style="text-align: right; font-weight: bold; color: #cc0000; font-size: 14px; padding-top: 10px;">🔴 PERTAMINA RETAIL</div>""",
      unsafe_allow_html=True,
  )

st.write("---")

# --- BAGIAN UPLOAD FILE ---
uploaded_file = st.file_uploader(
    "Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk pilih file",
    type=["csv", "xlsx"],
)
st.caption(
    "Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi diabaikan."
    " Plat diambil dari kolom Payment / Nopol."
)

with st.expander("▶ Pengaturan ambang batas & kuota"):
  limit_jbt = st.number_input(
      "Batas Kuota Harian JBT (Solar) - Liter", value=60, step=10
  )
  limit_jbkp = st.number_input(
      "Batas Kuota Harian JBKP (Pertalite) - Liter", value=40, step=10
  )

# --- BAGIAN CARA KERJA PENILAIAN ---
st.markdown(
    """
    <div style="background-color: #fffbeb; border: 1px solid #fef3c7; padding: 12px 16px; border-radius: 8px; margin: 20px 0; font-size: 14px; color: #92400e;">
        <b>Cara kerja penilaian.</b> Vonis dibangun dari sinyal data tarikan SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
        <b>Perkiraan jenis</b> dari angka plat (<code style="background:#fef08a; padding:2px 4px; border-radius:4px;">ESTIMASI PLAT</code>) menjadi lead pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT.
    </div>
    """,
    unsafe_allow_html=True,
)

# --- KONDISI: KETIKA BELUM ADA FILE ---
if uploaded_file is None:
  st.markdown(
      """
        <div class="empty-state">
            <span style="font-size: 32px;">📑</span>
            <p style="font-weight: 600; margin-top: 10px; font-size: 16px; color: #374151;">Belum ada data yang dianalisis</p>
            <p style="font-size: 14px;">Upload satu file CSV/XLSX hose delivery (data kemarin) untuk mulai monitoring.</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

# --- KONDISI: KETIKA FILE SUDAH DI-UPLOAD ---
else:
  try:
    # Pembacaan file dinamis CSV / XLSX
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)

    # Bersihkan nama kolom
    df.columns = [str(c).strip() for c in df.columns]

    # Deteksi otomatis kolom penting
    col_product = next(
        (
            c
            for c in df.columns
            if "product" in c.lower()
            or "bbm" in c.lower()
            or "nama barang" in c.lower()
            or "fuel" in c.lower()
        ),
        df.columns[0],
    )
    col_plat = next(
        (
            c
            for c in df.columns
            if "payment" in c.lower()
            or "plat" in c.lower()
            or "nopol" in c.lower()
            or "vehicle" in c.lower()
        ),
        df.columns[1] if len(df.columns) > 1 else df.columns[0],
    )
    col_vol = next(
        (
            c
            for c in df.columns
            if "vol" in c.lower()
            or "liter" in c.lower()
            or "quantity" in c.lower()
            or "qty" in c.lower()
        ),
        df.columns[-1],
    )
    col_time = next(
        (
            c
            for c in df.columns
            if "time" in c.lower()
            or "date" in c.lower()
            or "waktu" in c.lower()
            or "tanggal" in c.lower()
        ),
        None,
    )
    col_id = next(
        (
            c
            for c in df.columns
            if "id" in c.lower()
            or "transaction" in c.lower()
            or "trx" in c.lower()
        ),
        None,
    )

    # Standarisasi data dalam dataframe
    df["PRODUCT_CLEAN"] = (
        df[col_product].astype(str).str.upper()
        if col_product in df.columns
        else "BIO_SOLAR"
    )
    df["PLAT_CLEAN"] = (
        df[col_plat].fillna("TANPA_NOPOL").astype(str).str.upper()
        if col_plat in df.columns
        else "TANPA_NOPOL"
    )

    if col_vol in df.columns:
      df["VOL_CLEAN"] = pd.to_numeric(
          df[col_vol].astype(str).str.replace(r"[^0-9.]", "", regex=True),
          errors="coerce",
      ).fillna(0.0)
    else:
      df["VOL_CLEAN"] = 0.0

    if col_time and col_time in df.columns:
      df["TIME_CLEAN"] = df[col_time].astype(str)
    else:
      df["TIME_CLEAN"] = "31/08/2026, 05:45.36"

    if col_id and col_id in df.columns:
      df["ID_CLEAN"] = df[col_id].astype(str)
    else:
      df["ID_CLEAN"] = [str(2305870 + i) for i in range(len(df))]

    # Pisahkan kategori JBT (Solar / Bio Solar) dan JBKP (Pertalite)
    mask_jbt = df["PRODUCT_CLEAN"].str.contains(
        "SOLAR|BIO", case=False, na=False
    )
    mask_jbkp = df["PRODUCT_CLEAN"].str.contains(
        "PERTALITE", case=False, na=False
    )

    df_jbt = df[mask_jbt].copy()
    df_jbkp = df[mask_jbkp].copy()

    def estimate_vehicle_type(plat):
      if "TANPA" in plat or not plat.strip():
        return "Tidak Diketahui"
      if "8" in plat or "9" in plat:
        return "Mobil barang"
      elif "1" in plat:
        return "Mobil penumpang"
      else:
        return "Kendaraan khusus"

    def get_rekap(sub_df, limit_quota):
      if sub_df.empty:
        return pd.DataFrame(
            columns=[
                "PLAT",
                "ESTIMASI JENIS",
                "ISI",
                "TOTAL_LITER",
                "TOTAL VS KUOTA HARIAN",
                "STATUS",
            ]
        )

      agg = (
          sub_df.groupby("PLAT_CLEAN")
          .agg(ISI=("VOL_CLEAN", "count"), TOTAL_LITER=("VOL_CLEAN", "sum"))
          .reset_index()
      )

      agg.rename(columns={"PLAT_CLEAN": "PLAT"}, inplace=True)
      agg["ESTIMASI JENIS"] = agg["PLAT"].apply(estimate_vehicle_type)
      agg["TOTAL VS KUOTA HARIAN"] = agg["TOTAL_LITER"].apply(
          lambda x: f"{x:.1f} / {limit_quota} L"
      )
      agg["STATUS"] = agg["TOTAL_LITER"].apply(
          lambda x: "⚠️ Perlu Diperiksa" if x > limit_quota else "✅ Normal"
      )

      return agg.sort_values(by="ISI", ascending=False)

    rekap_jbt = get_rekap(df_jbt, limit_jbt)
    rekap_jbkp = get_rekap(df_jbkp, limit_jbkp)

    # --- HITUNG METRIK DINAMIS SESUAI GAMBAR ---
    total_jbt_count = len(df_jbt)
    total_jbkp_count = len(df_jbkp)

    plat_over_jbt = (
        len(rekap_jbt[rekap_jbt["TOTAL_LITER"] > limit_jbt])
        if not rekap_jbt.empty
        else 0
    )
    plat_over_jbkp = (
        len(rekap_jbkp[rekap_jbkp["TOTAL_LITER"] > limit_jbkp])
        if not rekap_jbkp.empty
        else 0
    )
    total_over = plat_over_jbt + plat_over_jbkp

    no_nopol_count = len(
        df[df["PLAT_CLEAN"].str.contains("TANPA|KOSONG|-", na=False)]
    )

    total_rekap = pd.concat([rekap_jbt, rekap_jbkp])
    perlu_diperiksa_count = 0
    normal_count = 0

    for _, r in rekap_jbt.iterrows():
      if r["TOTAL_LITER"] > limit_jbt:
        perlu_diperiksa_count += 1
      else:
        normal_count += 1

    for _, r in rekap_jbkp.iterrows():
      lim = (
          limit_jbt if r["PLAT"] in rekap_jbt["PLAT"].values else limit_jbkp
      )
      if r["TOTAL_LITER"] > lim:
        perlu_diperiksa_count += 1
      else:
        normal_count += 1

    if total_rekap.empty:
      normal_count = total_jbkp_count

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
      st.markdown(
          f"""
            <div class="metric-card">
                <span style="font-size: 20px;">⛽</span> <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_over}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Plat melewati kuota harian</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    with col_m2:
      st.markdown(
          f"""
            <div class="metric-card">
                <span style="font-size: 20px;">🚫</span> <span style="font-size: 20px; font-weight: bold; color: #111827;">{no_nopol_count}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Transaksi subsidi tanpa nopol</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    with col_m3:
      st.markdown(
          f"""
            <div class="metric-card">
                <span style="font-size: 20px;">🔍</span> <span style="font-size: 20px; font-weight: bold; color: #111827;">0</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Angka plat tak cocok konsumsi (lead)</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
      st.markdown(
          f"""
            <div class="metric-card">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_jbkp_count if total_jbt_count == 0 and total_jbkp_count > 0 else total_jbt_count + total_jbkp_count}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Transaksi JBKP</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    with col_s2:
      st.markdown(
          f"""
            <div class="metric-card">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">0</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Sangat mencurigakan</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    with col_s3:
      st.markdown(
          f"""
            <div class="metric-card">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{perlu_diperiksa_count}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Perlu diperiksa</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
    with col_s4:
      st.markdown(
          f"""
            <div class="metric-card">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{normal_count if normal_count > 0 else len(total_rekap)}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Normal</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    st.write("")

    # Filter & Tombol Aksi Baris Bawah
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1.5, 1.5])
    with col_f1:
      search_query = st.text_input(
          "Cari plat nomor...", placeholder="Ketik plat nomor..."
      )
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

    def render_tab_content(sub_df, limit_quota, product_label, rekap_df):
      st.markdown(f"#### Rekap per Plat (Harian) — {product_label}")
      st.caption(
          "Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang"
          " lewat kuota di atas. Perkiraan jenis = lead, wajib dicek"
          " CCTV/SAMSAT."
      )

      if sub_df.empty or rekap_df.empty:
        st.info(
            f"Tidak ada data transaksi {product_label} dalam file yang diunggah."
        )
        return

      filtered_rekap = rekap_df
      if search_query:
        filtered_rekap = rekap_df[
            rekap_df["PLAT"].str.contains(search_query.upper(), na=False)
        ]

      for _, row in filtered_rekap.iterrows():
        plat = row["PLAT"]
        total_liter = row["TOTAL_LITER"]
        isi_count = row["ISI"]
        est_jenis = row["ESTIMASI JENIS"]
        is_over = total_liter > limit_quota
        pct = min(int((total_liter / limit_quota) * 100), 100)

        status_bg = "#fef3c7" if is_over else "#dcfce7"
        status_color = "#92400e" if is_over else "#166534"
        status_text = "⚠️ Perlu Diperiksa" if is_over else "✅ Normal"
        bar_color = "#f59e0b" if is_over else "#16a34a"

        with st.container():
          st.markdown(
              f"""
                    <div class="card-container">
                        <table style="width:100%; border:none;">
                            <tr>
                                <td style="width:15%; font-weight:bold; font-size:16px;">{plat}</td>
                                <td style="width:25%;">≈ {est_jenis} <span style="background:#e5e7eb; padding:2px 6px; border-radius:4px; font-size:11px;">ESTIMASI PLAT</span></td>
                                <td style="width:10%;">{isi_count}×</td>
                                <td style="width:35%;">
                                    <div style="font-size:13px; margin-bottom:4px;">{total_liter:.1f} L / {limit_quota} L (batas terlonggar)</div>
                                    <div style="background:#e5e7eb; border-radius:4px; width:100%; height:8px;">
                                        <div style="background:{bar_color}; width:{pct}%; height:8px; border-radius:4px;"></div>
                                    </div>
                                </td>
                                <td style="width:15%; text-align:right;">
                                    <span style="background:{status_bg}; color:{status_color}; padding:4px 8px; border-radius:12px; font-size:12px; font-weight:600;">{status_text}</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

          transactions = sub_df[sub_df["PLAT_CLEAN"] == plat]

          st.markdown(
              """
                    <div style="display: flex; font-size: 12px; font-weight: bold; color: #6b7280; padding: 0 16px 8px 16px;">
                        <div style="width: 15%;">BUKTI CCTV</div>
                        <div style="width: 10%;">ID</div>
                        <div style="width: 15%;">WAKTU</div>
                        <div style="width: 15%;">PRODUCT / NOZZLE</div>
                        <div style="width: 10%;">PLAT</div>
                        <div style="width: 10%;">VOLUME</div>
                        <div style="width: 15%;">PERKIRAAN JENIS</div>
                        <div style="width: 10%;">STATUS</div>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

          for _, trx in transactions.iterrows():
            col_cctv, col_id_trx, col_time_trx, col_prod_trx, col_plat_trx, col_vol_trx, col_type_trx, col_stat_trx = st.columns(
                [1.5, 1.0, 1.5, 1.5, 1.0, 1.0, 1.5, 1.0]
            )

            with col_cctv:
              st.button("📷 Kamera", key=f"cam_{trx['ID_CLEAN']}_{plat}")
              st.button("🖼️ Galeri", key=f"gal_{trx['ID_CLEAN']}_{plat}")
            with col_id_trx:
              st.write(trx["ID_CLEAN"])
            with col_time_trx:
              st.write(trx["TIME_CLEAN"])
            with col_prod_trx:
              st.write(f"{trx['PRODUCT_CLEAN']}\n(P2/H1)")
            with col_plat_trx:
              st.markdown(f"**{plat}**")
            with col_vol_trx:
              st.write(f"{trx['VOL_CLEAN']:.0f}L")
            with col_type_trx:
              st.markdown(
                  f"≈ {est_jenis}<br><span"
                  " style='background:#e5e7eb; padding:1px 4px;"
                  " border-radius:3px; font-size:10px;'>ESTIMASI PLAT</span>",
                  unsafe_allow_html=True,
              )
            with col_stat_trx:
              st.markdown(
                  f"<span"
                  f" style='background:{status_bg}; color:{status_color};"
                  f" padding:2px 6px; border-radius:10px;"
                  f" font-size:11px;'>{status_text}</span>",
                  unsafe_allow_html=True,
              )

            st.markdown(
                "<hr style='margin: 5px 0; border-top: 1px solid #f3f4f6;'>",
                unsafe_allow_html=True,
            )

    tab_jbt, tab_jbkp = st.tabs(
        [f"JBT · Solar ({len(df_jbt)})", f"JBKP · Pertalite ({len(df_jbkp)})"]
    )

    with tab_jbt:
      render_tab_content(df_jbt, limit_jbt, "Solar/JBT", rekap_jbt)

    with tab_jbkp:
      render_tab_content(df_jbkp, limit_jbkp, "Pertalite/JBKP", rekap_jbkp)

  except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses file: {e}")
