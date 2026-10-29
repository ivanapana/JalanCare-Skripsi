# Versi terbaru2.8 - alur sederhana sesuai skripsi

Baca UPDATE_REVISI_2_8.md dahulu. Kategori ditetapkan surveyor sesuai Bab1.5.2 poin14. Formulir dinas lengkap tidak lagi menjadi isian utama. Petunjuk versi2.7 dan sebelumnya di bawah adalah riwayat.

# JalanCare Revisi 2.7 - formulir dinas

Baca UPDATE_REVISI_2_7.md untuk pemasangan patch dan pengisian formulir. Ekspor dinas tersedia; nilai survei/SDI diisi petugas. Petunjuk berikut mempertahankan riwayat konfigurasi versi sebelumnya.

# JalanCare — website skripsi tahap 2, revisi 2.6

Website Flask untuk pelaporan lubang jalan provinsi Sulawesi Utara. Proyek ini melanjutkan prototipe YOLO milik Ivana, memakai model yang sama tanpa training ulang.

## Sudah punya website revisi sebelumnya?

Ikuti UPDATE_REVISI_2_6.md: salin seluruh file kode ke folder yang sudah terpasang dan pakai .venv lama. Tidak perlu setup.bat/unduh Torch ulang. Baca KESESUAIAN_DIAGRAM_2_4.md untuk struktur kelas dan urutan baru.

## Instalasi pertama di Windows (jika belum pernah memasang)

1. Ekstrak ZIP ke folder baru, misalnya `C:\Skripsi 1\Train\website_lubang_jalan`. Jangan menimpa prototipe lama.
2. Salin `best_potholes.pt` dari folder `models` proyek lama ke folder `models` proyek baru. Pastikan bukan `.pt.zip`.
3. Klik dua kali `setup.bat`. Tunggu instalasi selesai. Internet diperlukan. Instalasi library lebih lama daripada menjalankan website.
4. Klik dua kali `run.bat`. Biarkan jendela terbuka.
5. Buka **http://127.0.0.1:5000**.
6. Pada beranda klik Login warga/Login petugas. Mode demo lokal tetap memerlukan email/password: warga@demo.local / WargaDemo2026! dan petugas@demo.local / PetugasDemo2026!. Mode ini menyimpan data lokal, bukan Firebase.

Alternatif CMD setelah ekstrak:

```bat
cd /d "C:\Skripsi 1\Train\website_lubang_jalan"
setup.bat
run.bat
```

Setelah instalasi, perintah langsung:

```bat
.venv\Scripts\python.exe app.py
```

Hentikan dengan Ctrl+C. Setelah mengedit konfigurasi `.env`, jalankan ulang server. Jika port 5000 dipakai, hentikan aplikasi lama terlebih dahulu.

## Coba alur lengkap

1. Masuk sebagai warga. Klik Buat laporan.
2. Isi nama jalan/patokan dan keterangan jika diperlukan. Tidak ada checkbox kewenangan; petugas memeriksa kewenangan saat verifikasi.
3. Klik Pilih 3 foto dan pilih tiga file sekaligus. JPG/PNG, lebar **dan** tinggi minimal 640 piksel, maksimal 10 MB per foto. Hapus foto yang salah dengan tombol Hapus foto, lalu pilih penggantinya.
4. Wajah dan plat yang terdeteksi diburamkan otomatis sebelum simpan. Pastikan models/privacy dari paket disalin; detektor dapat melewatkan objek, jadi periksa hasil. Tidak ada menu penandaan manual.
5. GPS hanya diambil dari EXIF file asli. Tidak ada lokasi perangkat atau koordinat manual. Jika semua foto tidak memiliki GPS EXIF, unggahan ditolak. Jika beberapa foto memiliki EXIF, titik pertama dipakai dan titik lain dicek dalam radius 30 m. Koordinat dicari nama daerahnya memakai reverse geocoding OpenStreetMap/Nominatim; nama seperti Tondano ditampilkan terpisah dari Kabupaten Minahasa. Layanan bisa gagal; sistem tetap menampilkan koordinat EXIF dan menjelaskan nama daerah belum tersedia. Tidak menebak nama daerah.
6. Klik Kirim laporan & analisis foto. YOLO asli dijalankan. Setelah lokasi valid/tidak duplikat dan ada deteksi, narasi diproses, blur diterapkan, lalu laporan disimpan sebelum halaman hasil. Jika model tidak tersedia atau tidak ada deteksi, laporan tidak disimpan.
7. Periksa hasil deteksi, nomor kotak/confidence, lokasi, foto blur dan narasi pada laporan tersimpan. Pemeriksaan privasi otomatis dilakukan sebelum simpan. Laporan aktif tidak dapat diunggah ulang pada lokasi yang sama; petugas dapat menolak laporan yang tidak sesuai.
8. Edit narasi bila perlu dan klik Simpan perubahan narasi. Ini memperbarui laporan yang sama, tidak membuat laporan kedua. Status awal Menunggu Verifikasi sudah tersimpan sejak analisis berhasil.
9. Keluar; masuk sebagai petugas dengan email/password contoh. Buka detail, isi pemeriksaan lapangan, ubah status dan simpan. Status Ditolak wajib disertai alasan; alasan terlihat oleh warga.
10. Buka riwayat atau detail warga: status diperbarui otomatis lewat SSE. Mode Firebase memakai Firestore listener; demo lokal membaca SQLite tiap 1 detik. Baris baru dan angka rekap memerlukan refresh.
11. Petugas dapat memfilter tanggal/wilayah/status, melihat grafik rekap, dan mengekspor PDF/Excel berdasarkan filter.
12. Menu Akun menyediakan tambah, ubah role/data, nonaktifkan, dan hapus akun. Registrasi publik selalu role warga. Akun petugas yang sedang digunakan tidak bisa dihapus/diubah dari menu ini.

Dua laporan aktif berjarak **kurang dari 30 meter** diblokir. Status Selesai dan Ditolak tidak menghalangi pelaporan ulang. Pemeriksaan diulangi secara atomik pada saat kirim untuk menghindari pengiriman bersamaan. Sistem memakai perkiraan batas koordinat Sulawesi Utara; belum memiliki database ruas jalan provinsi untuk memverifikasi kewenangan otomatis.

## Hubungkan Firebase setelah website lokal berjalan

Jangan kirim service-account JSON atau API key Gemini ke chat. Simpan hanya di komputer/proyek ini. File `.env`, folder `secrets`, dan `private` dikecualikan dari Git.

1. Buka https://console.firebase.google.com/ dan buat proyek untuk skripsi.
2. Buka **Authentication → Get started → Sign-in method**, aktifkan **Email/Password**.
3. Buka **Firestore Database → Create database**. Pilih Firestore Standard/native yang sesuai. Pilih lokasi dengan sadar karena lokasi database tidak mudah diubah. Gunakan aturan aman; aplikasi memakai Admin SDK server, sehingga browser tidak memerlukan akses langsung.
4. Pada tab **Rules** Firestore, salin isi `firestore.rules`, lalu Publish. Aturan ini menolak akses langsung browser; server Flask tetap dapat membaca/menulis melalui service account dan memeriksa hak akses.
5. Buka **Project settings → General → Your apps**, daftarkan aplikasi Web bila belum ada. Ambil nilai `apiKey` dari Firebase config. Itu menjadi `FIREBASE_WEB_API_KEY`.
6. Buka **Project settings → Service accounts → Generate new private key**. Simpan JSON di `secrets/firebase-service-account.json`. File ini privat; jangan upload ke GitHub/chat.
7. Buka `.env` dengan Notepad (file dibuat oleh setup.bat). Isi:

```dotenv
APP_MODE=firebase
FIREBASE_CREDENTIALS=secrets/firebase-service-account.json
FIREBASE_WEB_API_KEY=ISI_APIKEY_FIREBASE
FIREBASE_STORAGE_BUCKET=
```

8. Di **Authentication → Users → Add user**, buat akun petugas pertama dengan email/password milikmu. Jangan gunakan akun demo.
9. Di CMD dalam folder proyek jalankan, ganti email:

```bat
.venv\Scripts\python.exe initialize_staff.py --email "email-petugas-anda@example.com"
```

Skrip membuat profil `pengguna/{uid}` dengan role petugas bagi akun Authentication yang sudah dibuat. Pembuatan petugas berikutnya melalui menu Akun.

10. Jalankan ulang `run.bat`. Banner demo hilang. Registrasi warga dan login sekarang menggunakan Firebase Authentication; laporan disimpan ke Firestore.

**Dengan bucket kosong, foto tetap disimpan lokal di komputer server.** Ini mode transisi untuk menghubungkan Auth/Firestore dahulu, belum memenuhi penyimpanan foto cloud di skripsi. Data demo tidak otomatis dipindahkan ke Firebase. Buat laporan uji baru setelah koneksi Firebase aktif.

### Aktifkan Cloud Storage untuk memenuhi rancangan akhir

Cloud Storage Firebase saat ini mensyaratkan **Blaze (pay-as-you-go)**. Blaze masih dapat memberikan kuota tanpa biaya, tetapi bukan jaminan semua penggunaan gratis. Aktivasi billing dilakukan sendiri setelah memahami tarif; aplikasi ini tidak mengaktifkannya otomatis. Pasang pemantauan anggaran; peringatan anggaran bukan batas keras biaya.

1. Setelah siap memakai billing, buka Storage → Get started dan buat bucket.
2. Salin nama bucket tepat dari console, misalnya `nama-proyek.firebasestorage.app` (tanpa `gs://`). Jangan menebak nama.
3. Isi `FIREBASE_STORAGE_BUCKET=nama-bucket` di `.env`.
4. Salin `storage.rules` ke aturan Storage dan Publish. Jangan membuat foto publik.
5. Jalankan ulang aplikasi, buat laporan baru, periksa folder `laporan/{idLaporan}` di Storage dan dokumen Firestore.

Foto asli yang belum diblur tidak ditulis ke disk atau cloud. Sistem menyimpan tiga foto blur `foto_foto1.jpg`, `foto_foto2.jpg`, `foto_foto3.jpg` dan tiga visual hasil deteksi untuk pemeriksaan. URL `gs://` adalah referensi privat, bukan URL publik. Foto ditampilkan melalui Flask setelah pemeriksaan pemilik laporan/role petugas.

## Aktifkan Gemini setelah alur pelaporan tersimpan

1. Buka https://aistudio.google.com/api-keys dan buat API key sesuai proyek/aksesmu.
2. Di `.env`, isi `GEMINI_API_KEY` dan nama model yang tersedia pada akun. Default kode `gemini-2.5-flash` mengikuti naskah; ketersediaan dan kuota dapat berubah.
3. Jalankan ulang aplikasi. Buat laporan baru dan cek label sumber draf pada halaman tinjau: **Gemini** jika berhasil.
4. Jika key kosong, quota/API gagal, atau struktur JSON tidak valid, sistem memakai **template**, menampilkan sumber secara jujur, dan tidak mengklaim output itu hasil Gemini.

Gemini menerima teks terstruktur: deteksi per foto, confidence, bounding box, lokasi, waktu, nama jalan, wilayah, dan keterangan. Foto serta identitas/email pelapor tidak dikirim ke Gemini. Draf selalu bahasa Indonesia walaupun UI Inggris. Respons divalidasi bentuk/tipe/panjang; kebenaran isinya tetap perlu diperiksa manusia. Draf tidak boleh dipakai sebagai nilai SDI resmi.

## Hubungan implementasi dengan naskah

Lihat `CAKUPAN_DAN_CATATAN_SKRIPSI.md` untuk fitur, penyesuaian yang perlu dibahas dengan pembimbing, dan batas validasi. Jangan menyebut seluruh sistem sudah diuji hanya karena model mencapai mAP50 81,71% pada evaluasi sebelumnya.

## Struktur file

- `app.py`: Flask, login, hak akses, proses laporan, media privat, status, akun, ekspor.
- `store.py`: SQLite demo dan Firebase Auth/Firestore/Storage adapters.
- `vision.py`: validasi foto, GPS EXIF, deteksi YOLO, blur, visualisasi.
- `narrative.py`: prompt Gemini dan fallback draf.
- `templates/`, `static/`: UI responsif, pilihan bahasa, alat seleksi blur.
- `initialize_staff.py`: profil petugas pertama.
- `models/`: bobot milikmu.
- `private/`: data lokal dan draf (jangan bagikan).
- `secrets/`: credential Firebase privat.

## Validasi teknis dan langkah sebelum publikasi

Paket diuji menggunakan detector pengganti **hanya dalam unit/integration tests**, agar alur hak akses, duplikat, status, dan ekspor dapat diverifikasi tanpa mengaku telah melakukan inference asli di lingkungan pengembang. Aplikasi pengguna tidak memiliki inference palsu. Inference asli memakai bobotmu yang harus disalin sendiri.

Jalankan tes bila ingin:

```bat
.venv\Scripts\python.exe -m pip install pytest
.venv\Scripts\python.exe -m pytest tests -q
```

Integrasi live Firebase/Gemini perlu diuji setelah konfigurasi akun pengguna; tidak diuji live tanpa credential. Belum dipublikasikan. Untuk hosting diperlukan server Python yang mendukung PyTorch/YOLO; Firebase Hosting saja tidak menjalankan Flask/YOLO. Sebelum publikasi: aktifkan APP_MODE=firebase, HTTPS, COOKIE_SECURE=true, SECRET_KEY acak, server WSGI (waitress), penyimpanan cloud, dan verifikasi UAT. Pembatasan percobaan login saat ini per proses, cocok pengujian satu server; gunakan penyimpanan rate-limit bersama jika memperbanyak worker. Data rekap saat ini dibaca server dan difilter dalam memori; perlu pagination/agregasi untuk skala besar. Draf lokal sementara masih diperlukan untuk proses tinjau, sehingga deployment beberapa server memerlukan shared temporary storage/sticky session.

## Referensi konfigurasi resmi

- https://firebase.google.com/docs/auth/admin/manage-cookies
- https://firebase.google.com/docs/storage/faqs-storage-changes-announced-sept-2024
- https://firebase.google.com/docs/admin/setup
- https://ai.google.dev/gemini-api/docs/structured-output

## Memperbarui versi sebelumnya tanpa kehilangan model/konfigurasi

1. Hentikan server lama dengan Ctrl+C.
2. Buat salinan folder proyek sebagai backup.
3. Ekstrak ZIP terbaru ke folder baru.
4. Salin folder `models`, file `.env` bila sudah dikonfigurasi, dan folder `secrets` dari versi lama. Untuk mempertahankan laporan demo dan foto lokal, salin juga folder `private`.
5. Jalankan `setup.bat` dan `run.bat` di folder baru. `.env` yang sudah ada tidak ditimpa setup.
6. Laporan lama tetap bisa dibuka termasuk foto yang dahulu dinamai kiri/kanan/atas. Draf yang belum dikirim sebaiknya diunggah ulang setelah pembaruan.

## EXIF dan nama daerah

Lokasi perangkat saat upload tidak diakses. File GPS EXIF memuat koordinat, bukan nama daerah. Nama daerah dihasilkan dari pencarian koordinat pada layanan peta. Titik GPS dikirim ke layanan geocoding; foto tidak dikirim. Alamat adalah perkiraan dari data peta, bukan bukti kewenangan ruas jalan. Atribusi OpenStreetMap ditampilkan. Caching serta batas satu permintaan per detik digunakan pada satu proses server. Jika deployment beberapa proses, gunakan rate limiter bersama atau penyedia geocoding yang sesuai.

`GEOCODER_URL` dapat diubah di `.env` untuk penyedia Nominatim lain. `GEOCODER_USER_AGENT` mengidentifikasi aplikasi. Referensi: https://operations.osmfoundation.org/policies/nominatim/ dan https://nominatim.org/release-docs/latest/api/Reverse/.

Filter Tondano mencocokkan daerah/alamat Tondano, sementara kabupaten administratifnya tetap Minahasa. Jika layanan peta tidak memberikan nama Tondano, sistem tidak memaksakan label tersebut.

## Revisi 2.2

Baca `UPDATE_REVISI_2_2.md` untuk memastikan kode terbaru dijalankan dan cache browser dimuat ulang. Panel lokasi GPS/nama daerah sekarang dapat dilihat sesudah tiga foto dipilih, sebelum analisis. File asli dikirim ke server untuk membaca EXIF; foto tidak disimpan pada tahap pemeriksaan lokasi. Blur otomatis default mati; hanya penandaan pengguna yang diterapkan.

## Revisi 2.3

Baca UPDATE_REVISI_2_3.md. Gunakan instalasi .venv lama; tidak ada dependensi baru. Foto dapat diperbesar pada halaman yang sama dan label diperbesar tanpa mengubah bobot. Peta mengirim origin sesuai kebijakan penyedia, disertai daftar titik sebagai alternatif. Tampilan EN memiliki ringkasan fakta Inggris dan laporan asli Indonesia.

## Revisi 2.4 berdasarkan diagram

Struktur kelas mengikuti class diagram; login warga/petugas terpisah; logout ke login; pipeline menyimpan laporan sebelum hasil; listener status; kategori pemeriksaan manual; alias field laporan dan kompatibilitas data lama. Baca KESESUAIAN_DIAGRAM_2_4.md untuk batas implementasi serta tambahan berdasarkan revisimu.

## Revisi 2.5

Baca UPDATE_REVISI_2_5.md. Login demo tanpa password dihapus. Deteksi wajah/plat memakai dua model pretrained tambahan, dengan Gaussian blur OpenCV. Model privasi, sumber dan lisensi disertakan di models/privacy; ini terpisah dari model lubang jalan yang kamu latih. .env lama AUTO_FACE_BLUR tidak dipakai lagi; kedua pemeriksaan otomatis wajib.

## Revisi 2.6

Validasi formulir menggunakan pesan website; kategori mengikuti empat label SDI dalam naskah; draf terstruktur berlabel sementara; data survei terbaru terpisah; peta detail dan rekap/baris baru otomatis. Mode Firebase memerlukan Storage dan Gemini untuk pengiriman laporan. Baca AUDIT_CAKUPAN_2_6.md, FORMAT_LAPORAN_DINAS.md dan UPDATE_REVISI_2_6.md. Naskah tidak diubah.
