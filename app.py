with col_f3:
              st.write("")
              if data_tab.empty:
                st.button("📥 Unduh Excel", key=f"dl_empty_{nama_bbm}", disabled=True)
              else:
                output_excel = io.BytesIO()
                with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
                    df_export_base = data_tab.copy()
                    noted_dict = st.session_state[f"noted_dict_{nama_bbm}"]
                    df_export_base["Noted"] = [
                        noted_dict.get(idx, "") for idx in data_tab.index
                    ]
                    df_export_base.to_excel(writer, index=False, sheet_name="Data")
                st.download_button(
                    "📥 Unduh Excel",
                    data=output_excel.getvalue(),
                    file_name=f"tindak_lanjut_{nama_bbm}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{nama_bbm}",
                )

            with col_f4:
              st.write("")
              if data_tab.empty:
                st.button("Unduh transaksi + foto (Excel)", key=f"dl_foto_empty_{nama_bbm}", disabled=True)
              else:
                excel_foto_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_foto_buffer, engine="openpyxl") as writer:
                    df_export = data_tab.copy()
                    foto_dict = st.session_state[f"foto_dict_{nama_bbm}"]
                    noted_dict = st.session_state[f"noted_dict_{nama_bbm}"]

                    status_foto_list = []
                    noted_list = []
                    jenis_kendaraan_list = []
                    status_transaksi_list = []
                    alasan_temuan_list = []

                    for idx, row in data_tab.iterrows():
                        f_key = f"foto_trx_{nama_bbm}_{idx}"
                        if f_key in foto_dict and foto_dict[f_key] is not None:
                            status_foto_list.append("Ada (Terunggah)")
                        else:
                            status_foto_list.append("Belum Ada")
                        noted_list.append(noted_dict.get(idx, ""))

                        trx_plat = (
                            str(row[plat_col])
                            if plat_col in data_tab.columns
                            else "N/A"
                        )
                        trx_vol = (
                            float(row[vol_col])
                            if vol_col in data_tab.columns
                            else 0.0
                        )
                        total_vol_plat = plat_totals.get(trx_plat, trx_vol)
                        jenis_kendaran, batas_val = (
                            identifikasi_jenis_dan_kuota_dari_plat(
                                trx_plat, nama_bbm
                            )
                        )

                        if trx_plat in ["N/A", "-", ""]:
                            st_val = "Perlu Diperiksa"
                            alasan_val = (
                                "Subsidi tanpa nopol — wajib dicatat per aturan"
                            )
                        elif total_vol_plat > batas_val:
                            st_val = "Perlu Diperiksa"
                            alasan_val = f"Total harian {total_vol_plat:.1f}L > jatah {jenis_kendaran} ({batas_val}L)"
                        else:
                            st_val = "Normal"
                            alasan_val = "Normal"

                        jenis_kendaraan_list.append(jenis_kendaran)
                        status_transaksi_list.append(st_val)
                        alasan_temuan_list.append(alasan_val)

                    df_export["Jenis_Kendaraan"] = jenis_kendaraan_list
                    df_export["Status_Transaksi"] = status_transaksi_list
                    df_export["Alasan_Temuan"] = alasan_temuan_list
                    df_export["Status_Foto_CCTV"] = status_foto_list
                    df_export["Noted"] = noted_list

                    cols_order = [
                        c
                        for c in df_export.columns
                        if c
                        not in [
                            "Jenis_Kendaraan",
                            "Status_Transaksi",
                            "Alasan_Temuan",
                            "Status_Foto_CCTV",
                            "Noted",
                            "Clean_Product",
                        ]
                    ]
                    final_cols = (
                        cols_order[:4]
                        + [
                            "Jenis_Kendaraan",
                            "Status_Transaksi",
                            "Alasan_Temuan",
                            "Status_Foto_CCTV",
                            "Noted",
                        ]
                        + cols_order[4:]
                    )
                    df_export = df_export[
                        [c for c in final_cols if c in df_export.columns]
                    ]

                    df_export.to_excel(
                        writer, index=False, sheet_name="Laporan & Foto"
                    )

                    worksheet = writer.sheets["Laporan & Foto"]
                    for col in worksheet.columns:
                        max_length = 0
                        column_letter = col[0].column_letter
                        for cell in col:
                            try:
                                if cell.value:
                                    max_length = max(
                                        max_length, len(str(cell.value))
                                    )
                            except:
                                pass
                        worksheet.column_dimensions[column_letter].width = max(
                            max_length + 3, 12
                        )

                st.download_button(
                    "Unduh transaksi + foto (Excel)",
                    data=excel_foto_buffer.getvalue(),
                    file_name=f"laporan_transaksi_dan_foto_{nama_bbm}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_foto_excel_{nama_bbm}",
                )
