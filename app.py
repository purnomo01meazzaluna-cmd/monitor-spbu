# --- KARTU METRIK RINGKASAN ---
        total_jbt_count = len(df_jbt)
        total_jbkp_count = len(df_jbkp)
        
        # Hitung metrik dinamis
        plat_over_jbt = len(rekap_jbt[rekap_jbt['TOTAL_LITER'] > limit_jbt]) if not rekap_jbt.empty else 0
        plat_over_jbkp = len(rekap_jbkp[rekap_jbkp['TOTAL_LITER'] > limit_jbkp]) if not rekap_jbkp.empty else 0
        total_over = plat_over_jbt + plat_over_jbkp
        
        no_nopol_count = len(df[df['PLAT_CLEAN'].str.contains('TANPA|KOSONG|-', na=False)])
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 20px;">⛽</span> <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_over}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Plat melewati kuota harian</p>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 20px;">🚫</span> <span style="font-size: 20px; font-weight: bold; color: #111827;">{no_nopol_count}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Transaksi subsidi tanpa nopol</p>
            </div>
            """, unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 20px;">🔍</span> <span style="font-size: 20px; font-weight: bold; color: #111827;">0</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Angka plat tak cocok konsumsi (lead)</p>
            </div>
            """, unsafe_allow_html=True)

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_jbt_count}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Transaksi JBT</p>
            </div>
            """, unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">0</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Sangat mencurigakan</p>
            </div>
            """, unsafe_allow_html=True)
        with col_s3:
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">{total_jbt_count}</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Perlu diperiksa</p>
            </div>
            """, unsafe_allow_html=True)
        with col_s4:
            st.markdown(f"""
            <div class="metric-card">
                <span style="font-size: 20px; font-weight: bold; color: #111827;">0</span>
                <p style="color: #6b7280; font-size: 13px; margin: 4px 0 0 0;">Normal</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        
        # Filter & Tombol Aksi Baris Bawah
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1.5, 1.5])
        with col_f1:
            search_query = st.text_input("Cari plat nomor...", placeholder="Ketik plat nomor...")
        with col_f2:
            st.write("")
            st.button("Analisis ulang")
        with col_f3:
            st.write("")
            st.button("Unduh tindak lanjut (Excel)")
        with col_f4:
            st.write("")
            st.button("Unduh transaksi + foto (Excel)", type="primary")
