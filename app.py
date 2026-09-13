import streamlit as np_st
import pandas as pd

# 1. Konfigurasi Halaman
np_st.set_page_config(page_title="Pertamina Way One Solution", page_icon="⛽", layout="wide")

# 2. Styling CSS Dashboard
np_st.markdown("""
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
    .card-container {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Header Utama
np_st.markdown("### ⛽ Pertamina Way One Solution - Dashboard Audit SPBU")
np_st.markdown("Schedule audits, collect evidence, and score results in a single platform.")
np_st.write("")

# 4. Navigasi Tabs
tab1, tab2, tab3, tab4, tab5 = np_st.tabs([
    "1. INPUT DATA", 
    "2. Ceklist", 
    "3. QQ Checklist", 
    "4. Eviden Temuan Ceklist", 
    "5. Report Audit"
])

# ==================== TAB 1: INPUT DATA ====================
with tab1:
    np_st.markdown("#### 📝 Form Input Data Informasi SPBU & Kegiatan Audit")

    # Data Pemetaan Lengkap Provinsi beserta Kota/Kabupaten di Indonesia
    master_wilayah = {
        "Nangroe Aceh Darussalam": [
            "Banda Aceh", "Kab. Aceh Besar", "Kab. Aceh Pidie", "Kab. Aceh Utara", "Kab. Aceh Timur",
            "Kab. Aceh Barat", "Kab. Aceh Selatan", "Kab. Bener Meriah", "Kab. Bireuen", "Kab. Gayo Lues",
            "Kab. Jeumpa", "Kab. Nagan Raya", "Kab. Pidie Jaya", "Kab. Simeulue", "Kab. Singkil",
            "Lhokseumawe", "Sabang", "Subulussalam"
        ],
        "Sumatra Utara": [
            "Medan", "Binjai", "Pematang Siantar", "Sibolga", "Tanjung Balai", "Tebing Tinggi",
            "Kab. Deli Serdang", "Kab. Angkola", "Kab. Asahan", "Kab. Batu Bara", "Kab. Dairi",
            "Kab. Humbang Hasundutan", "Kab. Labuhanbatu", "Kab. Nias", "Kab. Nias Selatan", "Kab. Padang Lawas",
            "Kab. Pakpak Bharat", "Kab. Serdang Bedagai", "Kab. Simalungun", "Kab. Tapanuli Selatan",
            "Kab. Tapanuli Tengah", "Kab. Tapanuli Utara", "Kab. Toba Samosir", "Langkat"
        ],
        "Sumatra Barat": [
            "Padang", "Bukittinggi", "Padang Panjang", "Pariaman", "Payakumbuh", "Sawahlunto", "Solok",
            "Kab. Agam", "Kab. Dharmasraya", "Kab. Lima Puluh Kota", "Kab. Padang Pariaman", "Kab. Pasaman",
            "Kab. Pasaman Barat", "Kab. Pesisir Selatan", "Kab. Sijunjung", "Kab. Solok", "Kab. Solok Selatan",
            "Kab. Tanah Datar", "Kep. Mentawai"
        ],
        "Riau": [
            "Pekanbaru", "Dumai", "Kab. Bengkalis", "Kab. Indragiri Hilir", "Kab. Indragiri Hulu",
            "Kab. Kampar", "Kab. Kuantan Singingi", "Kab. Pelalawan", "Kab. Rokan Hilir", "Kab. Rokan Hulu", "Kab. Siak"
        ],
        "Kepulauan Riau": [
            "Batam", "Tanjung Pinang", "Kab. Bintan", "Kab. Karimun", "Kab. Lingga", "Kab. Natuna", "Kab. Kepulauan Anambas"
        ],
        "Jambi": [
            "Jambi", "Sungai Penuh", "Kab. Batanghari", "Kab. Bungo", "Kab. Kerinci", "Kab. Merangin",
            "Kab. Muaro Jambi", "Kab. Sarolangun", "Kab. Tanjung Jabung Barat", "Kab. Tanjung Jabung Timur", "Kab. Tebo"
        ],
        "Bengkulu": [
            "Bengkulu", "Kab. Bengkulu Selatan", "Kab. Bengkulu Tengah", "Kab. Bengkulu Utara", "Kab. Kaur",
            "Kab. Kepahiang", "Kab. Lebong", "Kab. Muko Muko", "Kab. Rejang Lebong", "Kab. Seluma"
        ],
        "Sumatra Selatan": [
            "Palembang", "Lubuklinggau", "Pagar Alam", "Prabumulih", "Kab. Banyuasin", "Kab. Empat Lawang",
            "Kab. Lahat", "Kab. Muara Enim", "Kab. Musi Banyuasin", "Kab. Musi Rawas", "Kab. Musi Rawas Utara",
            "Kab. Ogan Ilir", "Kab. Ogan Komering Ilir", "Kab. Ogan Komering Ulu", "Kab. Ogan Komering Ulu Selatan",
            "Kab. Ogan Komering Ulu Timur", "Kab. Penukal Abab Lematang Ilir"
        ],
        "Bangka Belitung": [
            "Pangkal Pinang", "Kab. Bangka", "Kab. Bangka Barat", "Kab. Bangka Selatan", "Kab. Bangka Tengah",
            "Kab. Belitung", "Kab. Belitung Timur"
        ],
        "Lampung": [
            "Bandar Lampung", "Metro", "Kab. Lampung Barat", "Kab. Lampung Selatan", "Kab. Lampung Tengah",
            "Kab. Lampung Timur", "Kab. Lampung Utara", "Kab. Mesuji", "Kab. Pesawaran", "Kab. Pesisir Barat",
            "Kab. Pringsewu", "Kab. Tanggamus", "Kab. Tulang Bawang", "Kab. Tulang Bawang Barat", "Kab. Way Kanan"
        ],
        "DKI Jakarta": [
            "Jakarta Pusat", "Jakarta Selatan", "Jakarta Timur", "Jakarta Barat", "Jakarta Utara", "Kepulauan Seribu"
        ],
        "Banten": [
            "Serang", "Cilegon", "Tangerang", "Tangerang Selatan", "Kab. Lebak", "Kab. Pandeglang",
            "Kab. Serang", "Kab. Tangerang"
        ],
        "Jawa Barat": [
            "Bandung", "Bekasi", "Bogor", "Cimahi", "Cirebon", "Depok", "Sukabumi", "Tasikmalaya", "Banjar",
            "Kab. Bandung", "Kab. Bandung Barat", "Kab. Bekasi", "Kab. Bogor", "Kab. Ciamis", "Kab. Cianjur",
            "Kab. Cirebon", "Kab. Garut", "Kab. Indramayu", "Kab. Karawang", "Kab. Kuningan", "Kab. Majalengka",
            "Kab. Pangandaran", "Kab. Purwakarta", "Kab. Subang", "Kab. Sukabumi", "Kab. Sumedang", "Kab. Tasikmalaya"
        ],
        "Jawa Tengah": [
            "Semarang", "Surakarta", "Salatiga", "Tegal", "Pekalongan", "Magelang",
            "Kab. Semarang", "Kab. Kendal", "Kab. Demak", "Kab. Grobogan", "Kab. Kudus", 
            "Kab. Jepara", "Kab. Pati", "Kab. Rembang", "Kab. Blora", "Kab. Boyolali", 
            "Kab. Klaten", "Kab. Sukoharjo", "Kab. Wonogiri", "Kab. Karanganyar", 
            "Kab. Sragen", "Kab. Temanggung", "Kab. Wonosobo", "Kab. Banjarnegara", 
            "Kab. Kebumen", "Kab. Purworejo", "Kab. Cilacap", "Kab. Banyumas", 
            "Kab. Purbalingga", "Kab. Tegal", "Kab. Pemalang", "Kab. Pekalongan", 
            "Kab. Batang", "Kab. Brebes", "Kab. Magelang"
        ],
        "DI Yogyakarta": [
            "Yogyakarta", "Kab. Bantul", "Kab. Gunungkidul", "Kab. Kulon Progo", "Kab. Sleman"
        ],
        "Jawa Timur": [
            "Surabaya", "Malang", "Madiun", "Kediri", "Blitar", "Mojokerto", "Pasuruan", "Probolinggo", "Batu",
            "Kab. Bangkalan", "Kab. Banyuwangi", "Kab. Blitar", "Kab. Bojonegoro", "Kab. Bondowoso", "Kab. Gresik",
            "Kab. Jember", "Kab. Jombang", "Kab. Kediri", "Kab. Lamongan", "Kab. Lumajang", "Kab. Madiun",
            "Kab. Magetan", "Kab. Malang", "Kab. Mojokerto", "Kab. Nganjuk", "Kab. Ngawi", "Kab. Pacitan",
            "Kab. Pamekasan", "Kab. Pasuruan", "Kab. Ponorogo", "Kab. Probolinggo", "Kab. Sampang", "Kab. Sidoarjo",
            "Kab. Situbondo", "Kab. Sumenep", "Kab. Trenggalek", "Kab. Tuban", "Kab. Tulungagung"
        ],
        "Bali": [
            "Denpasar", "Kab. Badung", "Kab. Bangli", "Kab. Buleleng", "Kab. Gianyar", "Kab. Jembrana",
            "Kab. Karangasem", "Kab. Klungkung", "Kab. Tabanan"
        ],
        "Nusa Tenggara Barat": [
            "Mataram", "Bima", "Kab. Bima", "Kab. Dompu", "Kab. Lombok Barat", "Kab. Lombok Tengah",
            "Kab. Lombok Timur", "Kab. Lombok Utara", "Kab. Sumbawa", "Kab. Sumbawa Barat"
        ],
        "Nusa Tenggara Timur": [
            "Kupang", "Kab. Alor", "Kab. Belu", "Kab. Ende", "Kab. Flores Timur", "Kab. Lembata",
            "Kab. Malaka", "Kab. Manggarai", "Kab. Manggarai Barat", "Kab. Manggarai Timur", "Kab. Nagekeo",
            "Kab. Ngada", "Kab. Rote Ndao", "Kab. Sabu Raijua", "Kab. Sikka", "Kab. Sumba Barat",
            "Kab. Sumba Barat Daya", "Kab. Sumba Tengah", "Kab. Sumba Timur", "Kab. Timor Tengah Selatan",
            "Kab. Timor Tengah Utara"
        ],
        "Kalimantan Barat": [
            "Pontianak", "Singkawang", "Kab. Bengkayang", "Kab. Kapuas Hulu", "Kab. Kayong Utara", "Kab. Ketapang",
            "Kab. Kubu Raya", "Kab. Landak", "Kab. Melawi", "Kab. Mempawah", "Kab. Sambas", "Kab. Sanggau",
            "Kab. Sekadau", "Kab. Sintang"
        ],
        "Kalimantan Tengah": [
            "Palangka Raya", "Kab. Barito Selatan", "Kab. Barito Timur", "Kab. Barito Utara", "Kab. Gunung Mas",
            "Kab. Kapuas", "Kab. Katingan", "Kab. Kotawaringin Barat", "Kab. Kotawaringin Timur", "Kab. Lamandau",
            "Kab. Murung Raya", "Kab. Pulang Pisau", "Kab. Seruyan", "Kab. Sukamara"
        ],
        "Kalimantan Selatan": [
            "Banjarmasin", "Banjarbaru", "Kab. Balangan", "Kab. Banjar", "Kab. Barito Kuala", "Kab. Hulu Sungai Selatan",
            "Kab. Hulu Sungai Tengah", "Kab. Hulu Sungai Utara", "Kab. Kotabaru", "Kab. Tabalong", "Kab. Tanah Bumbu",
            "Kab. Tanah Laut", "Kab. Tapin"
        ],
        "Kalimantan Timur": [
            "Samarinda", "Balikpapan", "Bontang", "Kab. Berau", "Kab. Kutai Barat", "Kab. Kutai Kartanegara",
            "Kab. Kutai Timur", "Kab. Mahakam Ulu", "Kab. Paser", "Kab. Penajam Paser Utara"
        ],
        "Kalimantan Utara": [
            "Tarakan", "Kab. Bulungan", "Kab. Malinau", "Kab. Nunukan", "Kab. Tana Tidung"
        ],
        "Sulawesi Utara": [
            "Manado", "Bitung", "Tomohon", "Kotamobagu", "Kab. Bolaang Mongondow", "Kab. Bolaang Mongondow Selatan",
            "Kab. Bolaang Mongondow Timur", "Kab. Bolaang Mongondow Utara", "Kab. Kepulauan Sangihe", "Kab. Kepulauan Siau Tagulandang Biaro",
            "Kab. Kepulauan Talaud", "Kab. Minahasa", "Kab. Minahasa Selatan", "Kab. Minahasa Tenggara", "Kab. Minahasa Utara"
        ],
        "Gorontalo": [
            "Gorontalo", "Kab. Boalemo", "Kab. Bone Bolango", "Kab. Gorontalo", "Kab. Gorontalo Utara", "Kab. Pohuwato"
        ],
        "Sulawesi Tengah": [
            "Palu", "Kab. Banggai", "Kab. Banggai Kepulauan", "Kab. Banggai Laut", "Kab. Buol", "Kab. Donggala",
            "Kab. Morowali", "Kab. Morowali Utara", "Kab. Parigi Moutong", "Kab. Poso", "Kab. Sigi", "Kab. Tojo Una-Una", "Kab. Toli-Toli"
        ],
        "Sulawesi Barat": [
            "Kab. Majene", "Kab. Mamasa", "Kab. Mamuju", "Kab. Mamuju Tengah", "Kab. Pasangkayu", "Kab. Polewali Mandar"
        ],
        "Sulawesi Selatan": [
            "Makassar", "Palopo", "Parepare", "Kab. Bantaeng", "Kab. Barru", "Kab. Bone", "Kab. Bulukumba",
            "Kab. Enrekang", "Kab. Gowa", "Kab. Jeneponto", "Kab. Kepulauan Selayar", "Kab. Luwu", "Kab. Luwu Timur",
            "Kab. Luwu Utara", "Kab. Maros", "Kab. Pangkajene dan Kepulauan", "Kab. Pinrang", "Kab. Sidenreng Rappang",
            "Kab. Sinjai", "Kab. Soppeng", "Kab. Takalar", "Kab. Tana Toraja", "Kab. Toraja Utara", "Kab. Wajo"
        ],
        "Sulawesi Tenggara": [
            "Kendari", "Bau-Bau", "Kab. Bombana", "Kab. Buton", "Kab. Buton Selatan", "Kab. Buton Tengah",
            "Kab. Buton Utara", "Kab. Kolaka", "Kab. Kolaka Timur", "Kab. Kolaka Utara", "Kab. Konawe",
            "Kab. Konawe Kepulauan", "Kab. Konawe Selatan", "Kab. Konawe Utara", "Kab. Muna", "Kab. Muna Barat", "Kab. Wakatobi"
        ],
        "Maluku Utara": [
            "Ternate", "Tidore Kepulauan", "Kab. Halmahera Barat", "Kab. Halmahera Selatan", "Kab. Halmahera Tengah",
            "Kab. Halmahera Timur", "Kab. Halmahera Utara", "Kab. Kepulauan Sula", "Kab. Pulau Morotai", "Kab. Pulau Taliabu"
        ],
        "Maluku": [
            "Ambon", "Tual", "Kab. Buru", "Kab. Buru Selatan", "Kab. Kepulauan Aru", "Kab. Kepulauan Tanimbar",
            "Kab. Maluku Barat Daya", "Kab. Maluku Tengah", "Kab. Maluku Tenggara", "Kab. Seram Bagian Barat", "Kab. Seram Bagian Timur"
        ],
        "Papua": [
            "Jayapura", "Kab. Biak Numfor", "Kab. Jayapura", "Kab. Keerom", "Kab. Mamberamo Raya", "Kab. Sarmi", "Kab. Supiori", "Kab. Waropen"
        ],
        "Papua Barat": [
            "Sorong", "Kab. Fakfak", "Kab. Kaimana", "Kab. Manokwari", "Kab. Manokwari Selatan", "Kab. Maybrat",
            "Kab. Pegunungan Arfak", "Kab. Raja Ampat", "Kab. Sorong", "Kab. Sorong Selatan", "Kab. Tambrauw", "Kab. Teluk Bintuni", "Kab. Teluk Wondama"
        ],
        "Irian Jaya": [
            "Merauke", "Kab. Asmat", "Kab. Boven Digoel", "Kab. Mappi", "Kab. Merauke", "Kab. Mimika", "Kab. Nabire",
            "Kab. Nduga", "Kab. Paniai", "Kab. Pegunungan Bintang", "Kab. Puncak", "Kab. Puncak Jaya", "Kab. Tolikara",
            "Kab. Yahukimo", "Kab. Yalimo"
        ]
    }

    daftar_provinsi = list(master_wilayah.keys())

    with np_st.form("form_input_spbu_lengkap"):
        np_st.markdown("##### 📍 Informasi SPBU")
        col1, col2 = np_st.columns(2)
        with col1:
            nomor_spbu = np_st.text_input("Nomor SPBU", value="4456202")
            
            # Selectbox Provinsi
            default_prov_index = daftar_provinsi.index("Jawa Tengah") if "Jawa Tengah" in daftar_provinsi else 0
            provinsi = np_st.selectbox("Provinsi", options=daftar_provinsi, index=default_prov_index)
            
            # Selectbox Kota/Kabupaten yang otomatis terfilter berdasarkan Provinsi yang dipilih
            pilihan_kota = master_wilayah.get(provinsi, ["Kab. Temanggung"])
            default_kota_index = pilihan_kota.index("Kab. Temanggung") if "Kab. Temanggung" in pilihan_kota else 0
            kota_kabupaten = np_st.selectbox("Kota/Kabupaten", options=pilihan_kota, index=default_kota_index)

        with col2:
            alamat = np_st.text_input("Alamat", value="Pringsurat, kab. temanggung")
            tipe_kepemilikan = np_st.text_input("Tipe Kepemilikan", value="DODO")
            pra_audit = np_st.text_input("Pra Audit", value="-")

        np_st.markdown("---")
        np_st.markdown("##### 📋 Informasi Kegiatan Audit")
        col3, col4 = np_st.columns(2)
        with col3:
            tanggal_audit = np_st.date_input("Tanggal Audit")
            tipe_audit = np_st.text_input("Tipe Audit", value="TAGE1")
        with col4:
            next_audit = np_st.text_input("Next Audit", value="TAGE2")
            kelas_spbu = np_st.text_input("Kelas SPBU", value="Pasti Pas Good")

        np_st.write("")
        submitted_data = np_st.form_submit_button("💾 Simpan & Perbarui Data Audit")
        
        if submitted_data:
            np_st.success(f"Data audit untuk SPBU No. {nomor_spbu} ({kota_kabupaten}, {provinsi}) berhasil disimpan!")

# ==================== TAB 2: CEKLIST ====================
with tab2:
    np_st.markdown("#### ✔️ Daftar Checklist Pemeriksaan SPBU")
    np_st.write("Centang item pemeriksaan operasional SPBU di bawah ini:")
    
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
    
    edited_df = np_st.data_editor(df_check, use_container_width=True, hide_index=True)

# ==================== TAB 3: QQ CHECKLIST ====================
with tab3:
    np_st.markdown("#### ❓ QQ Checklist (Quisioner & Quality Control)")
    np_st.write("Evaluasi kualitas dan pertanyaan penunjang audit:")
    
    with np_st.expander("Pertanyaan 1: Apakah prosedur HSSE dijalankan sesuai standar Pertamina?"):
        np_st.radio("Pilih:", ["Ya", "Tidak", "Tidak Berlaku"], key="q1")
        np_st.text_area("Keterangan Tambahan Q1", key="note_q1")
        
    with np_st.expander("Pertanyaan 2: Apakah pengelolaan limbah dan B3 memenuhi regulasi lingkungan?"):
        np_st.radio("Pilih:", ["Ya", "Tidak", "Tidak Berlaku"], key="q2")
        np_st.text_area("Keterangan Tambahan Q2", key="note_q2")

    with np_st.expander("Pertanyaan 3: Apakah pencatatan transaksi non-tunai tertib?"):
        np_st.radio("Pilih:", ["Ya", "Tidak", "Tidak Berlaku"], key="q3")
        np_st.text_area("Keterangan Tambahan Q3", key="note_q3")
        
    np_st.button("Simpan Jawaban QQ Checklist")

# ==================== TAB 4: EVIDEN TEMUAN CEKLIST ====================
with tab4:
    np_st.markdown("#### 📁 Eviden Temuan Ceklist & Unggah Dokumen")
    np_st.write("Unggah foto atau dokumen bukti pendukung temuan audit di lapangan.")
    
    col_e1, col_e2 = np_st.columns(2)
    with col_e1:
        np_st.text_input("Nomor SPBU Terkait", placeholder="Masukkan No SPBU", value="4456202")
        np_st.selectbox("Kategori Temuan", ["Mayor", "Minor", "Observasi", "Pujian"])
    with col_e2:
        np_st.file_uploader("Unggah Bukti Foto / Dokumen Eviden", type=["png", "jpg", "jpeg", "pdf"])
        
    np_st.text_area("Deskripsi Temuan Lapangan")
    np_st.button("Unggah Eviden")

# ==================== TAB 5: REPORT AUDIT ====================
with tab5:
    np_st.markdown("#### 📊 Laporan & Ringkasan Hasil Audit SPBU")
    
    # Ringkasan Metrik
    c1, c2, c3, c4 = np_st.columns(4)
    with c1:
        np_st.markdown('<div class="metric-card"><b>Total Audit</b><br><span style="font-size:22px; color:#0f172a;">24 SPBU</span></div>', unsafe_allow_html=True)
    with c2:
        np_st.markdown('<div class="metric-card" style="border-left-color: #22c55e;"><b>Selesai</b><br><span style="font-size:22px; color:#16a34a;">15 SPBU</span></div>', unsafe_allow_html=True)
    with c3:
        np_st.markdown('<div class="metric-card" style="border-left-color: #eab308;"><b>Berlangsung</b><br><span style="font-size:22px; color:#ca8a04;">5 SPBU</span></div>', unsafe_allow_html=True)
    with c4:
        np_st.markdown('<div class="metric-card" style="border-left-color: #dc2626;"><b>Temuan Mayor</b><br><span style="font-size:22px; color:#dc2626;">2 Kasus</span></div>', unsafe_allow_html=True)
    
    np_st.write("")
    np_st.markdown("##### Tabel Rekapitulasi Laporan")
    
    df_report = pd.DataFrame({
        "No. SPBU": ["4456202", "4150201", "4450609", "4450613"],
        "Kelas SPBU": ["Pasti Pas Good", "Pasti Pas Excellent", "Pasti Pas Good", "Pasti Pas Good"],
        "Skor Audit": ["80 (Baik)", "88 (Baik)", "75 (Cukup)", "92 (Sangat Baik)"],
        "Status Laporan": ["Final", "Final", "Draft", "Final"]
    })
    
    np_st.dataframe(df_report, use_container_width=True, hide_index=True)
    
    np_st.download_button(
        label="📥 Unduh Laporan Audit (CSV)",
        data=df_report.to_csv(index=False).encode('utf-8'),
        file_name='report_audit_spbu.csv',
        mime='text/csv',
    )
