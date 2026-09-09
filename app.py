import pandas as pd

def deteksi_pelanggaran_jbt(df_transaksi):
    # Ubah kolom waktu menjadi tipe datetime
    df_transaksi['waktu'] = pd.to_datetime(df_transaksi['waktu'])
    
    # 1. Deteksi Transaksi Tanpa Plat
    df_tanpa_nopol = df_transaksi[df_transaksi['plat'].isna() | (df_transaksi['plat'].astype(str).str.strip() == '') | (df_transaksi['plat'] == '- tanpa plat -')]
    
    # 2. Deteksi Pengisian Berulang dengan Jeda Waktu Singkat
    # Bersihkan data yang memiliki plat valid untuk dianalisis jedanya
    df_valid = df_transaksi.dropna(subset=['plat']).copy()
    df_valid = df_valid[df_valid['plat'].astype(str).str.strip() != '- tanpa plat -']
    
    # Urutkan berdasarkan plat dan waktu
    df_valid = df_valid.sort_values(by=['plat', 'waktu']).reset_index(drop=True)
    
    # Hitung selisih waktu dengan transaksi sebelumnya pada plat yang sama (dalam menit)
    df_valid['selisih_menit'] = df_valid.groupby('plat')['waktu'].diff().dt.total_seconds() / 60
    
    # Tentukan batas jeda waktu mencurigakan (misalnya kurang dari 15 menit)
    BATAS_MENIT = 15
    df_jeda_singkat = df_valid[(df_valid['selisih_menit'].notnull()) & (df_valid['selisih_menit'] < BATAS_MENIT)]
    
    return df_jeda_singkat, df_tanpa_nopol

# Contoh data frame berdasarkan gambar dasbor
data = {
    'id_transaksi': [2305873, 2305876, 2305877, 2305921],
    'plat': ['H1460UW', 'H1460UW', 'H1460UW', '- tanpa plat -'],
    'waktu': ['2026-08-31 05:45:36', '2026-08-31 05:48:55', '2026-08-31 05:57:51', '2026-08-31 07:42:06'],
    'volume': [34.35, 17.65, 29.42, 22.06]
}

df_sample = pd.DataFrame(data)
hasil_jeda, hasil_tanpa_nopol = deteksi_pelanggaran_jbt(df_sample)

print("=== TEMUAN: JEDA WAKTU TERLALU SINGKAT ===")
print(hasil_jeda[['id_transaksi', 'plat', 'waktu', 'volume', 'selisih_menit']])

print("\n=== TEMUAN: TRANSAKSI TANPA PLAT ===")
print(hasil_tanpa_nopol[['id_transaksi', 'plat', 'waktu', 'volume']])
