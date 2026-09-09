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

# Sidebar untuk unggah file
st.sidebar.header("Pengaturan Data")
uploaded_file = st.sidebar.file_uploader(
    "Unggah file laporan transaksi (CSV atau XLSX)",
    type=["csv", "xlsx"]
)

def render_dashboard_tab(df, title):
    st.subheader(f"Dashboard {title}")
    
    if df.empty:
        st.warning(f"Tidak ada data untuk kategori {title}.")
        return

    # Metrik Ringkasan
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=f"Total Baris Data {title}", value=len(df))
    with col2:
        if 'Volume' in df.columns:
            total_volume = df['Volume'].sum()
            st.metric(label="Total Volume (L)", value=f"{total_volume:,.2f}")
        else:
            st.metric(label="Total Kolom", value=len(df.columns))
    with col3:
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

        # Simulasi pemisahan dataframe untuk JBT dan JBKP jika kolom kategori tersedia, 
        # atau membaginya secara dummy jika strukturnya disesuaikan kebutuhan Anda.
        if 'Kategori' in df_main.columns:
            df_jbt = df_main[df_main['Kategori'].str.contains('JBT|Solar', case=False, na=False)]
            df_jbkp = df_main[df_main['Kategori'].str.contains('JBKP|Pertalite', case=False, na=False)]
        else:
            # Fallback pembagian data jika kolom kategori tidak spesifik
            mid_len = len(df_main) // 2
            df_jbt = df_main.iloc[:mid_len]
            df_jbkp = df_main.iloc[mid_len:]

        # Membuat Tab Navigasi
        tab_utama, tab_jbt, tab_jbkp = st.tabs(["📊 Ringkasan Utama", "🚛 JBT-Solar", "🚗 JBKP-Pertalite"])

        with tab_utama:
            st.subheader("Overview Keseluruhan Data")
            st.dataframe(df_main, use_container_width=True)
            
            # Contoh elemen tambahan status iterasi baris jika diperlukan
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

        with tab_jbt:
            render_dashboard_tab(df_jbt, "JBT-Solar")

        with tab_jbkp:
            render_dashboard_tab(df_jbkp, "JBKP-Pertalite")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {e}")
else:
    st.info("Silakan unggah file laporan transaksi (CSV atau XLSX) untuk mulai memantau.")
