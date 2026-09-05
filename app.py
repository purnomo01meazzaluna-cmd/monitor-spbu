import streamlit as st
import pandas as pd
import io
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PilImage

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Dashboard SPBU & Manajemen Laporan",
    page_icon="⛽",
    layout="wide"
)

# Inisialisasi session state dummy jika belum ada
if 'foto_evidens' not in st.session_state:
    st.session_state.foto_evidens = {}
if 'catatan_transaksi' not in st.session_state:
    st.session_state.catatan_transaksi = {}

# Dummy Database Lokal (Session State untuk simulasi database)
if 'db_laporan' not in st.session_state:
    st.session_state.db_laporan = pd.DataFrame([
        {
            "ID": 1, 
            "Waktu Unduh": "2026-09-05 07:05:56", 
            "Jenis Laporan": "Laporan Tindak Lanjut", 
            "Nama File": "tindak_lanjut_subsidi_4450609_2026-09-01.xlsx", 
            "ID SPBU": "4450609", 
            "Total Baris": 5,
            "File_Bytes": b"dummy_bytes_1"
        },
        {
            "ID": 2, 
            "Waktu Unduh": "2026-09-05 07:10:37", 
            "Jenis Laporan": "Laporan Tindak Lanjut", 
            "Nama File": "tindak_lanjut_subsidi_4450609_2026-09-01.xlsx", 
            "ID SPBU": "4450609", 
            "Total Baris": 5,
            "File_Bytes": b"dummy_bytes_2"
        },
        {
            "ID": 3, 
            "Waktu Unduh": "2026-09-05 07:11:41", 
            "Jenis Laporan": "Transaksi Lengkap & Foto", 
            "Nama File": "transaksi_lengkap_evidens_4450609_2026-09-02.xlsx", 
            "ID SPBU": "4450609", 
            "Total Baris": 5,
            "File_Bytes": b"dummy_bytes_3"
        }
    ])

# Fungsi simulasi penyimpanan ke database
def simpan_ke_database(jenis_laporan, filename, file_bytes, spbu_id, total_baris):
    import datetime
    new_id = int(st.session_state.db_laporan['ID'].max() + 1) if not st.session_state.db_laporan.empty else 1
    new_row = pd.DataFrame([{
        "ID": new_id,
        "Waktu Unduh": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Jenis Laporan": jenis_laporan,
        "Nama File": filename,
        "ID SPBU": spbu_id,
        "Total Baris": total_baris,
        "File_Bytes": file_bytes
    }])
    st.session_state.db_laporan = pd.concat([st.session_state.db_laporan, new_row], ignore_index=True)

# Fungsi update database
def update_database_record(record_id, nama_file, id_spbu, total_baris):
    idx = st.session_state.db_laporan[st.session_state.db_laporan['ID'] == record_id].index
    if not idx.empty:
        st.session_state.db_laporan.loc[idx, 'Nama File'] = nama_file
        st.session_state.db_laporan.loc[idx, 'ID SPBU'] = id_spbu
        st.session_state.db_laporan.loc[idx, 'Total Baris'] = total_baris

# Fungsi hapus database
def delete_database_record(record_id):
    st.session_state.db_laporan = st.session_state.db_laporan[st.session_state.db_laporan['ID'] != record_id].reset_index(drop=True)

# Dummy dataframe untuk analisis
df_analysis = pd.DataFrame({
    'No_Polisi': ['H 1234 AB', 'H 5678 CD', 'K 9999 XX', 'B 1111 ZZ', 'AA 2222 BB'],
    'Jenis_BBM': ['Pertalite', 'Solar', 'Pertalite', 'Solar', 'Pertalite'],
    'Volume_Liter': [20, 35, 15, 40, 25],
    'Status': ['Valid', 'Perlu Verifikasi', 'Valid', 'Valid', 'Perlu Verifikasi']
})

spbu_id_input = "4450609"
selected_date = "2026-09-05"

st.title("⛽ Dashboard Operasional SPBU & Manajemen Laporan")

# Membuat Navigasi Utama (Tab)
tab1, tab2, tab3 = st.tabs(["📊 Ringkasan & Analisis", "🔍 Detail Transaksi & Evidens", "📂 Riwayat Database Laporan"])

with tab1:
    st.subheader("Ringkasan Data Harian")
    st.dataframe(df_analysis, use_container_width=True)

with tab2:
    st.subheader("🔍 Detail Transaksi & Evidens Kamera Perangkat")
    
    # Proporsi kolom diatur agar tombol dan input sejajar sempurna tanpa bertumpuk
    control_col1, control_col2, control_col3, control_col4 = st.columns([2.0, 0.9, 2.3, 2.3])
    
    with control_col1:
        search_query = st.text_input("Cari plat nomor...", placeholder="Ketik nomor plat...", label_visibility="collapsed")
    
    with control_col2:
        if st.button("Refresh", use_container_width=True):
            st.rerun()
    
    with control_col3:
        output_tindak_lanjut = io.BytesIO()
        with pd.ExcelWriter(output_tindak_lanjut, engine='openpyxl') as writer:
            df_analysis.to_excel(writer, index=False, sheet_name='Tindak_Lanjut')
        
        file_bytes_tl = output_tindak_lanjut.getvalue()
        filename_tl = f"tindak_lanjut_subsidi_{spbu_id_input}_{selected_date}.xlsx"
        
        st.download_button(
            label="📥 Unduh Tindak Lanjut",
            data=file_bytes_tl,
            file_name=filename_tl,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            on_click=simpan_ke_database,
            args=("Laporan Tindak Lanjut", filename_tl, file_bytes_tl, spbu_id_input, len(df_analysis))
        )

    with control_col4:
        df_export = df_analysis.copy()
        df_export['Status_Evidens_Foto'] = [
            "ADA FOTO" if f"row_{idx}" in st.session_state.foto_evidens else "BELUM ADA FOTO" 
            for idx in df_export.index
        ]
        df_export['Catatan_Investigasi'] = [
            st.session_state.catatan_transaksi.get(f"row_{idx}", "") 
            for idx in df_export.index
        ]

        output_transaksi = io.BytesIO()
        with pd.ExcelWriter(output_transaksi, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=True, sheet_name='Transaksi_Dan_Foto')
        
        output_transaksi.seek(0)
        
        if len(st.session_state.foto_evidens) > 0:
            wb = load_workbook(output_transaksi)
            ws = wb['Transaksi_Dan_Foto']
            ws.column_dimensions['A'].width = 15
            
            for idx, row in df_export.iterrows():
                row_key = f"row_{idx}"
                if row_key in st.session_state.foto_evidens:
                    excel_row = list(df_export.index).index(idx) + 2
                    ws.row_dimensions[excel_row].height = 60
                    
                    img_bytes = st.session_state.foto_evidens[row_key]
                    try:
                        pil_img = PilImage.open(io.BytesIO(img_bytes))
                        img_io = io.BytesIO()
                        pil_img.save(img_io, format='JPEG')
                        img_io.seek(0)
                        
                        img = OpenpyxlImage(img_io)
                        img.width = 70
                        img.height = 50
                        ws.add_image(img, f"A{excel_row}")
                    except Exception:
                        pass
            
            final_excel_io = io.BytesIO()
            wb.save(final_excel_io)
            final_excel_data = final_excel_io.getvalue()
        else:
            final_excel_data = output_transaksi.getvalue()

        filename_full = f"transaksi_lengkap_evidens_{spbu_id_input}_{selected_date}.xlsx"

        st.download_button(
            label="📥 Unduh Transaksi + Foto",
            data=final_excel_data,
            file_name=filename_full,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            on_click=simpan_ke_database,
            args=("Transaksi Lengkap & Foto Evidens", filename_full, final_excel_data, spbu_id_input, len(df_export))
        )
        
    st.markdown("---")
    # Filter dan tampilkan tabel data
    if search_query:
        filtered_df = df_analysis[df_analysis['No_Polisi'].str.contains(search_query, case=False, na=False)]
    else:
        filtered_df = df_analysis
    
    st.dataframe(filtered_df, use_container_width=True)

with tab3:
    st.subheader("📂 Manajemen Riwayat Laporan Database")
    st.markdown("Daftar seluruh file laporan dan data yang pernah Anda unduh tersimpan aman di database lokal. Anda dapat melihat detail, mengedit catatan/metadata, atau menghapusnya.")

    df_riwayat = st.session_state.db_laporan

    if not df_riwayat.empty:
        # Pilihan aksi manajemen
        action_tab = st.radio("Pilih Aksi Manajemen:", ["👀 View (Lihat & Unduh)", "✏️ Edit Data", "🗑️ Hapus Data"], horizontal=True)
        
        st.markdown("---")
        
        if action_tab == "👀 View (Lihat & Unduh)":
            st.markdown("### Daftar Riwayat Laporan")
            # Tampilkan tabel tanpa kolom binary 'File_Bytes' agar bersih
            st.dataframe(df_riwayat.drop(columns=['File_Bytes']), use_container_width=True)
            
            selected_id_view = st.selectbox("Pilih ID Laporan untuk diunduh ulang:", df_riwayat['ID'].tolist(), key="view_id")
            selected_row = df_riwayat[df_riwayat['ID'] == selected_id_view].iloc[0]
            
            st.info(f"File terpilih: **{selected_row['Nama File']}** (SPBU: {selected_row['ID SPBU']})")
            
            file_blob = selected_row['File_Bytes']
            st.download_button(
                label="📥 Unduh Ulang File Ini",
                data=file_blob,
                file_name=selected_row['Nama File'],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        elif action_tab == "✏️ Edit Data":
            st.markdown("### Edit Metadata Laporan")
            selected_id_edit = st.selectbox("Pilih ID Laporan yang ingin diedit:", df_riwayat['ID'].tolist(), key="edit_id")
            
            row_to_edit = df_riwayat[df_riwayat['ID'] == selected_id_edit].iloc[0]
            
            with st.form("form_edit_laporan"):
                new_nama_file = st.text_input("Nama File", value=str(row_to_edit['Nama File']))
                new_id_spbu = st.text_input("ID SPBU", value=str(row_to_edit['ID SPBU']))
                new_total_baris = st.number_input("Total Baris", value=int(row_to_edit['Total Baris']))
                
                submit_edit = st.form_submit_button("💾 Simpan Perubahan", use_container_width=True)
                if submit_edit:
                    update_database_record(selected_id_edit, new_nama_file, new_id_spbu, new_total_baris)
                    st.success(f"Data laporan dengan ID {selected_id_edit} berhasil diperbarui!")
                    st.rerun()

        elif action_tab == "🗑️ Hapus Data":
            st.markdown("### Hapus Riwayat Laporan")
            selected_id_del = st.selectbox("Pilih ID Laporan yang ingin dihapus:", df_riwayat['ID'].tolist(), key="del_id")
            
            row_to_del = df_riwayat[df_riwayat['ID'] == selected_id_del].iloc[0]
            st.warning(f"Anda akan menghapus laporan: **{row_to_del['Nama File']}** (ID: {selected_id_del}). Tindakan ini tidak dapat dibatalkan.")
            
            if st.button("🗑️ Konfirmasi Hapus Data", type="primary", use_container_width=True):
                delete_database_record(selected_id_del)
                st.success(f"Laporan dengan ID {selected_id_del} berhasil dihapus dari database.")
                st.rerun()
    else:
        st.info("Belum ada riwayat laporan tersimpan di database.")
