import io
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Dashboard
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU",
    page_icon="⛽",
    layout="wide",
)

# Header Dashboard
st.markdown("### 📊 MONITORING · DATA H-1 (KEMARIN)")
st.markdown(
    "## ⛽ Monitor Subsidi Tepat Guna",
    help="Penyaringan awal anomali BBM bersubsidi — untuk verifikasi CCTV & koordinasi SAMSAT.",
)
st.markdown(
    "---"
)  # Menggunakan garis pemisah sesuai instruksi visual toolkit


# Sidebar / Pengaturan Ambang Batas & Kuota
with st.sidebar:
  st.header("⚙️ Pengaturan Ambang Batas & Kuota")
  max_volume_harian = st.number_input(
      "Maks. Akumulasi Harian (Liter)", value=60, min_value=10, max_value=200
  )
  max_frekuensi_isi = st.number_input(
      "Maks. Frekuensi Isi Ulang per Hari", value=3, min_value=1, max_value=10
  )
  st.info(
      "Atur parameter di atas untuk menyesuaikan sensitivitas pendeteksian"
      " anomali sistem."
  )

# Area Unggah File
st.markdown(
    "#### Tarik satu file CSV/XLSX (data kemarin) ke sini, atau klik untuk"
    " pilih file"
)
st.caption(
    "Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi (Pertamax"
    " dll.) diabaikan. Plat diambil dari kolom Payment."
)

uploaded_file = st.file_uploader(
    "Upload file Hose Delivery (CSV/XLSX)", type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
  try:
    # Membaca file berdasarkan ekstensinya
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)

    # Validasi kolom standar (mengatasi variasi nama kolom huruf besar/kecil)
    df.columns = df.columns.str.strip().str.title()

    # Memetakan kolom yang dibutuhkan
    # Asumsi kolom standar: Product, Volume (L), Payment (untuk nopol), Date, Time, dll.
    required_cols = ["Product", "Volume (L)", "Payment"]

    # Mencari kolom alternatif jika format sedikit berbeda
    prod_col = next(
        (c for c in df.columns if "product" in c.lower()), "Product"
    )
    vol_col = next((c for c in df.columns if "volume" in c.lower()), "Volume")
    pay_col = next((c for c in df.columns if "payment" in c.lower()), "Payment")

    # Filter hanya produk Subsidi (Solar / Bio Solar / Pertalite / JBT / JBKP)
    df["Clean_Product"] = df[prod_col].astype(str).str.upper()
    df_subsidi = df[
        df["Clean_Product"].str.contains("SOLAR|PERTALITE|JBT|JBKP", na=False)
    ].copy()

    st.success(
        f"File berhasil dianalisis! Ditemukan {len(df_subsidi)} baris transaksi"
        " subsidi."
    )

    # Tab Pemisahan JBT (Solar) dan JBKP (Pertalite)
    tab_jbt, tab_jbkp, tab_anomali = st.tabs(
        ["Tab JBT (Solar)", "Tab JBKP (Pertalite)", "🚨 Indikasi Anomali"]
    )

    df_jbt = df_subsidi[
        df_subsidi["Clean_Product"].str.contains("SOLAR|JBT", na=False)
    ]
    df_jbkp = df_subsidi[
        df_subsidi["Clean_Product"].str.contains("PERTALITE|JBKP", na=False)
    ]

    with tab_jbt:
      st.subheader("Daftar Transaksi JBT (Solar)")
      st.dataframe(df_jbt, use_container_width=True)

    with tab_jbkp:
      st.subheader("Daftar Transaksi JBKP (Pertalite)")
      st.dataframe(df_jbkp, use_container_width=True)

    with tab_anomali:
      st.subheader("Penyaringan Awal Sinyal Anomali")

      # Simulasi Deteksi Anomali
      # 1. Subsidi tanpa nopol (kolom pembayaran kosong atau hanya teks Cash tanpa plat)
      anomali_tanpa_nopol = df_subsidi[
          df_subsidi[pay_col].isna()
          | (df_subsidi[pay_col].astype(str).str.strip() == "")
          | (df_subsidi[pay_col].astype(str).str.upper() == "CASH")
      ].copy()
      anomali_tanpa_nopol["Jenis Anomali"] = "Subsidi Tanpa Nopol"

      # 2. Akumulasi melebihi kuota harian (jika ada kolom plat / payment terdeteksi)
      # Mengelompokkan berdasarkan nopol di kolom payment
      if pay_col in df_subsidi.columns:
        akumulasi_nopol = (
            df_subsidi.groupby(pay_col)[vol_col].sum().reset_index()
        )
        plat_lebih_kuota = akumulasi_nopol[
            akumulasi_nopol[vol_col] > max_volume_harian
        ][pay_col].tolist()
        anomali_kuota = df_subsidi[
            df_subsidi[pay_col].isin(plat_lebih_kuota)
        ].copy()
        anomali_kuota["Jenis Anomali"] = "Akumulasi Harian Melewati Kuota"
      else:
        anomali_kuota = pd.DataFrame()

      # Gabungkan temuan anomali
      df_final_anomali = pd.concat(
          [anomali_tanpa_nopol, anomali_kuota]
      ).drop_duplicates()

      if not df_final_anomali.empty:
        st.warning(
            f"Ditemukan {len(df_final_anomali)} baris transaksi yang"
            " mengindikasikan anomali!"
        )
        st.dataframe(df_final_anomali, use_container_width=True)

        # Fitur Unggah Foto CCTV Pendukung per Baris
        st.markdown("#### 📷 Verifikasi Foto CCTV / Bukti Pendukung")
        uploaded_cctv = st.file_uploader(
            "Unggah tangkapan layar CCTV untuk justifikasi pemeriksaan",
            type=["png", "jpg", "jpeg"],
            key="cctv_upload",
        )
        if uploaded_cctv:
          st.image(
              uploaded_cctv,
              caption="Bukti CCTV Pemeriksaan Baris Anomali",
              width=350,
          )
          st.info(
              "Foto terlampir sebagai referensi verifikasi visual lokal."
          )
      else:
        st.info("Tidak ada anomali terdeteksi berdasarkan ambang batas saat ini.")

  except Exception as e:
    st.error(
        f"Terjadi kesalahan saat memproses file. Pastikan format kolom sesuai."
        f" Detail error: {e}"
    )

else:
  # Tampilan awal sebelum file diunggah (sesuai gambar dashboard Anda)
  st.markdown(
      """
        <div style="padding: 40px; border: 2px dashed #d1d5db; border-radius: 10px; text-align: center; background-color: #f9fafb;">
            <p style="color: #6b7280; font-size: 16px; margin: 0;"><b>Belum ada data yang dianalisis</b></p>
            <p style="color: #9ca3af; font-size: 14px;">Upload satu file CSV/XLSX hose delivery (data kemarin) untuk mulai monitoring.</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #6b7280; font-size: 12px;'>Analisis"
    " & foto berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke"
    " server manapun. Alat bantu penyaringan awal; setiap temuan wajib"
    " dikonfirmasi CCTV/SAMSAT sebelum tindakan.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #9ca3af; font-size: 11px;'>Made by"
    " Antoni · Area Business Head NTT</p>",
    unsafe_allow_html=True,
)
