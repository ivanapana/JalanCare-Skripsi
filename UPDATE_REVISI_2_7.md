# Revisi 2.7: formulir dinas yang diberikan

Paket ini meneruskan perubahan 2.5 dan 2.6 pada ZIP proyek Ivana yang dikirim. Naskah skripsi tidak diedit. Halaman warga tetap untuk laporan foto; formulir survei dinas tersedia bagi petugas di detail laporan.

## Pasang pada folder yang sudah dipakai

1. Hentikan server pada CMD dengan Ctrl+C. Buat salinan cadangan folder proyek sebelum menyalin patch.
2. Ekstrak ZIP patch ke folder sementara.
3. Buka `salin_ke_folder_proyek`. Salin **isi** folder tersebut ke `C:\Skripsi 1\Train\website_lubang_jalan_revisi_2_2`, di tempat `app.py` berada. Setujui Replace hanya untuk file patch yang tercantum.
4. Jangan hapus folder proyek. `.venv`, `.env`, `private`, `secrets` dan `models/best_potholes.pt` tidak disertakan dalam patch. Folder `models/privacy` berisi model privasi dari revisi sebelumnya.
5. Tidak perlu menginstal ulang Python atau melatih YOLO. Jalankan pada CMD:

```bat
cd /d "C:\Skripsi 1\Train\website_lubang_jalan_revisi_2_2"
.venv\Scripts\python.exe app.py
```

6. Buka http://127.0.0.1:5000 dan muat ulang halaman. Footer menunjukkan Revisi 2.7. Gunakan akun petugas yang sudah ada; konfigurasi login tidak diubah oleh revisi ini.

## Coba formulirnya

1. Masuk sebagai petugas, buka detail satu laporan.
2. Buka **Formulir dinas: survei kondisi jalan aspal** dalam formulir pembaruan status.
3. Isi nomor/nama ruas, status ruas, STA awal–akhir tepat 200 meter, tanggal dan surveyor berdasarkan pemeriksaan. Akses ke jalan berbeda dari status ruas; jangan disamakan otomatis.
4. Isi kode kondisi berdasarkan formulir. **Belum disurvei** berbeda dari **Tidak ada**. Memilih Tidak ada berarti surveyor telah memeriksa kondisi itu.
5. Isi jumlah lubang unik segmen jika tersedia. Aplikasi memetakan jumlah hasil survei ke kode 0 lubang → 1; 1–2 → 2; 3–9 → 3; ≥10 → 4. Kotak dari tiga foto tidak digunakan untuk hitungan ini.
6. Diameter dan kedalaman lubang yang diukur menampilkan klasifikasi kecil/besar dan dangkal/dalam setelah disimpan. Kode ukuran pada formulir segmen tetap dipilih surveyor, terutama bila ada beberapa lubang berukuran berbeda.
7. Isi SDI akhir dan tahap perhitungan dari hasil surveyor. Jika tahap bekas roda dan SDI akhir sama-sama diisi, nilainya harus sama. Pilih kategori kondisi sesuai SDI, lalu klik Simpan perubahan.
8. Buka ringkasan Formulir dinas & klasifikasi lubang, klik **Unduh formulir dinas PDF**. Ekspor Excel di dashboard memuat lembar Analisis SDI dan Rekap Ruas.

Gunakan laporan pengujian untuk uji awal; jangan mengisi data rekaan pada laporan lapangan asli. Berkas `examples/CONTOH_FORM_DINAS.pdf` hanya menunjukkan tampilan, bukan hasil survei.

## Pembatasan yang perlu dipahami

- Gemini menyusun deskripsi dan tindak lanjut sebagai lampiran; aplikasi menyusun kolom formulir dari data asli. Ukuran, nilai SDI dan prioritas bukan tebakan LLM.
- PDF meniru susunan kolom dan empat kelompok formulir, dengan label Draf digital. Tidak menyalin logo/tanda tangan atau menyatakan pengesahan dinas.
- Formula lengkap SDI tidak tersedia di PDF sampel. Penghitungan SDI otomatis belum ditambahkan; nilai dan tahap analisis dimasukkan surveyor.
- Persentase Baik/Sedang/Rusak Ringan/Rusak Berat dikosongkan bila cakupan ruas belum lengkap, terputus, tumpang tindih, atau data survei belum lengkap. Filter ekspor juga dapat membuat cakupan tidak lengkap.
- Batas kondisi SDI menggunakan batas pada naskah Ivana. Nama tampilan **Rusak Ringan** mengikuti formulir dinas, sedangkan kode data lama **Rusak** dipertahankan untuk kompatibilitas.
- Delapan tes baru untuk skema/ekspor lulus. Pemeriksaan Flask, browser, Firebase dan Gemini langsung pada revisi ini belum dapat dijalankan di lingkungan pemeriksaan; lakukan uji alur di laptop sebelum dipakai dinas.
