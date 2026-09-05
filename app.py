import io
from datetime import datetime
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Monitoring Subsidi Tepat - SPBU TAC",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
<style>
    .main { background-color: #f1f5f9; }
    
    .custom-metric-card {
        background-color: #ffffff;
        padding: 12px 16px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .custom-metric-card-alert {
        background-color: #fee2e2 !important;
        padding: 12px 16px;
        border-radius: 6px;
        border: 1px solid #f87171 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Inisialisasi Session State
if "filter_produk" not in st.session_state:
  st.session_state.filter_produk = "SEMUA"

if "kuota_pribadi_r4" not in st.session_state:
  st.session_state.kuota_pribadi_r4 = 60.0
if "kuota_motor" not in st.session_state:
  st.session_state.kuota_motor = 10.0
if "kuota_penumpang" not in st.session_state:
  st.session_state.kuota_penumpang = 100.0
if "kuota_barang" not in st.session_state:
  st.session_state.kuota_barang = 150.0
if "kuota_berat" not in st.session_state:
  st.session_state.kuota_berat = 200.0

if "max_frekuensi_harian" not in st.session_state:
  st.session_state.max_frekuensi_harian = 2
if "min_jeda_waktu" not in st.session_state:
  st.session_state.min_jeda_waktu = 30  # dalam menit
if "batas_sekali_isi" not in st.session_state:
  st.session_state.batas_sekali_isi = 200.0

if "evidens_media" not in st.session_state:
  st.session_state.evidens_media = (
      {}
  )  # Menyimpan file foto/kamera per ID transaksi
if "catatan_transaksi" not in st.session_state:
  st.session_state.catatan_transaksi = {}

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU Monitoring System | JBT & JBKP SPBU TAC - Reg V**")
st.markdown("---")

# Sidebar / Upload Section
st.sidebar.header("📂 Pengaturan & Sumber Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload file Excel (.xlsx) atau CSV", type=["xlsx", "csv"]
)
selected_date = st.sidebar.date_input(
    "Pilih Tanggal Analisis", datetime.now().date()
)

if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      df_raw = pd.read_csv(uploaded_file)
    else:
      df_raw = pd.read_excel(uploaded_file, engine="openpyxl")

    st.sidebar.success("File berhasil dimuat!")

    df_raw.columns = df_raw.columns.str.strip()
    columns_list = list(df_raw.columns)


    def find_best_column(keywords, negative_keywords=[]):
      for col in columns_list:
        col_lower = col.lower()
        if any(neg in col_lower for neg in negative_keywords):
          continue
        for kw in keywords:
          if kw in col_lower:
            return col
      return columns_list[0] if columns_list else None


    default_id = find_best_column(
        ["id", "transaksi", "trx", "code", "kode"]
    )
    default_nopol = find_best_column(
        ["plat", "nopol", "nomor", "vehicle", "police", "kendaraan"],
        ["payment", "bayar", "status", "id"],
    )
    default_vol = find_best_column(["volume", "liter", "vol", "qty", "jumlah"])
    default_produk = find_best_column(
        ["produk", "bbm", "jenis", "product", "fuel", "bahan bakar"]
    )
    default_status = find_best_column(
        ["status", "keterangan", "ket", "remark", "note"]
    )
    default_time = find_best_column(
        ["waktu", "time", "jam", "tanggal", "date", "timestamp"]
    )
    default_nozzle = find_best_column(
        ["nozzle", "nosel", "pompa", "island", "dispenser"]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Pemetaan Kolom Data")

    col_id_opt = st.sidebar.selectbox(
        "Kolom ID Transaksi",
        columns_list,
        index=(
            columns_list.index(default_id) if default_id in columns_list else 0
        ),
    )
    col_nopol_opt = st.sidebar.selectbox(
        "Kolom Plat Nomor / Nopol",
        columns_list,
        index=(
            columns_list.index(default_nopol)
            if default_nopol in columns_list
            else 0
        ),
    )
    col_vol_opt = st.sidebar.selectbox(
        "Kolom Volume (L)",
        columns_list,
        index=(
            columns_list.index(default_vol) if default_vol in columns_list else 0
        ),
    )
    col_produk_opt = st.sidebar.selectbox(
        "Kolom Produk / Jenis BBM",
        columns_list,
        index=(
            columns_list.index(default_produk)
            if default_produk in columns_list
            else 0
        ),
    )
    col_time_opt = st.sidebar.selectbox(
        "Kolom Waktu / Jam Transaksi",
        columns_list,
        index=(
            columns_list.index(default_time)
            if default_time in columns_list
            else 0
        ),
    )
    col_nozzle_opt = st.sidebar.selectbox(
        "Kolom Nozzle / Pompa (Opsional)",
        columns_list,
        index=(
            columns_list.index(default_nozzle)
            if default_nozzle in columns_list
            else 0
        ),
    )

    # Validasi Format & Karakter Nopol
    if col_nopol_opt in df_raw.columns:
      df_raw = df_raw.copy()


      def clean_and_validate_nopol(val):
        s = str(val).strip()
        s_upper = s.upper()
        invalid_keywords = [
            "CASH",
            "TIDAK ADA",
            "NAN",
            "NONE",
            "-",
            "NULL",
            "TUNAI",
            "0",
            "",
        ]
        if s_upper in invalid_keywords or len(s) < 3:
          return "INVALID_NOPOL"
        cleaned = re.sub(r"[^A-Z0-9 ]", "", s_upper)
        return cleaned if len(cleaned) >= 3 else "INVALID_NOPOL"


      df_raw[col_nopol_opt] = df_raw[col_nopol_opt].apply(
          clean_and_validate_nopol
      )

    # Pisahkan data JBT dan JBKP
    if col_produk_opt in df_raw.columns:
      produk_series = df_raw[col_produk_opt].astype(str)
      df_jbt = df_raw[
          produk_series.str.contains(
              "SOLAR|BIOSOLAR|JBT|MHD|DEALITE", case=False, na=False
          )
      ]
      df_jbkp = df_raw[
          produk_series.str.contains(
              "PERTALITE|JBKP|RON90", case=False, na=False
          )
      ]
    else:
      df_jbt = df_raw.iloc[:0]
      df_jbkp = df_raw.iloc[:0]

    # Filter produk di sidebar / session
    st.sidebar.markdown("---")
    st.session_state.filter_produk = st.sidebar.radio(
        "Filter Jenis Produk", ["SEMUA", "JBT", "JBKP"], horizontal=True
    )

    if st.session_state.filter_produk == "JBT":
      df_display = df_jbt
    elif st.session_state.filter_produk == "JBKP":
      df_display = df_jbkp
    else:
      df_display = df_raw

    # Analisis Waktu & Interval
    df_analysis = df_display.copy()
    if col_time_opt in df_analysis.columns:
      df_analysis["parsed_time"] = pd.to_datetime(
          df_analysis[col_time_opt], errors="coerce"
      )
      df_analysis = df_analysis.sort_values(
          by=[col_nopol_opt, "parsed_time"]
      )
      df_analysis["prev_time"] = df_analysis.groupby(col_nopol_opt)[
          "parsed_time"
      ].shift(1)
      df_analysis["diff_minutes"] = (
          df_analysis["parsed_time"] - df_analysis["prev_time"]
      ).dt.total_seconds() / 60.0
      df_analysis["is_fast_interval"] = (
          df_analysis["diff_minutes"] <= st.session_state.min_jeda_waktu
      )
    else:
      df_analysis["diff_minutes"] = None
      df_analysis["is_fast_interval"] = False

    if col_nozzle_opt in df_analysis.columns and col_time_opt in df_analysis.columns:
      df_analysis["prev_nozzle"] = df_analysis.groupby(col_nopol_opt)[
          col_nozzle_opt
      ].shift(1)
      df_analysis["is_cross_pump"] = (
          df_analysis["is_fast_interval"]
          & (
              df_analysis[col_nozzle_opt].astype(str)
              != df_analysis["prev_nozzle"].astype(str)
          )
          & (df_analysis["diff_minutes"] <= 60)
      )
    else:
      df_analysis["is_cross_pump"] = False

    # Main Layout Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Ringkasan Transaksi",
        "🔍 Detail Kendaraan & Evidens HP/CCTV",
        "⚙️ Pengaturan Batas & Regulasi",
    ])

    with tab1:
      st.subheader(
          "Rekap Harian Penyaluran BBM Subsidi & Deteksi Kecurangan"
      )

      if not df_display.empty and col_nopol_opt in df_display.columns:
        agg_dict_m = {
            "total_volume": (
                col_vol_opt,
                lambda x: pd.to_numeric(x, errors="coerce").sum(),
            ),
            "freq": (col_vol_opt, "count"),
        }
        df_g_metric = df_analysis.groupby(col_nopol_opt).agg(
            **agg_dict_m
        ).reset_index()

        tanpa_nopol = len(
            df_analysis[df_analysis[col_nopol_opt] == "INVALID_NOPOL"]
        )
        mobil_helikopter_count = len(
            df_g_metric[
                df_g_metric["freq"] > st.session_state.max_frekuensi_harian
            ]
        )
        vol_numeric = pd.to_numeric(
            df_analysis[col_vol_opt], errors="coerce"
        ).fillna(0)
        single_cap_violations = len(
            df_analysis[vol_numeric > st.session_state.batas_sekali_isi]
        )
        fast_interval_count = (
            int(df_analysis["is_fast_interval"].sum())
            if "is_fast_interval" in df_analysis.columns
            else 0
        )
        cross_pump_count = (
            int(df_analysis["is_cross_pump"].sum())
            if "is_cross_pump" in df_analysis.columns
            else 0
        )
      else:
        tanpa_nopol = 0
        mobil_helikopter_count = 0
        single_cap_violations = 0
        fast_interval_count = 0
        cross_pump_count = 0


      def render_custom_metric(label, value, icon, alert_if_gt_zero=False):
        is_alert = alert_if_gt_zero and (
            isinstance(value, (int, float)) and value > 0
        )
        card_class = (
            "custom-metric-card-alert" if is_alert else "custom-metric-card"
        )
        text_color = "#b91c1c" if is_alert else "#1e293b"
        label_color = "#991b1b" if is_alert else "#64748b"

        html_content = f"""
                <div class="{card_class}">
                    <div style="font-size: 0.75rem; color: {label_color}; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; font-weight: 500;">
                        <span>{icon}</span> {label}
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 600; color: {text_color};">
                        {value}
                    </div>
                </div>
                """
        st.markdown(html_content, unsafe_allow_html=True)


      m1, m2, m3, m4, m5 = st.columns(5)
      with m1:
        render_custom_metric(
            "Jeda Waktu Singkat (<30m)",
            fast_interval_count,
            "⏱️",
            alert_if_gt_zero=True,
        )
      with m2:
        render_custom_metric(
            "Anomali Cross-Pump",
            cross_pump_count,
            "🔀",
            alert_if_gt_zero=True,
        )
      with m3:
        render_custom_metric(
            "Potensi Mobil Helikopter",
            mobil_helikopter_count,
            "🚁",
            alert_if_gt_zero=True,
        )
      with m4:
        render_custom_metric(
            "Langgar Batas Sekali Isi",
            single_cap_violations,
            "⚠️",
            alert_if_gt_zero=True,
        )
      with m5:
        render_custom_metric(
            "Transaksi Tanpa Nopol", tanpa_nopol, "🚫", alert_if_gt_zero=True
        )

    with tab2:
      st.subheader("🔍 Detail Transaksi & Upload Evidens HP / Kamera / Galeri")
      st.markdown(
          "Gunakan tombol **📷 Kamera HP** atau **📁 Galeri HP** di bawah untuk"
          " mengambil atau mengupload foto eviden langsung dari perangkat Anda."
      )

      if df_display.empty:
        st.info(
            "Belum ada data transaksi yang dimuat. Silakan upload file data"
            " transaksi di sidebar."
        )
      else:
        for idx, row in df_display.iterrows():
          trx_id = (
              str(row[col_id_opt])
              if col_id_opt in df_display.columns
              else str(idx)
          )
          nopol = (
              str(row[col_nopol_opt])
              if col_nopol_opt in df_display.columns
              else "-"
          )
          waktu = (
              str(row[col_time_opt])
              if col_time_opt in df_display.columns
              else "-"
          )
          produk = (
              str(row[col_produk_opt])
              if col_produk_opt in df_display.columns
              else "-"
          )
          volume = (
              str(row[col_vol_opt])
              if col_vol_opt in df_display.columns
              else "-"
          )
          nozzle_val = (
              str(row[col_nozzle_opt])
              if col_nozzle_opt in df_display.columns
              else "-"
          )

          with st.container():
            st.markdown(f"---")
            col_info, col_btn_cam, col_btn_gal = st.columns([3, 1, 1])

            with col_info:
              st.markdown(
                  f"**ID:** `{trx_id}` | **Waktu:** `{waktu}` |"
                  f" **Produk/Nozzle:** `{produk} / {nozzle_val}`"
              )
              st.markdown(
                  f"**Plat Nopol:** `{nopol}` | **Volume:** `{volume} L`"
              )

              # Cek anomali baris ini
              is_fast = False
              if col_time_opt in df_analysis.columns:
                matched_row = df_analysis[df_analysis.index == idx]
                if (
                    not matched_row.empty
                    and "is_fast_interval" in matched_row.columns
                ):
                  is_fast = matched_row["is_fast_interval"].values[0]

              if is_fast:
                st.warning(
                    "⚠️ Indikasi pindah nosel atau jeda waktu pengisian terlalu"
                    " singkat (<30 menit)"
                )

            # Tombol Kamera HP (Menggunakan popover agar rapi & langsung aktif di HP)
            with col_btn_cam:
              with st.popover("📷 Kamera HP"):
                st.markdown(f"**Ambil Foto Kamera (ID: {trx_id})**")
                cam_file = st.camera_input(
                    "Foto Kamera HP", key=f"cam_{trx_id}"
                )
                if cam_file is not None:
                  st.session_state.evidens_media[trx_id] = cam_file
                  st.success("Foto kamera tersimpan!")

            # Tombol Galeri HP
            with col_btn_gal:
              with st.popover("📁 Galeri HP"):
                st.markdown(f"**Upload dari Galeri (ID: {trx_id})**")
                gal_file = st.file_uploader(
                    "Pilih File Foto",
                    type=["jpg", "jpeg", "png"],
                    key=f"gal_{trx_id}",
                )
                if gal_file is not None:
                  st.session_state.evidens_media[trx_id] = gal_file
                  st.success("File galeri tersimpan!")

            # Tampilkan preview jika sudah diupload/dipotret
            if trx_id in st.session_state.evidens_media:
              st.image(
                  st.session_state.evidens_media[trx_id],
                  caption=f"Evidens Terupload - ID {trx_id}",
                  width=200,
              )

            # Catatan Transaksi
            note_key = f"note_{trx_id}"
            catatan_val = st.text_input(
                "Tulis catatan (cth: QR CODE sesuai DII)...",
                key=note_key,
                value=st.session_state.catatan_transaksi.get(trx_id, ""),
            )
            st.session_state.catatan_transaksi[trx_id] = catatan_val

    with tab3:
      st.subheader("⚙️ Pengaturan Batas & Regulasi Kuota SPBU")
      st.session_state.max_frekuensi_harian = st.number_input(
          "Maksimal Frekuensi Harian per Nopol",
          value=st.session_state.max_frekuensi_harian,
      )
      st.session_state.min_jeda_waktu = st.number_input(
          "Minimal Jeda Waktu Antar Pengisian (Menit)",
          value=st.session_state.min_jeda_waktu,
      )
      st.session_state.batas_sekali_isi = st.number_input(
          "Batas Maksimal Sekali Isi (Liter)",
          value=st.session_state.batas_sekali_isi,
      )

  except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses file: {e}")
else:
  st.info(
      "Silakan upload file Excel (.xlsx) atau CSV transaksi melalui panel"
      " sidebar di sebelah kiri untuk memulai monitoring."
  )
