# Revisi 2.8: kembali ke cakupan skripsi Ivana

Yang benar menurut Bab1.5.2 naskah Skripsi2_V15:
- Poin1, halaman15: model mendeteksi pothole; retak dan kerusakan lain di luar lingkup deteksi.
- Poin6, halaman16: hasil otomatis adalah draf awal; validasi akhir oleh surveyor/staf teknis.
- Poin7 dan9, halaman16: ukuran fisik tidak diukur otomatis dari foto; hasil ukur dimasukkan surveyor.
- Poin14, halaman17: kategori kondisi jalan merupakan kewenangan surveyor; sistem tidak menilainya otomatis.

Formulir dinas lengkap adalah referensi format. Bukan berarti semua kolom survei perkerasan, retak, alur, bahu, saluran dan lain-lain harus menjadi fitur wajib website pothole. Revisi2.7 menampilkan terlalu banyak isian; revisi2.8 menyederhanakannya tanpa mengubah naskah.

## Alur sekarang
1. Warga unggah3foto. Sistem mendeteksi lubang, membaca lokasiEXIF dan membuat draf narasi. Laporan awal langsung tersimpan; tidak menunggu pengisian survei lengkap.
2. Petugas melihat laporan lalu mengubah status, memberi catatan dan menetapkan kategori jika sudah ada hasil pemeriksaan. Kategori dapat dibiarkan Belum dinilai.
3. Hanya alasan Ditolak atau catatan Selesai yang wajib pada status terkait. Pengukuran, jumlah lubang unik, nilaiSDI dan prioritas bersifat opsional, tersedia dalam bagian yang dapat dibuka.
4. Tidak ada lagi formulir retak/bahu/saluran/perkerasan/STA pada halaman utama. Ringkasan data pemeriksaan juga dapat dilipat.
5. EksporPDF/Excel utama berisi laporan indikasi lubang dan hasil verifikasi yang tersedia. Sistem tidak mengisi ukuran/SDI/kategori berdasarkan confidence dan tidak menghitung persentase kondisi seluruh ruas dari foto laporan.

Kategori masih ditetapkan petugas. Validasi kecocokan kategori dengan SDI yang diisi bukan perhitungan/penetapan kategori otomatis. Kode lama Rusak tetap tersimpan; label Rusak Ringan mengikuti istilah dinas. Petugas tidak wajib melakukan survei menyeluruh untuk membuat/menerima laporan awal.

## Cara pasang
1. Hentikan serverCMD dengan Ctrl+C. Cadangkan folder proyek.
2. EkstrakZIP. Buka salin_ke_folder_proyek, salin ISINYA ke folder yang berisi app.py:
   C:\Skripsi 1\Train\website_lubang_jalan_revisi_2_2
3. Replace file patch yang sama namanya. Jangan menghapus seluruh folder proyek. File .env, private, secrets, .venv dan models/best_potholes.pt tidak disertakan patch.
4. Jalankan:

```bat
cd /d "C:\Skripsi 1\Train\website_lubang_jalan_revisi_2_2"
.venv\Scripts\python.exe app.py
```

5. Muat ulang halaman, cek footer2.8. Loginpetugas dan buka detail laporan. Bagian formulir dinas lengkap harus sudah tidak tampil. Pilih satu status dan isi catatan sesuai kebutuhan, biarkan pengukuran kosong, simpan. Coba juga unduhPDF/Excel.

Tidak perlu melatih ulang YOLO atau membuat ulang akun. Revisi ini tidak mengganti password. Data survei yang sudah disimpan versi2.7 tetap berada di database. Ekspor lengkap versi2.7 pada URL lama tetap dilindungi loginpetugas, tetapi tidak menjadi menu/alur utama. Narasi historis tetap tersimpan dan tidak ditulis ulang; narasi versi2.7 yang panjang ditutup secara default pada halaman detail. Dokumen UPDATE2.7 merupakan riwayat, bukan petunjuk alur terbaru.

## Pengujian
11 tes unit skema/ekspor/narasi dan pemeriksaan sumber template lulus. KompilasiPython dan sintaksJavaScript lulus; contohPDF ringkas diperiksa visual. Flask/Jinja2/pytest/OpenCV tidak tersedia di lingkungan pemeriksaan, sehingga pengujian alur browser, integrasiFlask/Firebase/Gemini dan model asli belum dijalankan ulang. Uji langkah5 pada laptop sebelum dipakai.
