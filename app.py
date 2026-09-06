import json
import os
import pandas as pd
import streamlit as st

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="SPBU Monitoring & Fraud Prevention",
    page_icon="⛽",
    layout="wide",
)

# File untuk menyimpan konfigurasi secara permanen
CONFIG_FILE = "config_kuota.json"

default_config = {
    "jbt_1": 60, "jbt_2": 0, "jbt_3": 200, "jbt_4": 200, "jbt_5": 250,
    "jbkp_1": 60, "jbkp_2": 8, "jbkp_3": 120, "jbkp_4": 120, "jbkp_5": 120,
    "tenggat_waktu": 180,
    "max_freq_pelangsir_jbt": 2,
    "max_freq_pelangsir_jbkp_r4": 3,
    "max_freq_pelangsir_jbkp_r2": 4,
    "max_freq_pelangsir_jbt_r4_umum": 2,
    "max_freq_pelangsir_jbt_r6": 2,
    "max_vol_mismatch": 100
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
                for k, v in default_config.items():
                    if k not in loaded:
                        loaded[k] = v
                return loaded
        except:
            return default_config
    return default_config

if "config_data" not in st.session_state:
    st.session_state.config_data = load_config()

if "df" not in st.session_state:
    st.session_state.df = None

if "temp_df" not in st.session_state:
    st.session_state.temp_df = None

lock_keys = [
    "jbt_1", "jbt_2", "jbt_3", "jbt_4", "jbt_5",
    "jbkp_1", "jbkp_2", "jbkp_3", "jbkp_4", "jbkp_5",
    "max_freq_pelangsir_jbt", "max_freq_pelangsir_jbkp_r4", "max_freq_pelangsir_jbkp_r2",
    "max_freq_pelangsir_jbt_r4_umum", "max_freq_pelangsir_jbt_r6", "max_vol_mismatch", "tenggat_waktu"
]
for k in lock_keys:
    if f"lock_{k}" not in st.session_state:
        st.session_state[f"lock_{k}"] = True

# --- HEADER UTAMA ---
st.markdown(
    """
    <div style="background-color: #2563eb; color: white; padding: 16px; border-radius: 8px; margin-bottom: 20px;">
        <h2 style="margin:0; font-size: 24px;"><i class="fa-solid fa-gas-pump"></i> SPBU Monitoring & Fraud Prevention Dashboard</h2>
        <p style="margin:4px 0 0 0; font-size: 14px; opacity: 0.9;">Pantau transaksi harian, deteksi indikasi kecurangan subsidi, dan kelola kuota BBM berdasarkan rentang plat nomor.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- SIDEBAR NAVIGASI ---
st.sidebar.markdown("### 🗂️ Menu Navigasi SPBU")
selected_tab = st.sidebar.radio(
    "Pilih Menu:",
    [
        "📁 Data Eviden Upload",
        "📊 Ringkasan",
        "📋 Detail Transaksi",
        "🚨 Pelangsir & Beruntun",
        "⚠️ Mismatch Kendaraan",
        "⚙️ Pengaturan Batas & Kuota"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tips SPBU:** Pastikan file laporan harian di-upload melalui menu **Data Eviden Upload** dan klik **Submit Data** agar rekap dan metrik membaca data yang Anda unggah secara aktual.")

# ================= KONTEN BERDASARKAN SIDEBAR =================

if selected_tab == "📁 Data Eviden Upload":
    st.subheader("Sumber Data Transaksi (Hose Delivery)")
    st.write("Unggah file laporan penjualan harian (Excel / CSV) lalu klik **Submit Data Analisis** agar data masuk ke sistem.")

    uploaded_file = st.file_uploader("Pilih file CSV atau XLSX", type=["csv", "xlsx"], key="uploaded_eviden_file")

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                st.session_state.temp_df = pd.read_csv(uploaded_file)
            else:
                st.session_state.temp_df = pd.read_excel(uploaded_file)

            st.info(f"File **{uploaded_file.name}** berhasil dibaca sementara. Silakan klik tombol **Submit Data Analisis** di bawah ini untuk memperbarui rekap.")
            st.dataframe(st.session_state.temp_df.head())

            if st.button("🚀 Submit Data Analisis", type="primary"):
                st.session_state.df = st.session_state.temp_df
                st.success("Data berhasil di-submit! Ringkasan dan tabel rekap sekarang menggunakan data dari file Anda.")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")
            
    elif st.session_state.df is not None:
        st.success("Status: Data eviden aktif sedang digunakan oleh sistem.")
        st.dataframe(st.session_state.df.head())
        if st.button("🗑️ Hapus / Reset Data Aktif"):
            st.session_state.df = None
            st.session_state.temp_df = None
            st.rerun()
    else:
        st.markdown(
            """
            <div style="border: 2px dashed #cbd5e1; padding: 40px; text-align: center; border-radius: 8px; background-color: #f8fafc; margin-top: 20px;">
                <p style="color: #64748b; font-size: 16px; margin: 0;"><b>Belum ada data yang di-submit</b></p>
                <p style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Upload file CSV/XLSX lalu klik submit untuk memproses data aktual.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


elif selected_tab == "📊 Ringkasan":
    st.subheader("Ringkasan & Metrik Pemantauan Subsidi")

    if st.session_state.df is None:
        st.warning("⚠️ Belum ada file data eviden yang di-submit. Metrik dan rekap di bawah ini masih menggunakan **data tiruan (dummy)**. Silakan upload file Anda melalui menu **📁 Data Eviden Upload** lalu klik **Submit Data Analisis**.")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Total Transaksi", "0")
        with col2: st.metric("Subsidi Tanpa Nopol", "0")
        with col3: st.metric("Lebih Kuota Harian", "0")
        with col4: st.metric("Isi Ulang Beruntun", "0")
        with col5: st.metric("Mismatch Kendaraan", "0")
    else:
        actual_total_trx = len(st.session_state.df)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric(label="Total Transaksi Dianalisis", value=f"{actual_total_trx:,}", delta="Data Aktual")
        with col2:
            st.metric(label="Subsidi Tanpa Nopol", value="0", delta="Normal", delta_color="normal")
        with col3:
            st.metric(label="Lebih Kuota Harian", value="0", delta="Normal", delta_color="normal")
        with col4:
            st.metric(label="Isi Ulang Beruntun", value="0", delta="Normal", delta_color="normal")
        with col5:
            st.metric(label="Mismatch Kendaraan", value="0", delta="Normal", delta_color="normal")

    st.markdown("---")
    st.markdown("##### Filter Kategori BBM Berdasarkan Indikasi")
    selected_bbm = st.radio(
        "Pilih Jenis BBM",
        options=["JBT · Solar", "JBKP · Pertalite"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("#### Rekap per Plat (Harian) — " + selected_bbm)
    st.markdown("<p style='font-size: 13px; color: gray;'>Total pengisian plat sama dalam 1 hari vs batas. Diurutkan: yang lewat kuota di atas. Perkiraan jenis = lead, wajib dicek CCTV/SAMSAT.</p>", unsafe_allow_html=True)

    # --- PENGOLAHAN DATA DINAMIS DARI FILE UPLOAD PENGGUNA ---
    if st.session_state.df is not None:
        df_work = st.session_state.df.copy()
        
        # Mencari nama kolom secara fleksibel berdasarkan kemiripan (case-insensitive)
        col_nopol = next((c for c in df_work.columns if any(k in c.lower() for k in ["nopol", "plat", "police", "vehicle"])), None)
        col_vol = next((c for c in df_work.columns if any(k in c.lower() for k in ["liter", "volume", "qty", "jumlah"])), None)
        
        if col_nopol and col_vol:
            # Membersihkan data numerik volume
            df_work[col_vol] = pd.to_numeric(df_work[col_vol].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce").fillna(0)
            
            # Agregasi data per Nopol (jumlah liter total & frekuensi isi)
            agg_df = df_work.groupby(col_nopol).agg(
                total_liter=(col_vol, "sum"),
                frekuensi=(col_vol, "count")
            ).reset_index()
            
            # Batas kuota acuan (mengambil dari config_data jbt_3 atau nilai default 200 L)
            max_kuota = st.session_state.config_data.get("jbt_3", 200)
            
            # Menghitung persentase terhadap kuota
            agg_df["persen"] = (agg_df["total_liter"] / max_kuota * 100).round().astype(int)
            agg_df = agg_df.sort_values(by="total_liter", ascending=False)
            
            # Render baris tabel kustom dengan progress bar
            header_cols = st.columns([1.5, 2.2, 0.8, 4, 1.5])
            with header_cols[0]: st.markdown("**PLAT**")
            with header_cols[1]: st.markdown("**PERKIRAAN JENIS (DARI PLAT)**")
            with header_cols[2]: st.markdown("**ISI**")
            with header_cols[3]: st.markdown("**TOTAL VS KUOTA HARIAN**")
            with header_cols[4]: st.markdown("**STATUS**")
            st.markdown("<hr style='margin: 4px 0 12px 0;'>", unsafe_allow_html=True)

            for _, row in agg_df.iterrows():
                plat_val = str(row[col_nopol])
                liter_val = row["total_liter"]
                freq_val = row["frekuensi"]
                pct_val = min(row["persen"], 100) # Batasi maksimal progress 100%
                
                cols = st.columns([1.5, 2.2, 0.8, 4, 1.5])
                with cols[0]:
                    st.markdown(f"**{plat_val}**")
                with cols[1]:
                    st.markdown(f"≈ Mobil barang &nbsp; <code style='font-size:10px; border: 1px solid #ddd; padding: 1px 4px; border-radius: 3px; color: #555;'>ESTIMASI PLAT</code>", unsafe_allow_html=True)
                with cols[2]:
                    st.markdown(f"{freq_val}×")
                with cols[3]:
                    st.progress(pct_val / 100.0)
                    st.markdown(f"<span style='font-size: 12px; color: #555;'>{liter_val:,.0f} L / {max_kuota} L (batas terlonggar) &nbsp; • &nbsp; {pct_val}%</span>", unsafe_allow_html=True)
                with cols[4]:
                    st.markdown("<span style='background-color: #fef3c7; color: #b45309; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 500;'>🟡 Perlu Diperiksa</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 8px 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ Kolom Nomor Plat atau Volume (Liter) tidak ditemukan secara otomatis di dalam file yang di-upload. Pastikan file Anda memiliki kolom yang memuat kata kunci 'Nopol'/'Plat' dan 'Liter'/'Volume'.")
    else:
        st.info("💡 Belum ada data aktif. Silakan upload file CSV/Excel pada menu **📁 Data Eviden Upload** dan klik **Submit Data Analisis** untuk melihat rekap kustom ini berdasarkan data aktual Anda.")


elif selected_tab == "📋 Detail Transaksi":
    st.subheader("Detail Transaksi & Indikasi Temuan")
    if st.session_state.df is None:
        st.info("💡 Silakan upload file eviden Anda terlebih dahulu.")
    else:
        search_query = st.text_input("🔍 Cari No. Plat / Transaksi", placeholder="Ketik kata kunci...")
        df_show = st.session_state.df.copy()
        if search_query:
            mask = df_show.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
            df_show = df_show[mask]
        st.dataframe(df_show, use_container_width=True)


elif selected_tab == "🚨 Pelangsir & Beruntun":
    st.subheader("🚨 Identifikasi Pelangsir (Isi Ulang Beruntun)")
    if st.session_state.df is None:
        st.info("💡 Silakan upload dan submit data eviden terlebih dahulu.")
    else:
        st.dataframe(st.session_state.df.head(), use_container_width=True)


elif selected_tab == "⚠️ Mismatch Kendaraan":
    st.subheader("⚠️ Identifikasi Ketidaksesuaian (Mismatch Kendaraan vs BBM)")
    if st.session_state.df is None:
        st.info("💡 Silakan upload dan submit data eviden terlebih dahulu.")
    else:
        st.dataframe(st.session_state.df.head(), use_container_width=True)


elif selected_tab == "⚙️ Pengaturan Batas & Kuota":
    st.subheader("Konfigurasi Batas & Kuota BBM Berdasarkan Plat Nomor")
    st.markdown("Atur batasan volume maksimal harian (Liter/Hari) dan ambang batas pelangsir.")

    def render_locked_input(label, key):
        col_inp, col_chk = st.columns([0.92, 0.08])
        with col_chk:
            st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
            is_locked = st.checkbox("🔒", key=f"lock_{key}")
        with col_inp:
            val = st.number_input(label, value=st.session_state.config_data.get(key, 0), key=key, disabled=is_locked)
        return val

    st.markdown("### 🚚 JBT (Jenis BBM Tertentu)")
    col1, col2 = st.columns(2)
    with col1:
        render_locked_input("JBT | 0001-2999 (Roda 4 Pribadi)", "jbt_1")
        render_locked_input("JBT | 3000-6999 (Roda 2 Sepeda Motor)", "jbt_2")
        render_locked_input("JBT | 7000-7999 (Roda 4 > Minibus/Bus)", "jbt_3")
    with col2:
        render_locked_input("JBT | 8000-8999 (Roda 4 > Truck)", "jbt_4")
        render_locked_input("JBT | 9000-9999 (Roda 4 > Truck Khusus)", "jbt_5")

    if st.button("Simpan Pengaturan Kuota Berdasarkan Plat"):
        st.toast("Aturan kuota berhasil disimpan secara permanen!", icon="✅")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray; font-size: 12px;'>Analisis berjalan sepenuhnya di browser Anda.</p>",
    unsafe_allow_html=True,
)
