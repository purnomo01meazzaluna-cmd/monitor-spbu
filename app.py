import streamlit as st
import pandas as pd
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU 4150201",
    page_icon="⛽",
    layout="wide"
)

# Styling CSS tambahan agar tampilan tabel & kartu lebih rapi
st.markdown("""
    <style>
    .metric-card-top {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigasi
st.sidebar.markdown("### ⛽ Panel SPBU 4150201")
st.sidebar.markdown("Semarang", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navigasi", 
    ["Dashboard & Identifikasi", "Stok Tangki", "Delivery Order", "Laporan Harian"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📁 Tarikan / Upload Data")
uploaded_file = st.sidebar.file_uploader("Pilih file laporan transaksi (CSV/Excel)", type=["csv", "xlsx"])

# Fungsi untuk memproses data transaksi dan otomatis menambahkan kolom Noted
def process_transaction_data(df):
    # Pastikan kolom standar tersedia (sesuaikan dengan format data Anda jika berbeda)
    expected_cols = ['No. Transaksi', 'Waktu', 'Nozzle', 'Plat Nomor', 'Volume', 'Golongan']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = "-"
            
    # Buat logika otomatis untuk mengisi kolom 'Noted' berdasarkan hasil identifikasi
    def generate_note(row):
        notes = []
        # Contoh kondisi: jika volume harian/transaksi mencurigakan atau jeda cepat
        vol = float(str(row.get('Volume', 0)).replace('L', '').strip() or 0)
        golongan = str(row.get('Golongan', ''))
        
        if "Pribadi" in golongan and vol > 60:
            notes.append("Melebihi Batas Kuota Golongan")
        elif "Jeda Cepat" in str(row.get('Status', '')):
            notes.append("Jeda Pengisian Terlalu Cepat")
            
        return " | ".join(notes) if notes else "Sesuai / Normal"

    df['Noted'] = df.apply(generate_note, axis=1)
    return df

# Konten Utama Berdasarkan Menu
if menu == "Dashboard & Identifikasi":
    st.title("📊 Dashboard Monitoring & Identifikasi Transaksi")
    st.write("Deteksi otomatis rentang plat nomor, kuota spesifik, dan peringatan jeda waktu antar pengisian.")
    
    # Simulasi data jika file belum di-upload, atau gunakan data dari file user
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_trx = pd.read_csv(uploaded_file)
            else:
                df_trx = pd.read_excel(uploaded_file)
            df_trx = process_transaction_data(df_trx)
            st.success("Data berhasil dimuat!")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses file: {e}")
            df_trx = pd.DataFrame()
    else:
        # Data dummy untuk contoh tampilan tabel jika belum upload file
        df_trx = pd.DataFrame({
            "No. Transaksi": ["2305873", "2305876", "2305880"],
            "Waktu": ["05:45:48", "05:48:08", "06:12:15"],
            "Nozzle": ["3 / 1 / BIO_SOLAR", "3 / 1 / BIO_SOLAR", "2 / 1 / PERTALITE"],
            "Plat Nomor": ["H1460UW", "H1460UW", "H9921AB"],
            "Volume": ["34.35L", "17.65L", "20.00L"],
            "Golongan": ["R4 Pribadi / Umum", "R4 Pribadi / Umum", "R4 Pribadi / Umum"],
            "Status Peringatan": ["Perlu Diperiksa", "Jeda Cepat", "Normal"]
        })
        df_trx = process_transaction_data(df_trx)

    st.subheader("Rekapitulasi Berdasarkan Golongan Plat & Rentang Waktu")
    
    # Menggunakan st.data_editor agar kolom 'Noted' bisa diketik manual/di-update langsung jika diperlukan, 
    # atau st.dataframe jika hanya ingin dibaca.
    edited_df = st.data_editor(
        df_trx,
        column_config={
            "Noted": st.column_config.TextColumn(
                "Noted / Catatan Investigasi",
                help="Masukkan atau ubah catatan hasil verifikasi plat nomor di sini",
                max_chars=250,
                required=False,
            )
        },
        hide_index=True,
        use_container_width=True,
        key="table_editor_spbu"
    )

elif menu == "Stok Tangki":
    st.title("🛢️ Monitoring Stok Tangki Timbun")
    tank_data = pd.DataFrame({
        "No. Tangki": [1, 2, 3, 4],
        "Produk": ["Pertamax", "Pertalite", "Bio Solar", "Pertamina Dex"],
        "Kapasitas Maks (L)": [30000, 45000, 40000, 20000],
        "Stok Saat Ini (L)": [18500, 32000, 24000, 14500],
        "Status": ["Aman", "Aman", "Perhatian", "Aman"]
    })
    st.table(tank_data)

elif menu == "Delivery Order":
    st.title("🚚 Delivery Order (DO) & Penebusan BBM")
    do_data = pd.DataFrame({
        "No. DO": ["DO-889102", "DO-889103"],
        "Tanggal": ["2026-09-08", "2026-09-09"],
        "Produk": ["Pertalite", "Bio Solar"],
        "Volume (L)": [8000, 16000],
        "Status": ["Selesai", "Dalam Perjalanan"]
    })
    st.dataframe(do_data, use_container_width=True)

elif menu == "Laporan Harian":
    st.title("📝 Laporan Harian & Shift Operator")
    with st.form("form_laporan"):
        tanggal_laporan = st.date_input("Tanggal Laporan", datetime.now())
        shift = st.selectbox("Pilih Shift", ["Shift 1 (07:00 - 15:00)", "Shift 2 (15:00 - 23:00)", "Shift 3 (23:00 - 07:00)"])
        catatan_shift = st.text_area("Catatan Operasional / Kendala Dispenser / HSSE")
        submitted = st.form_submit_button("Simpan Laporan")
        
    if submitted:
        st.success(f"Laporan untuk tanggal {tanggal_laporan} ({shift}) berhasil disimpan!")
