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

# 4. Konten Ceklist Langsung (Tanpa st.tabs)
st.markdown("#### ✔️ Daftar Checklist Pemeriksaan SPBU")
st.markdown("Centang item pemeriksaan operasional SPBU di bawah ini:")

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
