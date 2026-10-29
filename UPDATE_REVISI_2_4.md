# Pasang revisi 2.4 sesuai diagram

1. Hentikan server lama di CMD dengan Ctrl+C.
2. Ekstrak ZIP baru ke folder sementara. Buka folder website_lubang_jalan di dalamnya sampai terlihat app.py, services.py, controllers.py, models_data.py, realtime.py, static dan templates.
3. Salin SEMUA isi folder tersebut ke C:\Skripsi 1\Train\website_lubang_jalan_revisi_2_2. Pilih Replace file kode yang sama. Jangan hapus folder lama; pertahankan .venv, .env, models, private, secrets milikmu. File baru services.py/controllers.py/models_data.py/realtime.py harus berada sejajar app.py.
4. Jalankan run.bat di folder lama, lalu Ctrl+F5 di browser. Footer harus Revisi 2.4.

Dependensi requirements tidak berubah; gunakan .venv lama, tidak perlu instal ulang atau training ulang.

Perubahan penting: tombol Kirim laporan & analisis foto langsung menyimpan laporan setelah proses berhasil, sebelum menampilkan hasil, sesuai diagram. Sesudah hasil tampil tombol narasi hanya memperbarui narasi laporan tersebut. Laporan aktif duplikat tetap ditolak.

Login warga: http://127.0.0.1:5000/login . Login petugas: http://127.0.0.1:5000/login/petugas . Akun harus memiliki role yang sesuai di database. Logout kembali ke login.

Kategori kerusakan diisi petugas dari hasil pemeriksaan, bukan nilai confidence. Pembaruan status otomatis ada di halaman detail dan riwayat; Firebase menggunakan listener, demo lokal memakai SQLite. Angka rekap dan baris laporan baru diperbarui ketika halaman dimuat ulang.

Kode integrasi Firebase/Gemini tersedia tetapi harus dikonfigurasi dan diuji dengan akun/proyek milikmu. Baca KESESUAIAN_DIAGRAM_2_4.md untuk pemetaan lengkap dan batas yang masih perlu diperiksa.
