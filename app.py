import pandas as pd
import streamlit as st

# Konfigurasi Halaman
st.set_page_config(
    page_title="Dashboard Monitoring SPBU",
    page_icon="⛽",
    layout="wide"
)

st.title("⛽ Dashboard Monitoring Transaksi & Operasional SPBU")
st.markdown("---")

# Sidebar untuk unggah file & pengaturan batas kuota
st.sidebar.header("Pengaturan Data")
uploaded_file = st.sidebar.file_uploader(
    "Unggah file laporan transaksi (CSV atau XLSX)",
    type=["csv", "xlsx"]
)

st.sidebar.markdown("---")
st.sidebar.header("Pengaturan Kuota & Kategori")

pilihan_kategori = st.sidebar.selectbox(
    "Pilih Kategori Produk",
    ["JBT-Solar", "JBKP-Pertalite"]
)

# Definisi rentang sub-kategori berdasarkan aturan yang diberikan
sub_kategori_rules = {
    "JBT-Solar": [
        {"nama": "1. 1000-2999 R4 Pribadi", "min": 1000, "max": 2999},
        {"nama": "2. 3000-6999 R2 SPM", "min": 3000, "max": 6999},
        {"nama": "3. 7000-7999 R4 Umum Bus", "min": 7000, "max": 7999},
        {"nama": "4. 8000-8999 R4> B Truck Barang", "min": 8000, "max": 8999},
        {"nama": "5. 9000-9999 R4> Truck Khusus", "min": 9000, "max": 9999},
    ],
    "JBKP-Pertalite": [
        {"nama": "1. 1000-2999 R4 Pribadi", "min": 1000, "max": 2999},
        {"nama": "2. 3000-6999 R2 SPM", "min": 3000, "max": 6999},
        {"nama": "3. 7000-7999 R4 Umum Bus", "min": 7000, "max": 7999},
        {"nama": "4. 8000-8999 R4 B Pick Up Barang", "min": 8000, "max": 8999},
        {"nama": "5. 9000-9999 R4p Pickup Barang", "min": 9000, "max": 9999},
    ]
}

# Pilihan sub-kategori spesifik berdasarkan kategori utama yang dipilih
current_rules = sub_kategori_rules[pilihan_kategori]
pilihan_sub_kategori = st.sidebar.selectbox(
    "Pilih Sub-Kategori / Rentang Nomor",
    [rule["nama"] for rule in current_rules]
)

# Dapatkan rentang min & max dari pilihan sub-kategori aktif
selected_rule = next(rule for rule in current_rules if rule["nama"] == pilihan_sub_kategori)

# Inisialisasi session state bertingkat (Kategori -> Sub-Kategori)
if 'pengaturan_kuota' not in st.session_state:
    st.session_state.pengaturan_kuota = {}

if pilihan_kategori not in st.session_state.pengaturan_kuota:
    st.session_state.pengaturan_kuota[pilihan_kategori] = {}

if pilihan_sub_kategori not in st.session_state.pengaturan_kuota[pilihan_kategori]:
    # Default kuota awal jika belum diatur (misal: 10000 untuk JBT, 15000 untuk JBKP)
    default_val = 10000.0 if pilihan_kategori == "JBT-Solar" else 15000.0
    st.session_state.pengaturan_kuota[pilihan_kategori][pilihan_sub_kategori] = default_val

current_saved_quota = st.session_state.pengaturan_kuota[pilihan_kategori][pilihan_sub_kategori]

# Input batas kuota spesifik untuk sub-kategori yang sedang dipilih
batas_kuota = st.sidebar.number_input(
    f"Batas Kuota (Liter)", 
    min_value=0.0, 
    value=current_saved_quota, 
    step=500.0,
    key=f"input_{pilihan_kategori}_{pilihan_sub_kategori}"
)

# Simpan kembali ke session state
st.session_state.pengaturan_kuota[pilihan_kategori][pilihan_sub_kategori] = batas_kuota

def render_dashboard_tab(df, title, batas_kuota=None):
    st.subheader(f"Dashboard {title}")
    
    if df.empty:
        st.warning(f"Tidak ada data untuk sub-kategori {title}.")
        return

    total_volume = df['Volume'].sum() if 'Volume' in df.columns else 0.0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"Total Baris Data", value=len(df))
    with col2:
        if 'Volume' in df.columns:
            st.metric(label="Total Volume (L)", value=f"{total_volume:,.2f}")
        else:
            st.metric(label="Total Kolom", value=len(df.columns))
    with col3:
        if batas_kuota is not None and 'Volume' in df.columns:
            persentase = (total_volume / batas_kuota) * 100 if batas_kuota > 0 else 0
            st.metric(
                label="Penggunaan Kuota", 
                value=f"{persentase:.1f}%", 
                delta=f"{batas_kuota - total_volume:,.2f} L sisa"
            )
            if total_volume > batas_kuota:
                st.error(f"⚠️ Peringatan: Volume telah melebihi batas kuota sub-kategori!")
            elif persentase >= 80:
                st.warning(f"⚠️ Perhatian: Volume sudah mencapai {persentase:.1f}% dari kuota sub-kategori.")
        else:
            if 'Total_Harga' in df.columns:
                total_harga = df['Total_Harga'].sum()
                st.metric(label="Total Pendapatan (Rp)", value=f"Rp {total_harga:,.0f}")
            else:
                st.metric(label="Status", value="Aktif")

    st.markdown("---")
    st.dataframe(df, use_container_width=True)

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_main = pd.read_csv(uploaded_file)
        else:
            df_main = pd.read_excel(uploaded_file)

        st.success("File berhasil diunggah dan dibaca!")

        if 'Kategori' in df_main.columns:
            df_jbt = df_main[df_main['Kategori'].str.contains('JBT|Solar', case=False, na=False)]
            df_jbkp = df_main[df_main['Kategori'].str.contains('JBKP|Pertalite', case=False, na=False)]
        else:
            mid_len = len(df_main) // 2
            df_jbt = df_main.iloc[:mid_len]
            df_jbkp = df_main.iloc[mid_len:]

        tab_jbt_tab, tab_jbkp_tab = st.tabs(["🚛 JBT-Solar", "🚗 JBKP-Pertalite"])

        with tab_jbt_tab:
            sub_df_jbt = df_jbt
            if 'Nomor' in df_jbt.columns:
                sub_df_jbt = df_jbt[(df_jbt['Nomor'] >= selected_rule["min"]) & (df_jbt['Nomor'] <= selected_rule["max"])]
            
            # Ambil kuota spesifik JBT untuk sub-kategori aktif
            active_quota_jbt = st.session_state.pengaturan_kuota["JBT-Solar"].get(pilihan_sub_kategori, 10000.0)
            render_dashboard_tab(sub_df_jbt, f"JBT-Solar ({pilihan_sub_kategori})", batas_kuota=active_quota_jbt)

        with tab_jbkp_tab:
            sub_df_jbkp = df_jbkp
            if 'Nomor' in df_jbkp.columns:
                sub_df_jbkp = df_jbkp[(df_jbkp['Nomor'] >= selected_rule["min"]) & (df_jbkp['Nomor'] <= selected_rule["max"])]
            
            # Ambil kuota spesifik JBKP untuk sub-kategori aktif
            active_quota_jbkp = st.session_state.pengaturan_kuota["JBKP-Pertalite"].get(pilihan_sub_kategori, 15000.0)
            render_dashboard_tab(sub_df_jbkp, f"JBKP-Pertalite ({pilihan_sub_kategori})", batas_kuota=active_quota_jbkp)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
else:
    st.info("Silakan unggah file laporan transaksi (CSV atau XLSX) untuk mulai memantau.")
