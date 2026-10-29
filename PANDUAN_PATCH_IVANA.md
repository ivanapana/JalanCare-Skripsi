# Versi terbaru2.8 - alur sederhana sesuai skripsi

Baca UPDATE_REVISI_2_8.md dahulu. Kategori ditetapkan surveyor sesuai Bab1.5.2 poin14. Formulir dinas lengkap tidak lagi menjadi isian utama. Petunjuk versi2.7 dan sebelumnya di bawah adalah riwayat.

# Patch terbaru 2.7

Ikuti UPDATE_REVISI_2_7.md. Instruksi dan perbandingan versi sebelumnya di bawah merupakan riwayat. File .env, private, secrets, .venv dan best_potholes.pt tidak disertakan dalam patch.

# Panduan terbaru

Gunakan UPDATE_REVISI_2_6.md. Catatan di bawah adalah riwayat patch2.5.1; kondisi terbaru dan hasil audit ada di AUDIT_CAKUPAN_2_6.md. Akun/password demo tetap sama.

# Pembaruan berdasarkan ZIP kode Ivana — 2.5.1

Pemeriksaan: seluruh file kode pada ZIP yang kamu kirim sama dengan paket revisi 2.4. Tidak ditemukan perubahan kode tambahan pada ZIP tersebut. Folder .venv, .env, models, private, secrets tidak tersedia dalam kiriman; kondisi dan password database di laptop tidak dapat diperiksa dari ZIP ini.

## Mengapa password lama tidak diketahui?

Pada app.py versi 2.4, endpoint /demo-login/<role> membuat akun dengan secrets.token_urlsafe(24). Password acak tidak ditampilkan, dan store.py menyimpan hash password, bukan teks aslinya. Klik Demo masuk tanpa meminta password. Jadi PetugasDemo2026! memang belum menjadi password tetap pada kode yang kamu kirim. Password akun yang dibuat lewat registrasi/manajemen akun hanya diketahui pembuatnya, dan password Firebase tidak dapat ditentukan dari kode ini.

## Perbandingan dan perubahan

| Bagian | Kiriman 2.4 | Patch 2.5.1 |
|---|---|---|
| Beranda | Coba dua peran, tombol Demo warga/petugas | Seluruh bagian tersebut dihapus |
| Endpoint demo-login | Membuat sesi tanpa password | Dihapus, URL lama ditolak |
| Login petugas/warga | Form ada, akun demo tidak memiliki sandi tetap | Form tetap dipakai; akun demo diberi sandi awal yang jelas |
| Sesi demo lama | Sesi bypass masih berlaku | Sesi versi lama dikeluarkan; wajib login kembali |
| Privasi | Penandaan manual | Model wajah/plat otomatis + Gaussian blur, sesuai 2.5 |
| Gambar/model/data lama | Disimpan di laptop | Tetap dipertahankan; model pothole tidak diganti |

Halaman auth, CSS, struktur kelas, store, ekspor, lokasi, narasi, aturan Firebase, dan file lain yang sama tidak diganti di patch. Daftar tepat file pengganti tercantum di DAFTAR_FILE_PATCH.txt pada ZIP.

## Cara memasang (tidak replace seluruh proyek)

1. Hentikan server di CMD dengan Ctrl+C dan simpan cadangan folder proyek.
2. Ekstrak ZIP patch. Buka folder salin_ke_folder_proyek.
3. Salin SEMUA isi folder salin_ke_folder_proyek ke C:\Skripsi 1\Train\website_lubang_jalan_revisi_2_2. Patch hanya berisi file yang berubah atau baru. Pilih Replace untuk file tersebut.
4. models/privacy berisi model privasi tambahan. Salin folder tersebut juga. Jangan hapus atau mengganti models/best_potholes.pt. Jangan hapus .env, .venv, private atau secrets.
5. Jalankan run.bat dari folder proyek lama, lalu Ctrl+F5 di browser. VERSION/footer harus 2.5.1. Tidak perlu setup.bat atau training ulang.
6. Login petugas melalui http://127.0.0.1:5000/login/petugas. Login warga melalui http://127.0.0.1:5000/login.

## Akun demo setelah pembaruan

Jika APP_MODE=demo, pertama kali kode 2.5 dijalankan akun petugas@demo.local dan warga@demo.local dibuat/diperbarui satu kali. UID akun lama dipertahankan sehingga hubungan laporan tidak hilang. Hanya dua akun contoh tersebut yang disesuaikan; akun lain dan laporan tidak dihapus. Inisialisasi ditandai di private/demo-passwords-v2_5.initialized, sehingga password tidak direset setiap restart.

Default:
- Petugas: petugas@demo.local / PetugasDemo2026!
- Warga: warga@demo.local / WargaDemo2026!

Jika .env memiliki DEMO_STAFF_PASSWORD atau DEMO_RESIDENT_PASSWORD khusus, inisialisasi memakai nilai itu. Jangan kirim .env atau password privat ke chat. Mode Firebase tidak memakai akun/password demo: gunakan akun Firebase milikmu. Akun contoh bukan akun produksi publik.

## Hasil dan batas pengujian

Patch diuji dengan database sementara dan model/alamat pengganti untuk alur aplikasi, serta dua model ONNX privasi asli pada gambar netral. Model pothole asli, .env, database laptop dan Firebase/Gemini live tidak tersedia dalam kiriman. Browser/komputer pengguna perlu UAT. Detektor wajah/plat dapat melewatkan objek; otomatis bukan jaminan semua identitas terdeteksi.
