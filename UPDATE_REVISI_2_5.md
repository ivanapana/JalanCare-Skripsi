# Revisi 2.5 — login password dan blur otomatis

1. Hentikan server dengan Ctrl+C.
2. Ekstrak ZIP baru, buka website_lubang_jalan sampai terlihat app.py/static/templates/models.
3. Salin SEMUA isi folder itu ke C:\Skripsi 1\Train\website_lubang_jalan_revisi_2_2, pilih Replace file kode yang sama.
4. PENTING: salin juga models/privacy ke dalam models pada folder lama. Folder privacy berisi dua file ONNX dan catatan sumber/lisensi. Model best_potholes.pt milikmu tetap dipertahankan. Jangan menghapus .venv, .env, private atau secrets.
5. Jalankan run.bat, lalu Ctrl+F5. Footer Revisi 2.5. Sesi demo tanpa password versi lama akan keluar; login kembali.

Mode demo lokal (APP_MODE=demo):
Petugas: email petugas@demo.local, password PetugasDemo2026!
Warga: email warga@demo.local, password WargaDemo2026!

Login warga /login; petugas /login/petugas. Tombol pada beranda hanya menuju form, tidak memberikan sesi. Endpoint bypass /demo-login dihapus. Akun contoh lama dimigrasi satu kali ke password di atas saat revisi ini pertama berjalan. Untuk akun Firebase, gunakan akun/password Firebase sendiri; akun contoh tidak dibuat pada mode Firebase. Password contoh untuk pengujian lokal, bukan akun publik produksi.

Wajah dan plat yang terdeteksi otomatis diburamkan sebelum foto disimpan. Tidak perlu menandai manual; menu penandaan dihapus dari form. Deteksi pothole tetap memakai foto sebelum blur, sehingga blur tidak mengubah input YOLO pothole. Setelah itu hanya foto yang sudah diproses privasi disimpan. Jika salah satu model privasi hilang/gagal, simpan laporan dibatalkan. Model privasi sudah disertakan, tidak perlu training atau download Torch ulang.

Batas: detektor dapat melewatkan wajah/plat kecil, blur, tertutup atau sudut ekstrem. Periksa hasil; otomatis bukan jaminan seluruh objek privat ditemukan. Uji khusus plat Indonesia perlu dilakukan. Laporan/gambar lama tidak diberi klaim telah diproses otomatis dan tidak diubah retroaktif.
