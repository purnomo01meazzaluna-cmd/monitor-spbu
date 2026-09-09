def render_tab_content(sub_df, rekap_df, label_prod):
            st.markdown(f"#### Rekapitulasi Berdasarkan Golongan Plat & Rentang Waktu — {label_prod}")
            st.caption("Deteksi otomatis rentang plat nomor, kuota spesifik, dan peringatan jeda waktu singkat antar pengisian pada hose nozzle.")
            
            if sub_df.empty or rekap_df.empty:
                st.info(f"Tidak ada data transaksi {label_prod}.")
                return

            filtered = rekap_df
            if search_input:
                filtered = rekap_df[rekap_df['PLAT'].str.contains(search_input.upper(), na=False)]

            global_row_counter = 0

            for _, row in filtered.iterrows():
                plat = row['PLAT']
                tgl = row['TANGGAL']
                gol = row['GOLONGAN']
                limit = row['KUOTA_BATAS']
                total_l = row['TOTAL_LITER']
                isi_cnt = row['ISI']
                status = row['STATUS']
                pct = min(int((total_l / limit) * 100), 100) if limit > 0 else 100
                
                b_color = "#fef3c7" if status == "⚠️ Perlu Diperiksa" else "#d1fae5"
                t_color = "#92400e" if status == "⚠️ Perlu Diperiksa" else "#065f46"

                with st.container():
                    st.markdown(f"""
                    <div class="card-container">
                        <table style="width:100%; border:none;">
                            <tr>
                                <td style="width:18%; font-weight:bold; font-size:16px;">{plat}<br><span style="font-size:11px; color:#6b7280; font-weight:normal;">📅 {tgl}</span></td>
                                <td style="width:25%;"><b>{gol}</b><br><span style="background:#e5e7eb; padding:2px 6px; border-radius:4px; font-size:11px;">GOLONGAN PLAT</span></td>
                                <td style="width:10%;">{isi_cnt}× isi</td>
                                <td style="width:32%;">
                                    <div style="font-size:13px; margin-bottom:4px;">{total_l:.1f} L / {limit} L (Batas Golongan)</div>
                                    <div style="background:#e5e7eb; border-radius:4px; width:100%; height:8px;">
                                        <div style="background:{'#dc2626' if total_l > limit else '#16a34a'}; width:{pct}%; height:8px; border-radius:4px;"></div>
                                    </div>
                                </td>
                                <td style="width:15%; text-align:right;">
                                    <span style="background:{b_color}; color:{t_color}; padding:4px 8px; border-radius:12px; font-size:12px; font-weight:600;">{status}</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    trx_detail = sub_df[(sub_df['PLAT_CLEAN'] == plat) & (sub_df['TANGGAL_SAJA'] == tgl)]
                    for trx in trx_detail.itertuples():
                        global_row_counter += 1
                        looping_badge = "<span style='color:red; font-weight:bold;'>(⚠️ Jeda Cepat)</span>" if trx.IS_LOOPING_RISK else ""
                        
                        col_cctv, col_id_trx, col_time_trx, col_prod_trx, col_plat_trx, col_vol_trx, col_type_trx, col_stat_trx, col_reason_trx = st.columns([1.5, 0.9, 1.3, 1.2, 1.0, 0.9, 1.2, 1.1, 1.8])
                        with col_cctv:
                            cam_key = f"cam_{label_prod}_{global_row_counter}"
                            gal_key = f"gal_{label_prod}_{global_row_counter}"
                            
                            # Menggunakan st.camera_input asli
                            cam_file = st.camera_input("📷 Ambil Foto", key=cam_key, label_visibility="collapsed")
                            if cam_file is not None:
                                st.session_state[f"img_{cam_key}"] = cam_file

                            if f"img_{cam_key}" in st.session_state:
                                st.success("Foto tersimpan!")
                                st.image(st.session_state[f"img_{cam_key}"], width=130)

                            gal_file = st.file_uploader("🖼️ Galeri", type=["jpg", "png", "jpeg"], key=gal_key, label_visibility="collapsed")
                            if gal_file is not None:
                                st.session_state[f"img_{gal_key}"] = gal_file

                            if f"img_{gal_key}" in st.session_state:
                                st.success("Galeri tersimpan!")
                                st.image(st.session_state[f"img_{gal_key}"], width=130)

                        with col_id_trx:
                            st.write(trx.ID_CLEAN)
                        with col_time_trx:
                            st.write(f"{trx.TIME_OBJ.strftime('%H:%M:%S')} {looping_badge}", unsafe_allow_html=True)
                        with col_prod_trx:
                            st.write(f"{trx.PRODUCT_CLEAN}")
                        with col_plat_trx:
                            st.markdown(f"**{plat}**")
                        with col_vol_trx:
                            st.write(f"{trx.VOL_CLEAN:.2f}L")
                        with col_type_trx:
                            st.markdown(f"<b>{trx.GOLONGAN}</b>", unsafe_allow_html=True)
                        with col_stat_trx:
                            st.markdown(f"<span style='background:{b_color}; color:{t_color}; padding:2px 6px; border-radius:10px; font-size:11px;'>{status}</span>", unsafe_allow_html=True)
                        with col_reason_trx:
                            reason_txt = f"Harian {total_l:.1f}L > Batas ({limit}L)" if total_l > limit else f"Jeda waktu {trx.DIFF_MINUTES:.0f} menit"
                            st.markdown(f"<span style='color:#6b7280; font-size:12px;'>{reason_txt}</span>", unsafe_allow_html=True)
                        
                        st.markdown("<hr style='margin: 5px 0; border-top: 1px solid #f3f4f6;'>", unsafe_allow_html=True)
