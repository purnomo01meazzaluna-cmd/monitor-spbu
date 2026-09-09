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
        "Penyaringan awal anomali BBM bersubsidi — untuk verifikasi CCTV & koordinasi SAMSAT."
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
    "Solar & Pertalite dipisah otomatis ke tab JBT / JBKP. Non-subsidi (Pertamax dll.) diabaikan. Plat diambil dari kolom Payment."
)

with st.expander("▶ Pengaturan ambang batas & kuota"):
    st.write(
        "Pengaturan kuota harian kendaraan, batasan volume, dan parameter validasi plat nomor."
    )

# --- BAGIAN CARA KERJA PENILAIAN ---
st.markdown(
    """
    <div style="background-color: #fffbeb; border: 1px solid #fef3c7; padding: 12px 16px; border-radius: 8px; margin: 20px 0; font-size: 14px; color: #92400e;">
        <b>Cara kerja penilaian.</b> Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
        <b>Perkiraan jenis</b> dari angka plat (<code style="background:#fef08a; padding:2px 4px; border-radius:4px;">ESTIMASI PLAT</code>) hanya jadi <b>lead "cek plat palsu"</b> bila janggal — mis. angka plat = motor tapi mengisi Solar. 
        Foto CCTV per baris (kamera HP atau upload file di PC) menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
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
    # 1. Kartu Metrik Baris Pertama
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            """<div class="metric-card">⛽ <b style="font-size: 18px;">0</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Plat melewati kuota harian</p></div>""",
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            """<div class="metric-card">🚫 <b style="font-size: 18px;">1</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Transaksi subsidi tanpa nopol</p></div>""",
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            """<div class="metric-card">🔍 <b style="font-size: 18px;">0</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Angka plat tak cocok konsumsi (lead)</p></div>""",
            unsafe_allow_html=True,
        )

    st.write("")

    # 2. Kartu Metrik Baris Kedua
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            """<div class="metric-card"><b style="font-size: 20px;">4</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Transaksi JBT</p></div>""",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            """<div class="metric-card"><b style="font-size: 20px; color:#dc2626;">0</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Sangat mencurigakan</p></div>""",
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            """<div class="metric-card"><b style="font-size: 20px; color:#d97706;">4</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Perlu diperiksa</p></div>""",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            """<div class="metric-card"><b style="font-size: 20px; color:#16a34a;">0</b><p style="margin:4px 0 0 0; font-size:13px; color:#4b5563;">Normal</p></div>""",
            unsafe_allow_html=True,
        )

    st.write("")

    # 3. Tab Navigasi & Filter (JBT & JBKP)
    tab_jbt, tab_jbkp = st.tabs(["JBT · Solar  4", "JBKP · Pertalite  4"])

    # --- KONTEN TAB JBT ---
    with tab_jbt:
        f1, f2, f3, f4 = st.columns([2, 1.5, 1.5, 1.5])
        with f1:
            st.text_input(
                "Cari JBT",
                placeholder="Cari plat nomor...",
                label_visibility="collapsed",
            )
        with f2:
            st.button(
                "Analisis ulang",
                use_container_width=True,
                key="btn_analisis_jbt",
            )
        with f3:
            st.button(
                "Unduh tindak lanjut (Excel)",
                use_container_width=True,
                key="btn_tindak_jbt",
            )
        with f4:
            st.button(
                "Unduh transaksi + foto (Excel)",
                type="primary",
                use_container_width=True,
                key="btn_foto_jbt",
            )

        st.markdown("### Rekap per Plat (Harian) — Solar/JBT")
        st.caption(
            "Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT."
        )

        rekap_jbt = {
            "PLAT": ["H1460UW"],
            "PERKIRAAN JENIS (DARI PLAT)": [
                "≈ Mobil penumpang [ESTIMASI PLAT]"
            ],
            "ISI": ["3×"],
            "TOTAL VS KUOTA HARIAN": [
                "81 L / 200 L (batas terlonggar)                  41%"
            ],
            "STATUS": ["🟡 Perlu Diperiksa"],
        }
        st.dataframe(
            pd.DataFrame(rekap_jbt), use_container_width=True, hide_index=True
        )

        st.markdown("### Detail Transaksi & Bukti CCTV")
        detail_jbt = {
            "BUKTI CCTV": ["[Kamera] [Galeri]", "[Kamera] [Galeri]", "[Kamera] [Galeri]"],
            "ID": ["2305873", "2305876", "2305877"],
            "WAKTU": [
                "31/08/2026, 05.45.36",
                "31/08/2026, 05.48.55",
                "31/08/2026, 05.57.51",
            ],
            "PRODUCT / NOZZLE": [
                "BIO_SOLAR (P3/H1)",
                "BIO_SOLAR (P3/H1)",
                "BIO_SOLAR (P3/H1)",
            ],
            "PLAT": ["H1460UW", "H1460UW", "H1460UW"],
            "VOLUME": ["34.35L", "17.65L", "29.42L"],
            "PERKIRAAN JENIS": [
                "≈ Mobil penumpang [ESTIMASI PLAT]",
                "≈ Mobil penumpang [ESTIMASI PLAT]",
                "≈ Mobil penumpang [ESTIMASI PLAT]",
            ],
            "STATUS": ["🟡 Perlu Diperiksa", "🟡 Perlu Diperiksa", "🟡 Perlu Diperiksa"],
            "ALASAN TEMUAN": [
                "Total harian 81.4L > jatah mobil pribadi (50L) — konfirmasi jenis",
                "Total harian 81.4L > jatah mobil pribadi (50L) — konfirmasi jenis",
                "Total harian 81.4L > jatah mobil pribadi (50L) — konfirmasi jenis",
            ],
        }
        st.dataframe(
            pd.DataFrame(detail_jbt), use_container_width=True, hide_index=True
        )

    # --- KONTEN TAB JBKP ---
    with tab_jbkp:
        jb1, jb2, jb3, jb4 = st.columns([2, 1.5, 1.5, 1.5])
        with jb1:
            st.text_input(
                "Cari JBKP",
                placeholder="Cari plat nomor...",
                label_visibility="collapsed",
            )
        with jb2:
            st.button(
                "Analisis ulang",
                use_container_width=True,
                key="btn_analisis_jbkp",
            )
        with jb3:
            st.button(
                "Unduh tindak lanjut (Excel)",
                use_container_width=True,
                key="btn_tindak_jbkp",
            )
        with jb4:
            st.button(
                "Unduh transaksi + foto (Excel)",
                type="primary",
                use_container_width=True,
                key="btn_foto_jbkp",
            )

        st.markdown("### Rekap per Plat (Harian) — Pertalite/JBKP")
        st.caption(
            "Total pengisian plat sama dalam 1 hari vs batas JBKP. Diurutkan: yang lewat kuota di atas."
        )

        rekap_jbkp = {
            "PLAT": ["H8899XX"],
            "PERKIRAAN JENIS (DARI PLAT)": ["≈ Sepeda Motor [ESTIMASI PLAT]"],
            "ISI": ["2×"],
            "TOTAL VS KUOTA HARIAN": [
                "25 L / 40 L (batas terlonggar)                    62%"
            ],
            "STATUS": ["🟢 Normal"],
        }
        st.dataframe(
            pd.DataFrame(rekap_jbkp), use_container_width=True, hide_index=True
        )

        st.markdown("### Detail Transaksi & Bukti CCTV")
        detail_jbkp = {
            "BUKTI CCTV": ["[Kamera] [Galeri]", "[Kamera] [Galeri]"],
            "ID": ["2305901", "2305905"],
            "WAKTU": ["31/08/2026, 08.12.10", "31/08/2026, 14.30.22"],
            "PRODUCT / NOZZLE": [
                "PERTALITE (P1/H2)",
                "PERTALITE (P1/H2)",
            ],
            "PLAT": ["H8899XX", "H8899XX"],
            "VOLUME": ["10.00L", "15.00L"],
            "PERKIRAAN JENIS": [
                "≈ Sepeda Motor [ESTIMASI PLAT]",
                "≈ Sepeda Motor [ESTIMASI PLAT]",
            ],
            "STATUS": ["🟢 Normal", "🟢 Normal"],
            "ALASAN TEMUAN": [
                "Dalam batas kuota harian wajar",
                "Dalam batas kuota harian wajar",
            ],
        }
        st.dataframe(
            pd.DataFrame(detail_jbkp), use_container_width=True, hide_index=True
        )
