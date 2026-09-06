<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Monitoring SPBU & Kuota BBM</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-50 text-gray-800 font-sans" x-data="{ activeTab: 'ringkasan' }">

    <header class="bg-blue-600 text-white shadow-md">
        <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <i class="fa-solid fa-gas-pump text-2xl"></i>
                <h1 class="text-xl font-bold">SPBU Monitoring & Fraud Prevention Dashboard</h1>
            </div>
            <div class="text-sm bg-blue-700 px-3 py-1 rounded-full">
                <i class="fa-regular fa-clock mr-1"></i> Data: Kemarin (H-1)
            </div>
        </div>
    </header>

    <nav class="bg-white border-b border-gray-200 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 flex space-x-8 overflow-x-auto">
            <button @click="activeTab = 'ringkasan'" 
                :class="activeTab === 'ringkasan' ? 'border-blue-600 text-blue-600 font-semibold' : 'border-transparent text-gray-500 hover:text-gray-700'"
                class="py-4 px-1 border-b-2 text-sm flex items-center space-x-2 transition-colors whitespace-nowrap">
                <i class="fa-solid fa-chart-pie"></i>
                <span>Ringkasan</span>
            </button>
            <button @click="activeTab = 'detail'" 
                :class="activeTab === 'detail' ? 'border-blue-600 text-blue-600 font-semibold' : 'border-transparent text-gray-500 hover:text-gray-700'"
                class="py-4 px-1 border-b-2 text-sm flex items-center space-x-2 transition-colors whitespace-nowrap">
                <i class="fa-solid fa-list-check"></i>
                <span>Detail Transaksi</span>
            </button>
            <button @click="activeTab = 'pengaturan'" 
                :class="activeTab === 'pengaturan' ? 'border-blue-600 text-blue-600 font-semibold' : 'border-transparent text-gray-500 hover:text-gray-700'"
                class="py-4 px-1 border-b-2 text-sm flex items-center space-x-2 transition-colors whitespace-nowrap">
                <i class="fa-solid fa-sliders"></i>
                <span>Pengaturan Batas & Kuota</span>
            </button>
            <button @click="activeTab = 'eviden'" 
                :class="activeTab === 'eviden' ? 'border-blue-600 text-blue-600 font-semibold' : 'border-transparent text-gray-500 hover:text-gray-700'"
                class="py-4 px-1 border-b-2 text-sm flex items-center space-x-2 transition-colors whitespace-nowrap">
                <i class="fa-solid fa-cloud-arrow-up"></i>
                <span>Data Eviden Upload</span>
            </button>
        </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 py-6">

        <div class="bg-amber-50 border-l-4 border-amber-500 p-4 mb-6 rounded-r-lg shadow-sm text-sm">
            <div class="flex items-start">
                <div class="flex-shrink-0 text-amber-500 mr-3">
                    <i class="fa-solid fa-triangle-exclamation text-lg"></i>
                </div>
                <div>
                    <span class="font-bold text-amber-900">Cara kerja penilaian:</span> 
                    Vonis dibangun dari sinyal yang ada di data SPBU: subsidi tanpa nopol, akumulasi harian melewati kuota, dan isi ulang beruntun. 
                    <strong>Perkiraan jenis</strong> dari angka plat (<code>ESTIMASI PLAT</code>) hanya jadi <strong>lead "cek plat palsu"</strong> bila janggal — mis. angka plat $\neq$ motor tapi mengisi Solar. 
                    Foto CCTV per baris menjadi justifikasi pemeriksaan. Semua temuan wajib dikonfirmasi CCTV/SAMSAT sebelum barcode/kuota diblokir.
                </div>
            </div>
        </div>

        <div x-show="activeTab === 'ringkasan'" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
                    <p class="text-sm text-gray-500">Total Transaksi Dianalisis</p>
                    <h3 class="text-2xl font-bold mt-1 text-gray-800">1,428</h3>
                    <span class="text-xs text-green-600 font-semibold mt-2 inline-block"><i class="fa-solid fa-arrow-up"></i> Data kemarin termuat</span>
                </div>
                <div class="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
                    <p class="text-sm text-gray-500">Subsidi Tanpa Nopol</p>
                    <h3 class="text-2xl font-bold mt-1 text-red-600">14</h3>
                    <span class="text-xs text-red-600 font-semibold mt-2 inline-block">Perlu Investigasi</span>
                </div>
                <div class="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
                    <p class="text-sm text-gray-500">Lebih Kuota Harian</p>
                    <h3 class="text-2xl font-bold mt-1 text-amber-600">8</h3>
                    <span class="text-xs text-amber-600 font-semibold mt-2 inline-block">Indikasi Pengetatan</span>
                </div>
                <div class="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
                    <p class="text-sm text-gray-500">Isi Ulang Beruntun</p>
                    <h3 class="text-2xl font-bold mt-1 text-purple-600">5</h3>
                    <span class="text-xs text-purple-600 font-semibold mt-2 inline-block">Aktivitas Mencurigakan</span>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
                <i class="fa-solid fa-chart-column text-4xl text-gray-300 mb-3"></i>
                <h3 class="font-semibold text-gray-700">Analisis Grafik Tren Penggunaan BBM</h3>
                <p class="text-sm text-gray-500 mt-1">Silakan unggah file CSV/XLSX hose delivery pada tab <strong>Data Eviden Upload</strong> untuk melihat grafik lengkap.</p>
            </div>
        </div>

        <div x-show="activeTab === 'detail'" class="space-y-4">
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex justify-between items-center">
                <div class="flex space-x-2">
                    <input type="text" placeholder="Cari No. Plat / Transaksi..." class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <select class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                        <option>Semua Status</option>
                        <option>Subsidi Tanpa Nopol</option>
                        <option>Lewat Kuota</option>
                        <option>Isi Ulang Beruntun</option>
                    </select>
                </div>
                <button class="bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                    <i class="fa-solid fa-download mr-1"></i> Export Data
                </button>
            </div>

            <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-100 text-gray-600 text-xs uppercase tracking-wider border-b border-gray-200">
                            <th class="p-3">Waktu</th>
                            <th class="p-3">No. Plat / Estimasi</th>
                            <th class="p-3">Jenis BBM</th>
                            <th class="p-3">Volume</th>
                            <th class="p-3">Indikasi Temuan</th>
                            <th class="p-3 text-center">Eviden CCTV</th>
                            <th class="p-3 text-center">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 text-sm">
                        <tr class="hover:bg-gray-50">
                            <td class="p-3 text-gray-500">08:14:22</td>
                            <td class="p-3 font-semibold">B 4567 XYZ <span class="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded ml-1">Motor/Solar?</span></td>
                            <td class="p-3">Solar Subsidi</td>
                            <td class="p-3">45 Liter</td>
                            <td class="p-3"><span class="bg-red-100 text-red-700 px-2 py-1 rounded text-xs font-medium">Plat Palsu / Mismatch</span></td>
                            <td class="p-3 text-center"><i class="fa-solid fa-camera text-blue-600 cursor-pointer" title="Lihat Foto CCTV"></i></td>
                            <td class="p-3 text-center">
                                <button class="text-blue-600 hover:underline text-xs font-semibold">Verifikasi</button>
                            </td>
                        </tr>
                        <tr class="hover:bg-gray-50">
                            <td class="p-3 text-gray-500">09:30:11</td>
                            <td class="p-3 font-semibold">H 1234 ABC</td>
                            <td class="p-3">Pertalite</td>
                            <td class="p-3">30 Liter</td>
                            <td class="p-3"><span class="bg-amber-100 text-amber-700 px-2 py-1 rounded text-xs font-medium">Lebih Kuota Harian</span></td>
                            <td class="p-3 text-center"><i class="fa-solid fa-camera text-gray-400"></i></td>
                            <td class="p-3 text-center">
                                <button class="text-blue-600 hover:underline text-xs font-semibold">Verifikasi</button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div x-show="activeTab === 'pengaturan'" class="space-y-6">
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 max-w-2xl">
                <h3 class="text-lg font-bold text-gray-800 mb-4">Konfigurasi Batas & Kuota BBM</h3>
                <form class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Batas Maksimal Solar Roda 4 Pribadi (Liter/Hari)</label>
                        <input type="number" value="60" class="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Batas Maksimal Pertalite Roda 4 (Liter/Hari)</label>
                        <input type="number" value="120" class="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Tenggat Waktu Isi Ulang Beruntun (Menit)</label>
                        <input type="number" value="180" class="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none">
                        <p class="text-xs text-gray-500 mt-1">Jika kendaraan mengisi ulang dalam kurun waktu kurang dari X menit, sistem akan menandainya.</p>
                    </div>
                    <button type="button" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition">
                        Simpan Perubahan
                    </button>
                </form>
            </div>
        </div>

        <div x-show="activeTab === 'eviden'" class="space-y-6">
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <div class="border-2 border-dashed border-gray-300 rounded-xl p-8 max-w-lg mx-auto bg-gray-50 hover:bg-gray-100 transition cursor-pointer">
                    <i class="fa-solid fa-cloud-arrow-up text-4xl text-blue-500 mb-3"></i>
                    <h3 class="font-semibold text-gray-700">Belum ada data yang dianalisis</h3>
                    <p class="text-sm text-gray-500 mt-1 mb-4">Upload satu file CSV/XLSX hose delivery (data kemarin) untuk mulai monitoring.</p>
                    <label class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition cursor-pointer shadow-sm">
                        Pilih File CSV / XLSX
                        <input type="file" class="hidden" accept=".csv, .xlsx">
                    </label>
                </div>
            </div>
        </div>

    </main>

    <footer class="text-center py-6 text-xs text-gray-500 border-t border-gray-200 mt-12">
        Analisis & foto berjalan sepenuhnya di browser Anda — tidak dikirim/disimpan ke server manapun. Foto hilang bila halaman dimuat ulang.
    </footer>

</body>
</html>
