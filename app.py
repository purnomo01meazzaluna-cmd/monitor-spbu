import streamlit as st
import pandas as pd

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Pertamina Way One Solution", page_icon="⛽", layout="wide")

# 2. Styling CSS Dashboard
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #0066FF;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Header Utama
st.markdown("### ⛽ Pertamina Way One Solution - Dashboard Audit SPBU")
st.markdown("Schedule audits, collect evidence, and score results in a single platform.")
st.write("")

# 4. Navigasi Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. INPUT DATA", 
    "2. Ceklist", 
    "3. QQ Checklist", 
    "4. Eviden Temuan Ceklist", 
    "5. Report Audit"
])

# ==================== DATA KOTA/KABUPATEN ====================
daftar_kota_kabupaten = [
    "Semarang", "Kab. Semarang", "Surakarta", "Salatiga", "Tegal", "Pekalongan", "Magelang",
    "Kab. Temanggung", "Kab. Kendal", "Kab. Demak", "Kab. Grobogan", "Kab. Kudus", "Kab. Jepara",
    "Kab. Pati", "Kab. Boyolali", "Kab. Klaten", "Kab. Sukoharjo", "Kab. Wonogiri", "Kab. Karanganyar",
    "Kab. Sragen", "Kab. Wonosobo", "Kab. Banjarnegara", "Kab. Kebumen", "Kab. Purworejo", "Kab. Cilacap",
    "Kab. Banyumas", "Kab. Purbalingga", "Kab. Pemalang", "Kab. Batang", "Kab. Brebes",
    "Jakarta Pusat", "Jakarta Selatan", "Jakarta Timur", "Jakarta Barat", "Jakarta Utara", "Kepulauan Seribu",
    "Bandung", "Bekasi", "Bogor", "Cimahi", "Cirebon", "Depok", "Sukabumi", "Tasikmalaya", "Banjar",
    "Kab. Bandung", "Kab. Bandung Barat", "Kab. Bekasi", "Kab. Bogor", "Kab. Ciamis", "Kab. Cianjur",
    "Kab. Cirebon", "Kab. Garut", "Kab. Indramayu", "Kab. Karawang", "Kab. Kuningan", "Kab. Majalengka",
    "Kab. Pangandaran", "Kab. Purwakarta", "Kab. Subang", "Kab. Sukabumi", "Kab. Sumedang", "Kab. Tasikmalaya",
    "Surabaya", "Malang", "Madiun", "Kediri", "Blitar", "Mojokerto", "Pasuruan", "Probolinggo", "Batu",
    "Kab. Bangkalan", "Kab. Banyuwangi", "Kab. Blitar", "Kab. Bojonegoro", "Kab. Bondowoso", "Kab. Gresik",
    "Kab. Jember", "Kab. Jombang", "Kab. Kediri", "Kab. Lamongan", "Kab. Lumajang", "Kab. Madiun",
    "Kab. Magetan", "Kab. Malang", "Kab. Mojokerto", "Kab. Nganjuk", "Kab. Ngawi", "Kab. Pacitan",
    "Kab. Pamekasan", "Kab. Pasuruan", "Kab. Ponorogo", "Kab. Probolinggo", "Kab. Sampang", "Kab. Sidoarjo",
    "Kab. Situbondo", "Kab. Sumenep", "Kab. Trenggalek", "Kab. Tuban", "Kab. Tulungagung",
    "Yogyakarta", "Kab. Bantul", "Kab. Gunungkidul", "Kab. Kulon Progo", "Kab. Sleman",
    "Serang", "Cilegon", "Tangerang", "Tangerang Selatan", "Kab. Lebak", "Kab. Pandeglang",
    "Kab. Serang", "Kab. Tangerang"
]

# ==================== TAB 1: INPUT DATA ====================
with tab1:
    st.markdown("#### 📝 Form Input Data Informasi SPBU & Kegiatan Audit")

    st.markdown("##### 📍 Informasi SPBU")
    col1, col2 = st.columns(2)
    
    with col1:
        nomor_spbu = st.text_input("Nomor SPBU", placeholder="Masukkan No SPBU", key="input_no_spbu_baru")
        
        # Selectbox Kota/Kabupaten Langsung tanpa Provinsi
        kota_kabupaten_pilihan = st.selectbox(
            "Kota/Kabupaten", 
            options=daftar_kota_kabupaten, 
            key="select_kota_kabupaten_baru"
        )

    with col2:
        alamat = st.text_input("Alamat", placeholder="Masukkan alamat lengkap SPBU", key="input_alamat_baru")
        tipe_kepemilikan = st.text_input("Tipe Kepemilikan", placeholder="Contoh: DODO / CODO", key="input_tipe_kepemilikan_baru")
        pra_audit = st.text_input("Pra Audit", placeholder="-", key="input_pra_audit_baru")

    st.markdown("---")
    st.markdown("##### 📋 Informasi Kegiatan Audit")
    col3, col4 = st.columns(2)
    with col3:
        tanggal_audit = st.date_input("Tanggal Audit", key="date_audit_baru")
        tipe_audit = st.text_input("Tipe Audit", placeholder="Contoh: TAGE1", key="input_tipe_audit_baru")
    with col4:
        next_audit = st.text_input("Next Audit", placeholder="Contoh: TAGE2", key="input_next_audit_baru")
        kelas_spbu = st.text_input("Kelas SPBU", placeholder="Contoh: Pasti Pas Good", key="input_kelas_spbu_baru")

    st.write("")
    submitted_data = st.button("💾 Simpan & Perbarui Data Audit", key="btn_simpan_audit_baru")
    
    if submitted_data:
        st.success(f"Data audit untuk SPBU No. {nomor_spbu} ({kota_kabupaten_pilihan}) berhasil disimpan!")

# ==================== TAB 2: CEKLIST ====================
with tab2:
    st.markdown("#### ✔️ Daftar Checklist Pemeriksaan SPBU")
    checklist_data = {
        "Kategori": ["HSSE", "HSSE", "NFR (Non-Fuel Retail)", "Operasional", "Operasional"],
        "Item Pemeriksaan": [
            "Ketersediaan Alat Pemadam Api Ringan (APAR) yang masih aktif",
            "Penggunaan Alat Pelindung Diri (APD) lengkap oleh operator",
            "Kebersihan area fasilitas toilet dan minimarket",
            "Peneraan/kalibrasi Nozel Dispenser BBM akurat",
            "Ketersediaan papan informasi harga BBM yang jelas"
        ],
        "Status": [True, False, True, True, False]
    }
    df_check = pd.DataFrame(checklist_data)
    st.data_editor(df_check, use_container_width=True, hide_index=True, key="editor_checklist_baru")

# ==================== TAB 3: QQ CHECKLIST ====================
with tab3:
    st.markdown("#### ❓ QQ Checklist (Quisioner & Quality Control)")
    with st.expander("Pertanyaan 1: Apakah prosedur HSSE dijalankan sesuai standar Pertamina?"):
        st.radio("Pilih:", ["Ya", "Tidak", "Tidak Berlaku"], key="qq_q1_baru")
        st.text_area("Keterangan Tambahan Q1", key="qq_note_q1_baru")
        
    with st.expander("Pertanyaan 2: Apakah pengelolaan limbah dan B3 memenuhi regulasi lingkungan?"):
        st.radio("Pilih:", ["Ya", "Tidak", "Tidak Berlaku"], key="qq_q2_baru")
        st.text_area("Keterangan Tambahan Q2", key="qq_note_q2_baru")

    with st.expander("Pertanyaan 3: Apakah pencatatan transaksi non-tunai tertib?"):
        st.radio("Pilih:", ["Ya", "Tidak", "Tidak Berlaku"], key="qq_q3_baru")
        st.text_area("Keterangan Tambahan Q3", key="qq_note_q3_baru")
        
    st.button("Simpan Jawaban QQ Checklist", key="btn_simpan_qq_baru")

# ==================== TAB 4: EVIDEN TEMUAN CEKLIST ====================
with tab4:
    st.markdown("#### 📁 Eviden Temuan Ceklist & Unggah Dokumen")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.text_input("Nomor SPBU Terkait", placeholder="Masukkan No SPBU", key="ev_no_spbu_baru")
        st.selectbox("Kategori Temuan", ["Mayor", "Minor", "Observasi", "Pujian"], key="ev_kategori_baru")
    with col_e2:
        st.file_uploader("Unggah Bukti Foto / Dokumen Eviden", type=["png", "jpg", "jpeg", "pdf"], key="ev_file_baru")
        
    st.text_input("Deskripsi Temuan Lapangan", key="ev_deskripsi_baru")
    st.button("Unggah Eviden", key="btn_upload_eviden_baru")

# ==================== TAB 5: REPORT AUDIT ====================
with tab5:
    st.markdown("#### 📊 Laporan & Ringkasan Hasil Audit SPBU")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="metric-card"><b>Total Audit</b><br><span style="font-size:22px; color:#0f172a;">24 SPBU</span></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card" style="border-left-color: #22c55e;"><b>Selesai</b><br><span style="font-size:22px; color:#16a34a;">15 SPBU</span></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card" style="border-left-color: #eab308;"><b>Berlangsung</b><br><span style="font-size:22px; color:#ca8a04;">5 SPBU</span></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="metric-card" style="border-left-color: #dc2626;"><b>Temuan Mayor</b><br><span style="font-size:22px; color:#dc2626;">2 Kasus</span></div>', unsafe_allow_html=True)
    
    st.write("")
    st.markdown("##### Tabel Rekapitulasi Laporan")
    df_report = pd.DataFrame({
        "No. SPBU": ["4456202", "4150201", "4450609", "4450613"],
        "Kelas SPBU": ["Pasti Pas Good", "Pasti Pas Excellent", "Pasti Pas Good", "Pasti Pas Good"],
        "Skor Audit": ["80 (Baik)", "88 (Baik)", "75 (Cukup)", "92 (Sangat Baik)"],
        "Status Laporan": ["Final", "Final", "Draft", "Final"]
    })
    st.dataframe(df_report, use_container_width=True, hide_index=True)
    st.download_button(
        label="📥 Unduh Laporan Audit (CSV)",
        data=df_report.to_csv(index=False).encode('utf-8'),
        file_name='report_audit_spbu.csv',
        mime='text/csv',
        key="btn_download_report_baru"
    )
