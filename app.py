# Main Layout Tabs (Pastikan baris ini ada sebelum memanggil tab1, tab2, tab3, atau tab4)
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Ringkasan Transaksi", 
            "🔍 Detail Kendaraan", 
            "⚙️ Pengaturan & Kuota", 
            "📸 Evidence Monitoring"
        ])

        with tab1:
            # ... (kode tab 1 Anda yang sudah ada)
            pass

        with tab2:
            st.subheader("Tabel Mentah Data Upload")
            st.dataframe(df_raw, use_container_width=True)

        with tab3:
            st.subheader("Pengaturan Batas Kuota Referensi Produk")
            st.markdown("Tentukan batas wajar harian untuk masing-masing kategori produk dalam satu kolom:")
            
            col_input, _ = st.columns([1, 2])
            with col_input:
                st.session_state.batas_JBT = st.number_input(
                    "Batas JBT (L)", 
                    value=float(st.session_state.batas_JBT),
                    step=5.0
                )
                st.session_state.batas_JBKP = st.number_input(
                    "Batas JBKP (L)", 
                    value=float(st.session_state.batas_JBKP),
                    step=5.0
                )
                st.session_state.batas_R2 = st.number_input(
                    "Batas R2 (L)", 
                    value=float(st.session_state.batas_R2),
                    step=1.0
                )

        with tab4:
            st.subheader("📸 Evidence & Log Monitoring Transaksi")
            st.markdown("Tabel hasil analisis transaksi, dokumentasi bukti CCTV, serta alasan temuan anomali kuota harian.")
            
            # Header Tabel Analisis Evidence (ditambah kolom JUSTIFIKASI)
            ev_header_html = """
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; margin-bottom: 8px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; color: #64748b; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;">
                <div style="flex: 1.1;">BUKTI CCTV</div>
                <div style="flex: 0.9;">ID</div>
                <div style="flex: 1.3;">WAKTU</div>
                <div style="flex: 1.4;">PRODUCT / NOZZLE</div>
                <div style="flex: 1.1;">PLAT</div>
                <div style="flex: 0.9;">VOLUME</div>
                <div style="flex: 1.4;">PERKIRAAN JENIS</div>
                <div style="flex: 1.2;">STATUS</div>
                <div style="flex: 1.8;">ALASAN TEMUAN</div>
                <div style="flex: 2.2; padding-left: 5px;">JUSTIFIKASI</div>
            </div>
            """
            st.markdown(ev_header_html, unsafe_allow_html=True)

            if not df_display.empty and col_nopol_opt in df_display.columns:
                agg_vol = df_display.groupby(col_nopol_opt)[col_vol_opt].apply(lambda x: pd.to_numeric(x, errors='coerce').sum()).to_dict()

                for index, row in df_display.iterrows():
                    trx_id = str(row[col_id_opt]) if col_id_opt in df_display.columns else f"230{index}5"
                    waktu = str(row[col_waktu_opt]) if col_waktu_opt in df_display.columns else f"{selected_date}, 08:30:00"
                    prod = str(row[col_produk_opt]) if col_produk_opt in df_display.columns else "BIOSOLAR"
                    plat = str(row[col_nopol_opt])
                    vol_val = pd.to_numeric(row[col_vol_opt], errors='coerce') if col_vol_opt in df_display.columns else 0.0
                    
                    total_plat_vol = agg_vol.get(plat, vol_val)
                    
                    row_limit = active_limit
                    plat_upper = plat.upper()
                    if any(char.isdigit() for char in plat_upper) and len(plat_upper) > 6:
                        jenis_kendaraan = "Bus" if vol_val > 100 else ("Mobil barang" if vol_val > 40 else "Mobil penumpang")
                    else:
                        jenis_kendaraan = "Mobil barang"

                    is_anomaly = total_plat_vol > row_limit
                    status_html = "<span style='background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Perlu Diperiksa</span>" if is_anomaly else "<span style='background-color: #def7ec; color: #03543f; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;'>● Normal</span>"
                    alasan = f"Total harian {total_plat_vol:.1f}L > jatah wajar ({row_limit:.0f}L)" if is_anomaly else "Dalam batas wajar kuota"

                    r_cols = st.columns([1.1, 0.9, 1.3, 1.4, 1.1, 0.9, 1.4, 1.2, 1.8, 2.2])
                    
                    with r_cols[0]:
                        st.markdown("""
                            <div style="display: flex; flex-direction: column; gap: 3px;">
                                <span style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px; font-size: 0.65rem; color: #334155; text-align: center;">📷 Kamera</span>
                                <span style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 2px 4px; font-size: 0.65rem; color: #334155; text-align: center;">📁 Galeri</span>
                            </div>
                        """, unsafe_allow_html=True)
                    with r_cols[1]:
                        st.markdown(f"<span style='font-family: monospace; font-size: 0.8rem; color: #475569;'>{trx_id}</span>", unsafe_allow_html=True)
                    with r_cols[2]:
                        st.markdown(f"<span style='font-size: 0.7rem; color: #475569;'>{waktu}</span>", unsafe_allow_html=True)
                    with r_cols[3]:
                        st.markdown(f"<span style='font-size: 0.75rem; font-weight: 500; color: #1e293b;'>{prod}</span>", unsafe_allow_html=True)
                    with r_cols[4]:
                        st.markdown(f"<span style='font-family: monospace; font-weight: 600; font-size: 0.8rem; color: #0f172a;'>{plat}</span>", unsafe_allow_html=True)
                    with r_cols[5]:
                        st.markdown(f"<span style='font-size: 0.8rem; font-weight: 600; color: #334155;'>{vol_val:.2f}L</span>", unsafe_allow_html=True)
                    with r_cols[6]:
                        st.markdown(f"<span style='font-size: 0.75rem; color: #64748b;'>≈ {jenis_kendaraan}</span>", unsafe_allow_html=True)
                    with r_cols[7]:
                        st.markdown(status_html, unsafe_allow_html=True)
                    with r_cols[8]:
                        st.markdown(f"<span style='font-size: 0.7rem; color: #64748b;'>{alasan}</span>", unsafe_allow_html=True)
                    with r_cols[9]:
                        st.text_input("Justifikasi", value="", key=f"justifikasi_{index}", label_visibility="collapsed", placeholder="Isi catatan...")
            else:
                st.warning("Belum ada data transaksi untuk dimuat ke tabel evidence.")

            st.markdown("---")
            
            if not df_display.empty:
                csv_data = df_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Laporan & Log Monitoring (.csv)",
                    data=csv_data,
                    file_name=f"Laporan_Evidence_SPBU_4150201_{selected_date}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
