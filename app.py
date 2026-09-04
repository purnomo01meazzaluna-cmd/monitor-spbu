with tab2:
            st.subheader("🔍 Detail Transaksi & Rekaman Evidens CCTV & Catatan")
            st.markdown("Setiap baris transaksi dilengkapi dengan tombol akses rekaman kamera CCTV, galeri foto, serta kolom catatan investigasi.")
            
            # Inisialisasi session state untuk menyimpan catatan pengawas
            if "catatan_transaksi" not in st.session_state:
                st.session_state.catatan_transaksi = {}

            if not df_analysis.empty:
                for idx, row in df_analysis.iterrows():
                    trans_id = f"230{idx}755"
                    waktu_val = str(row[col_time_opt]) if col_time_opt in df_analysis.columns else "01/09/2026, 06.05.23"
                    produk_val = str(row[col_produk_opt]) if col_produk_opt in df_analysis.columns else "BIO_SOLAR"
                    nozzle_val = f"({col_nozzle_opt}: {row[col_nozzle_opt]})" if col_nozzle_opt in df_analysis.columns else "(P3/H1)"
                    plat_val = str(row[col_nopol_opt])
                    if plat_val == "INVALID_NOPOL":
                        plat_val = "- tanpa plat -"
                    vol_val = f"{row[col_vol_opt]}L" if col_vol_opt in df_analysis.columns else "0L"
                    
                    alasan = "Transaksi Normal"
                    is_err = False
                    if plat_val == "- tanpa plat -":
                        alasan = "Subsidi tanpa nopol — wajib dicatat per aturan"
                        is_err = True
                    elif row.get('is_fast_interval', False) or row.get('is_cross_pump', False):
                        alasan = "Indikasi pindah nosel atau jeda waktu pengisian terlalu singkat (<30 menit)"
                        is_err = True
                    
                    # Layout baris data
                    col_card_1, col_card_2, col_card_3, col_card_4, col_card_5, col_card_6 = st.columns([1.2, 1.1, 1.5, 1.5, 1.2, 1.1])
                    
                    with col_card_1:
                        if st.button("📷 Kamera", key=f"cam_{idx}"):
                            st.toast(f"Membuka rekaman CCTV live untuk transaksi #{trans_id}")
                        if st.button("📁 Galeri", key=f"gal_{idx}"):
                            st.toast(f"Menampilkan galeri foto plat nopol {plat_val}")
                    with col_card_2:
                        st.markdown(f"**ID**\n`{trans_id}`")
                    with col_card_3:
                        st.markdown(f"**Waktu**\n{waktu_val}")
                    with col_card_4:
                        st.markdown(f"**Produk/Nozzle**\n{produk_val}\n`{nozzle_val}`")
                    with col_card_5:
                        st.markdown(f"**Plat**\n**`{plat_val}`**")
                    with col_card_6:
                        st.markdown(f"**Volume**\n`{vol_val}`")
                    
                    # Kolom Status & Catatan Investigasi di bawahnya
                    col_note_1, col_note_2 = st.columns([2.5, 3.5])
                    with col_note_1:
                        if is_err:
                            st.error(f"⚠️ {alasan}")
                        else:
                            st.success("● Normal")
                    with col_note_2:
                        current_note = st.session_state.catatan_transaksi.get(trans_id, "")
                        new_note = st.text_input(
                            f"Catatan Investigasi #{trans_id}", 
                            value=current_note, 
                            placeholder="Tulis catatan (cth: Ditegur, Barcode sesuai KTP)...",
                            key=f"note_input_{idx}",
                            label_visibility="collapsed"
                        )
                        st.session_state.catatan_transaksi[trans_id] = new_note
                        
                    st.markdown("---")
            else:
                st.info("Belum ada data untuk ditampilkan.")
