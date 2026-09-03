import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(
    page_title="Monitor Subsidi Tepat Guna - SPBU 4150201",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling to match the clean Pertamina/modern UI in screenshots
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.title("⛽ Dashboard Monitoring Transaksi Subsidi Tepat Guna")
st.markdown("**SPBU 4150201 | Semarang, Jawa Tengah**")
st.markdown("---")

# Sidebar or Top Filters
st.sidebar.header("Pengaturan Parameter")
selected_date = st.sidebar.date_input("Pilih Tanggal Analisis", datetime.now().date())

# Main Layout Tabs
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan Transaksi", "🔍 Detail Kendaraan", "⚙️ Pengaturan & Kuota"])

with tab1:
    st.subheader("Ikhtisar Harian Penyaluran BBM Subsidi")
    
    # Dummy Metric Cards for Overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Volume Terjual", value="14,250 Liter", delta="+3.2%")
    with col2:
        st.metric(label="Transaksi Pertalite", value="8,900 Liter", delta="-1.1%")
    with col3:
        st.metric(label="Transaksi Biosolar", value="5,350 Liter", delta="+5.4%")
    with col4:
        st.metric(label="Kendaraan Terlayani", value="1,420 Unit", delta="+12 Unit")

    st.markdown("### Grafik Tren Penyaluran per Jam")
    # Generate dummy chart data
    chart_data = pd.DataFrame(
        np.random.randint(20, 100, size=(24, 2)),
        columns=["Pertalite (L)", "Biosolar (L)"]
    )
    st.line_chart(chart_data)

with tab2:
    st.subheader("Pencarian & Riwayat Plat Nomor Kendaraan")
    search_query = st.text_input("Cari Plat Nomor Kendaraan (contoh: H 1234 XX):", "")
    
    # Dummy table for transactions
    data_transaksi = {
        "Waktu": ["08:15:20", "08:18:45", "08:22:10", "08:30:05"],
        "Plat Nomor": ["H 1234 AB", "K 5678 CD", "H 9999 XYZ", "B 1234 ABC"],
        "Jenis BBM": ["Pertalite", "Biosolar", "Pertalite", "Pertalite"],
        "Volume (L)": [20, 60, 15, 25],
        "Status": ["Valid", "Valid", "Perlu Diperiksa", "Valid"]
    }
    df_transaksi = pd.DataFrame(data_transaksi)
    
    if search_query:
        filtered_df = df_transaksi[df_transaksi["Plat Nomor"].str.contains(search_query, case=False, na=False)]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.dataframe(df_transaksi, use_container_width=True)

with tab3:
    st.subheader("Pengaturan Batas Kuota & Parameter Sistem")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input("Volume Wajar Maks. Motor (Liter)", value=20)
    with col2:
        st.number_input("Batas Terlonggar Pertalite (L/hari)", value=60)
    with col3:
        st.text_input("Jenis BBM Bersubsidi", value="PERTALITE, SOLAR, BIOSOLAR")

    st.markdown("---")
    st.markdown("#### Kuota Solar / Biosolar - JBT (liter/hari, per kendaraan)")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    with q_col1:
        st.number_input("Pribadi roda 4", value=60)
    with q_col2:
        st.number_input("Umum/barang roda 4", value=80)
    with q_col3:
        st.number_input("Roda 6 atau lebih", value=200)
    with q_col4:
        st.number_input("Pelayanan umum", value=50)

    st.markdown("#### Kuota Pertalite - JBKP (liter/hari, per kendaraan)")
    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.number_input("Roda 4 (pribadi/umum) - Pertalite", value=50)
    with p_col2:
        st.number_input("Pelayanan umum - Pertalite", value=50)

    st.markdown("---")
    st.markdown('**Tentang "Perkiraan Jenis" dari plat (skema nasional)**')
    st.info("1~(motor~1) mobil penumpang · [motor]~6999 sepeda motor · 7000~7999 bus · 8000~8999 mobil barang · 9000~9999 kendaraan khusus")

# Summary Warning Banner & Status
st.markdown("---")
st.markdown("🟡 `Perlu Diperiksa` - Sistem berjalan normal dan terhubung ke database SPBU 4150201.")
