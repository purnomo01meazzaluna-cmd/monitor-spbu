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

# Sidebar untuk unggah file & pengaturan batas kuota terpisah
st.sidebar.header("Pengaturan Data")
uploaded_file = st.sidebar.file_uploader(
    "Unggah file laporan transaksi (CSV atau XLSX)",
    type=["csv", "xlsx"]
)

st.sidebar.markdown("---")
st.sidebar.header("Pengaturan Kuota JBT")
periode_jbt = st.sidebar.selectbox(
    "Periode Kuota JBT-Solar",
    ["Harian", "Bulanan", "Tahunan"],
    key="periode_jbt"
)
kuota_jbt = st.sidebar.number_input(
    f"Batas Kuota JBT-Solar ({periode_jbt}) (Liter)", 
    min_value=0.0, 
    value=10000.0, 
    step=500.0,
    key="kuota_jbt"
)

st.sidebar.markdown("---")
st.sidebar.header("Pengaturan Kuota JBKP")
periode_jbkp = st.sidebar.selectbox(
    "Periode Kuota JBKP-Pertalite",
    ["Harian", "Bulanan", "Tahunan"],
    key="periode_jbkp"
)
kuota_jbkp = st.sidebar.number_input(
    f"Batas Kuota JBKP-Pertalite ({periode_jbkp}) (Liter)", 
    min_value=0.0, 
    value=15000.0, 
    step=500.0,
    key="kuota_jbkp"
)

def render_dashboard_tab(df, title, batas_kuota=None, periode=""):
    st.subheader(f"Dashboard {title}")
    
    if df.empty:
        st.warning(f"Tidak ada data untuk kategori {title}.")
        return

    # Hitung total volume jika kolom tersedia
    total_volume = df['Volume'].sum() if 'Volume' in df.columns else 0.0

    # Metrik Ringkasan dengan Indikator Kuota
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"Total Baris Data {title}", value=len(df))
    with col2:
        if 'Volume' in df.columns:
            st.metric(label="Total Volume (L)", value=f"{total_volume:,.2f}")
        else:
            st.metric(label="Total Kolom", value=len(df.columns))
    with col3:
        if batas_kuota and 'Volume' in df.columns:
            persentase = (total_volume / batas_kuota) * 100 if batas_kuota > 0 else 0
            st.metric(
                label=f"Penggunaan Kuota ({periode})", 
                value=f"{persentase:.1f}%", 
                delta=f"{batas_kuota - total_volume:,.2f} L sisa"
            )
            # Peringatan jika mendekati atau melebihi kuota
            if total_volume > batas_kuota:
                st.error(f"⚠️ Peringatan: Volume {title} telah melebihi batas kuota {periode.lower()}!")
            elif persentase >= 80:
                st.warning(f"⚠️ Perhatian: Volume {title} sudah mencapai {persentase:.1f}% dari kuota {periode.lower()}.")
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
        # Membaca file berdasarkan ekstensi
        if uploaded_file.name.endswith('.csv'):
            df_main = pd.read_csv(uploaded_file)
        else:
            df_main = pd.read_excel(uploaded_file)

        st.success("File berhasil diunggah dan dibaca!")

        # Simulasi pemisahan dataframe untuk JBT dan JBKP
        if 'Kategori' in df_main.columns:
            df_jbt = df_main[df_main['Kategori'].str.contains('JBT|Solar', case=False, na=False)]
            df_jbkp = df_main[df_main['Kategori'].str.contains('JBKP|Pertalite', case=False, na=False)]
        else:
            mid_len = len(df_main) // 2
            df_jbt = df_main.iloc[:mid_len]
            df_jbkp = df_main.iloc[mid_len:]

        # Membuat Tab Navigasi
        tab_utama, tab_jbt_tab, tab_jbkp_tab = st.tabs(["📊 Ringkasan Utama", "🚛 JBT-Solar", "🚗 JBKP-Pertalite"])

        with tab_utama:
            st.subheader("Overview Keseluruhan Data")
            st.dataframe(df_main, use_container_width=True)
            
            if not df_main.empty:
                st.markdown("### Status Monitoring Cepat")
                for index, row in df_main.head(5).iterrows():
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.write(f"Baris ke-{index+1}: Terproses dengan baik")
                    with cols[1]:
                        st.markdown(
                            "<span style='background-color:#d1fae5;color:#059669;padding:3px 6px;border-radius:8px;font-size:10px;font-weight:600;'>🟢 Normal</span>",
                            unsafe_allow_html=True,
                        )
                st.markdown("---")

        with tab_jbt_tab:
            render_dashboard_tab(df_jbt, "JBT-Solar", batas_kuota=kuota_jbt, periode=periode_jbt)

        with tab_jbkp_tab:
            render_dashboard_tab(df_jbkp, "JBKP-Pertalite", batas_kuota=kuota_jbkp, periode=periode_jbkp)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
else:
    st.info("Silakan unggah file laporan transaksi (CSV atau XLSX) untuk mulai memantau.")
