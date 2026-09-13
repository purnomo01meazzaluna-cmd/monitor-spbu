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

# 4. Navigasi Tabs (Hanya 4 tab tanpa Tab Input Data)
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Ceklist", 
    "2. QQ Checklist", 
    "3. Eviden Temuan Ceklist", 
    "4. Report Audit"
])

# ==================== TAB 1: CEKLIST ====================
with tab1:
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

# ==================== TAB 2: QQ CHECKLIST ====================
with tab2:
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

# ==================== TAB 3: EVIDEN TEMUAN CEKLIST ====================
with tab3:
    st.markdown("#### 📁 Eviden Temuan Ceklist & Unggah Dokumen")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.text_input("Nomor SPBU Terkait", placeholder="Masukkan No SPBU", key="ev_no_spbu_baru")
        st.selectbox("Kategori Temuan", ["Mayor", "Minor", "Observasi", "Pujian"], key="ev_kategori_baru")
    with col_e2:
        st.file_uploader("Unggah Bukti Foto / Dokumen Eviden", type=["png", "jpg", "jpeg", "pdf"], key="ev_file_baru")
        
    st.text_input("Deskripsi Temuan Lapangan", key="ev_deskripsi_baru")
    st.button("Unggah Eviden", key="btn_upload_eviden_baru")

# ==================== TAB 4: REPORT AUDIT ====================
with tab4:
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
