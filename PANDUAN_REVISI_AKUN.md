# Revisi footer dan pengelolaan akun

## Perubahan
- Menghapus teks revisi/draf AI dari footer bersama (beranda dan halaman lain).
- Hanya UID petugas utama yang dapat membuka /users dan melakukan create/update/delete.
- Petugas lain tetap dapat menangani laporan, statistik, dan ekspor; menu Kelola akun disembunyikan.
- Hak diperiksa backend pada setiap GET/POST, bukan dari input formulir atau cookie role.
- UID petugas utama tetap, tidak otomatis berpindah bila akun lain dibuat/promosi.
- Akun utama tetap tidak dapat menghapus/mengubah dirinya melalui menu ini.
- Warga: badge hijau. Petugas: badge ungu. Nama role tetap ditampilkan.

## Wajib sebelum dipasang
1. Di Firebase Console > Authentication > Users, salin UID akun petugas PERTAMA yang memang menjadi pengelola.
2. Tambahkan pada .env server (jangan unggah .env ke GitHub):
   FIRST_STAFF_UID=UID_AKUN_PETUGAS_PERTAMA
3. Salin app.py, templates/base.html, templates/users.html, static/style.css dari paket ini ke project yang sesuai, lalu restart jalancare.
4. Uji login petugas utama: dapat membuka Kelola akun dan mengelola akun uji.
5. Uji petugas lain: menu tidak muncul, akses /users ditolak 403, fungsi laporan tetap dapat digunakan.

UID tidak dipilih otomatis karena ZIP tidak berisi identitas Firebase produksi yang dapat membuktikan akun pertama. Jika konfigurasi kosong/salah, pengelolaan akun ditolak untuk semua pengguna; pelaporan tetap tersedia. Petugas utama harus masih ber-role petugas dan aktif. Tidak ada skema database atau role baru.

Jangan timpa .env, private/, secrets/, atau model produksi. Paket tidak menyertakan data runtime, kredensial, dan riwayat Git. Ini revisi berdasarkan ZIP unggahan, bukan bukti bahwa server sudah diperbarui. Masalah OOM/worker SSE pada server sebelumnya tidak diubah oleh paket ini.

## Validasi
- Sintaks app.py dan test: lulus compileall.
- 56 test lokal lulus; termasuk pembatasan GET/POST create/update/delete, role warga, menu, badge, kompilasi semua template, dan alur laporan dengan detector uji.
- Percobaan suite lengkap awal: 55 lulus, 6 gagal. Satu assertion footer lama disesuaikan dengan permintaan penghapusan dan lulus pada run akhir. Lima test lain terblokir modul google-genai/google-cloud-firestore dan model ONNX yang tidak tersedia; lima test tersebut dikecualikan pada run akhir, tidak dinyatakan lulus.
- Firebase/Supabase/Gemini produksi, model YOLO asli, dan deployment server belum diuji end-to-end. Detector uji pada test lama bukan pengganti model aplikasi.
