# Jalankan Revisi 2.2

Jika halaman masih menampilkan tiga input kiri/kanan/atas, tombol lokasi perangkat, atau checkbox kewenangan, kode lama masih dijalankan.

1. Hentikan server lama di CMD dengan Ctrl+C. Tutup tab hasil lama.
2. Ekstrak ZIP terbaru ke folder **baru**, misalnya `C:\Skripsi 1\Train\JalanCare_Revisi_2_2`.
3. Salin folder `models` dari proyek sebelumnya ke folder baru. Jika sudah punya konfigurasi/data yang ingin dipertahankan, salin `.env`, `secrets`, dan `private` juga.
4. Klik `setup.bat`, tunggu selesai. Klik `run.bat` dari folder **baru ini**.
5. Buka http://127.0.0.1:5000. Tekan Ctrl+F5 agar JavaScript terbaru dimuat.
6. Periksa bagian bawah halaman: harus tertulis **Revisi 2.2**.
7. Klik Buat laporan. Harus ada satu tombol **Pilih 3 foto**, tiga kotak pratinjau, dan panel **Lokasi dari foto**. Di pemilih file Windows, tahan Ctrl lalu klik tiga foto, lalu Open. Foto yang salah dapat dihapus dengan **Hapus foto ×**, kemudian pilih penggantinya.

Lokasi pengambilan foto dibaca dari GPS EXIF; koordinat digunakan untuk mencari nama daerah. Panel lokasi muncul sebelum analisis dan draf. Jika GPS tidak ada atau pencarian alamat gagal, penjelasan ditampilkan. Lokasi perangkat saat upload tidak digunakan.

## Kotak blur pada jalan

Detektor wajah awal dapat salah mengenali tekstur jalan sebagai wajah. Revisi 2.2 mematikan blur wajah otomatis secara default. Foto tidak diburamkan jika tidak ada area yang dipilih. Buka **Tandai area pribadi (opsional)** untuk memilih wajah/plat secara manual; **Batalkan tanda terakhir** hanya menghapus pilihan area, bukan fotonya. Perlindungan privasi otomatis penuh belum terpenuhi; catat batasan ini dalam naskah sampai detektor yang andal tersedia.

Jika `.env` milikmu berisi `AUTO_FACE_BLUR=true`, ubah menjadi `AUTO_FACE_BLUR=false` untuk perilaku ini. Pengaturan true bersifat eksperimental.

**Hasil lama yang sudah diburamkan tidak dipulihkan otomatis.** Untuk melihat hasil baru tanpa kotak blur keliru, unggah ulang foto asli dan lakukan analisis baru. Kotak biru bertuliskan Potholes adalah hasil deteksi YOLO, bukan blur; kualitasnya tetap bergantung pada bobot model.

Status Inggris: Pending verification, In progress, Completed, Rejected. Petugas dapat menolak dengan alasan wajib. Struktur halaman mengikuti wireframe dalam naskah: login/register terpusat, unggah tiga pratinjau, hasil foto/narasi dua kolom, riwayat tabel dan sidebar petugas.
