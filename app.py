import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Checklist Visit BUR SPBU", page_icon="⛽", layout="wide"
)

st.title("⛽ Checklist Visit BUR SPBU TAC 44.506.09")
st.subheader("Bawen Semarang Ambarawa")

# Data Kategori, Item, dan Keterangan Standar dari Form
checklist_data = [
    {
        "Kategori": "1. HSSE",
        "Item": "APAR APAB",
        "Kondisi": "Baik",
        "Keterangan": (
            "APAR CO2 pada area kantor tidak tersedia, Segitiga APAR/APAB tidak"
            " tersedia"
        ),
    },
    {
        "Kategori": "1. HSSE",
        "Item": "Stick cone",
        "Kondisi": "Baik",
        "Keterangan": "Tidak Standar",
    },
    {
        "Kategori": "1. HSSE",
        "Item": "Breakway",
        "Kondisi": "Baik",
        "Keterangan": "",
    },
    {
        "Kategori": "1. HSSE",
        "Item": "Island guard",
        "Kondisi": "Baik",
        "Keterangan": "",
    },
    {
        "Kategori": "1. HSSE",
        "Item": "Lain - lain (HSSE)",
        "Kondisi": "Rusak",
        "Keterangan": (
            "Belum Terpasang Impact Valve pada semua dispenser serta Emergeny"
            " Shut Down, Dutcing Belom Kedap/ Belom ditimbun pasir"
        ),
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "CCTV",
        "Kondisi": "Baik",
        "Keterangan": (
            "CCTV Tampak Belakang untuk monitoring JBT dan JBKP tidak tersedia"
        ),
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Dispenser",
        "Kondisi": "Baik",
        "Keterangan": "",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Alat Pebongkaran BBM/BBK",
        "Kondisi": "Baik",
        "Keterangan": "Selang Bongkar, Elbow dan Quick Coupling tidak tersedia",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Ember logam",
        "Kondisi": "Baik",
        "Keterangan": "Ember Tiris pembongkaran tidak terbuat dari logam",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Toilet",
        "Kondisi": "Baik",
        "Keterangan": (
            "Terdapat kerusakan pada perangkat utama berupa lantai keramik"
            " pecah dan tidak terdapat wastafel : Toilet tidak terdapat kotak"
            " (Toilet Gratis)/ sticker QR Code Pengaduan Toilet tersedia,"
            " Sicker Toilet Gratis, Toilet Pria & Wanita Kusam"
        ),
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Toilet berbayar/ Gratis",
        "Kondisi": "Ada (Gratis)",
        "Keterangan": "",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Totem",
        "Kondisi": "Rusak",
        "Keterangan": (
            "Totem belum standar serta terdapat kerusakan pada perangkat utama"
        ),
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Mushola",
        "Kondisi": "Baik",
        "Keterangan": "Terdapat Kotak Amal Mushola di area luar",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Lampu Penerangan",
        "Kondisi": "Baik",
        "Keterangan": "Lampu Lipslank Padam, Lampu penerangan SPBU Padam",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Air Angin",
        "Kondisi": "Tidak Ada",
        "Keterangan": "Tidak terdapat Fasiltas air dan angin",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Genset",
        "Kondisi": "Baik",
        "Keterangan": "Tidak terdapat kartu perawatan/ kartu inspeksi genset",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Drive way",
        "Kondisi": "Rusak",
        "Keterangan": (
            "Drive Way pada Pulau 2 Bio Solar kurang bersih Red Carpet Kusam"
        ),
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Rak LPG",
        "Kondisi": "Tidak Ada",
        "Keterangan": "Tidak terdapat Rak LPG sesuai standar Pertamina",
    },
    {
        "Kategori": "2. Sarfas",
        "Item": "Lain - lain (Sarfas)",
        "Kondisi": "Tidak Ada",
        "Keterangan": (
            "Tidak terdapat rak pelumas, Etalase Sampel Warna, Oil Spilkit"
            " belum tersedia pada semua pulau pompa"
        ),
    },
    {
        "Kategori": "3. Operator",
        "Item": "SOP",
        "Kondisi": "Baik",
        "Keterangan": (
            'SOP Pelayanan Kurang Maksimal "Masih transaksi penjualan mesin'
            ' kendaraan dalam keadaan ON {Hidup}"'
        ),
    },
    {
        "Kategori": "3. Operator",
        "Item": "Seragam",
        "Kondisi": "Baik",
        "Keterangan": "Seragam Kusam",
    },
    {
        "Kategori": "3. Operator",
        "Item": "Penampilan",
        "Kondisi": "Baik",
        "Keterangan": "Masih terdapat operator yang kurang rapi",
    },
    {
        "Kategori": "3. Operator",
        "Item": "Lain - lain (Operator)",
        "Kondisi": "Baik",
        "Keterangan": (
            "Hasil Audit Bulan Juli 2026 Certified dengan nilai sebagai"
            " berikut : Total Score 82,77, SS&S : 80,67 EQ&Q : 99,17 RF&S :"
            " 85,60 VFC : 78,00 EPO : 39,00 Next Audit DAGE 1 , Terdapat"
            " catatan yang perlu ditingkatkan"
        ),
    },
]

st.sidebar.header("Navigasi")
menu = st.sidebar.selectbox(
    "Pilih Menu", ["Lihat Checklist & Temuan", "Input Kunjungan Baru"]
)

if menu == "Lihat Checklist & Temuan":
    st.markdown("### Ringkasan Hasil Temuan Visit SPBU")
    df = pd.DataFrame(checklist_data)
    st.dataframe(df, use_container_width=True)

    st.markdown("### Catatan Penting / Monitoring Khusus:")
    st.info(
        "**SOP Penyaluran JBT & JBKP:** Hasil Monitoring Penyaluran BBM Subsidi"
        " jenis Bio Solar pada tanggal 17 Agustus 2026, SOP Penyaluran JBT"
        " hampir semua Operator Tidak Memverifikasi Ulang antara QR Code dengan"
        " Plat Nomer serta Foto Kendaraan pada tampilan di EDC sehingga"
        " terdapat perbedaan tarikan Hose Delivery dengan pengecekan CCTV..."
    )

elif menu == "Input Kunjungan Baru":
    st.markdown("### Form Input Temuan Kunjungan Baru")
    with st.form("form_visit"):
        tanggal = st.date_input("Tanggal Visit")
        petugas = st.text_input("Nama Petugas Visit")
        kategori = st.selectbox(
            "Kategori", ["1. HSSE", "2. Sarfas", "3. Operator", "4. Lain-lain"]
        )
        item = st.text_input("Nama Item Temuan")
        kondisi = st.radio("Kondisi", ["Ada / Baik", "Tidak Ada", "Rusak"])
        keterangan = st.text_area("Keterangan / Detail Temuan")

        submitted = st.form_submit_button("Simpan Data")
        if submitted:
            st.success(
                f"Data checklist untuk kategori {kategori} berhasil disimpan!"
            )
