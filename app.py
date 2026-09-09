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

# Definisi rentang sub-kategori dengan pembaruan nama dan ikon
sub_kategori_rules = {
    "JBT-Solar": [
        {"nama": "🚗 1000-2999 R4 Pribadi", "min": 1000, "max": 2999},
        {"nama": "🏍️ 3000-6999 Sepeda Motor", "min": 3000, "max": 6999},
        {"nama": "🚌 7000-7999 Minibus/ Bus", "min": 7000, "max": 7999},
        {"nama": "🚚 8000-8999 Truck", "min": 8000, "max": 8999},
        {"nama": "🚛 9000-9999 Truck Trailer", "min": 9000, "max": 9999},
    ],
    "JBKP-Pertalite": [
        {"nama": "🚗 1000-2999 R4 Pribadi", "min": 1000, "max": 2999},
        {"nama": "🏍️ 3000-6999 Sepeda Motor", "min": 3000, "max": 6999},
        {"nama": "🚌 7000-7999 Minibus/ Bus", "min": 7000, "max": 7999},
        {"nama": "🚚 8000-8999 Truck", "min": 8000, "max": 8999},
        {"nama": "🚛 9000-9999 Truck Trailer", "min": 9000, "max": 9999},
    ]
}

current_rules = sub_kategori_rules[pilihan_kategori]

# Inisialisasi session state untuk menyimpan kuota per sub-kategori
if 'pengaturan_kuota' not in st.session_state or not isinstance(st.session_state.pengaturan_kuota, dict):
    st.session_state.pengaturan_kuota = {}

if pilihan_kategori not in st.session_state.pengaturan_kuota or not isinstance(st.session_state.pengaturan_kuota[pilihan_kategori], dict):
    st.session_state.pengaturan_kuota[pilihan_kategori] = {}

# Render input batas kuota langsung untuk semua sub-kategori dalam kategori aktif (max_value=200.0)
st.sidebar.markdown("### Batas Kuota (Liter)")
kuota_per_sub = {}

for rule in current_rules:
    nama_sub = rule["nama"]
    default_val = 200.0
    
    if nama_sub not in st.session_state.pengaturan_kuota[pilihan_kategori]:
        st.session_state.pengaturan_kuota[pilihan_kategori][nama_sub] = default_val
        
    current_saved_quota = st.session_state.pengaturan_kuota[pilihan_kategori][nama_sub]
    if current_saved_quota > 200.0:
        current_saved_quota = 200.0
    
    kuota_per_sub[nama_sub] = st.sidebar.number_input(
        f"{nama_sub}", 
        min_value=0.0, 
        max_value=200.0,
        value=current_saved_quota, 
        step=10.0,
        key=f"input_{pilihan_kategori}_{nama_sub}"
    )
    st.session_state.pengaturan_kuota[pilihan_kategori][nama_sub] = kuota_per_sub[nama_sub]

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

        # Buat sub-tab untuk masing-masing sub-kategori di dalam kategori utama
        sub_tab_names = [rule["nama"] for rule in current_rules]
        
        if pilihan_kategori == "JBT-Solar":
            sub_tabs = st.tabs(sub_tab_names)
            for idx, rule in enumerate(current_rules):
                with sub_tabs[idx]:
                    sub_df = df_jbt
                    if 'Nomor' in df_jbt.columns:
                        sub_df = df_jbt[(df_jbt['Nomor'] >= rule["min"]) & (df_jbt['Nomor'] <= rule["max"])]
                    active_quota = st.session_state.pengaturan_kuota["JBT-Solar"].get(rule["nama"], 200.0)
                    render_dashboard_tab(sub_df, f"JBT-Solar ({rule['nama']})", batas_kuota=active_quota)
        else:
            sub_tabs = st.tabs(sub_tab_names)
            for idx, rule in enumerate(current_rules):
                with sub_tabs[idx]:
                    sub_df = df_jbkp
                    if 'Nomor' in df_jbkp.columns:
                        sub_df = df_jbkp[(df_jbkp['Nomor'] >= rule["min"]) & (df_jbkp['Nomor'] <= rule["max"])]
                    active_quota = st.session_state.pengaturan_kuota["JBKP-Pertalite"].get(rule["nama"], 200.0)
                    render_dashboard_tab(sub_df, f"JBKP-Pertalite ({rule['nama']})", batas_kuota=active_quota)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
else:
    st.info("Silakan unggah file laporan transaksi (CSV atau XLSX) untuk mulai memantau.")
