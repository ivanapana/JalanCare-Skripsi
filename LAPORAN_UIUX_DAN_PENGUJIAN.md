# Audit, implementasi, dan pengujian UI/UX JalanCare

## Ruang lingkup dan sumber

Satu sumber source code: unggahan `website_lubang_jalan_revisi_2_2 - Copy(3).zip`. Tidak ada pengambilan ulang file implementasi dari ZIP lama. Batas fungsi tetap mengacu pada project dan catatan cakupan/format laporan yang disertakan: warga/petugas, tiga foto, GPS EXIF, deteksi lubang, narasi awal, verifikasi petugas, riwayat, statistik, ekspor dan akun. Ini bukan revisi naskah skripsi; diagram/wireframe dalam naskah perlu memakai screenshot baru bila menggambarkan tampilan akhir.

Tidak menambah video, role baru, pengukuran fisik otomatis, SDI dari foto, atau identifikasi kewenangan jalan berbasis GIS. Firebase Authentication dan Firestore serta penyimpanan foto Supabase tetap menggunakan implementasi unggahan.

## Temuan dan tindakan yang diterapkan

| Temuan nyata pada source/UI | Tindakan | Bukti/file |
|---|---|---|
| Aturan `.badge:not(...)` menimpa badge role sehingga Warga/Petugas tetap kuning | Memisahkan selector role dari status, menghapus aturan fallback berlebih | `static/style.css`, preview Kelola akun, computed styles pada JSON |
| Stylesheet menumpuk tema hijau, tema biru, dan override revisi | Mengganti dengan satu stylesheet bersama dan token warna/layout | `static/style.css` |
| Dashboard mencetak `daerah · kabupaten` termasuk sentinel geocoder | Helper presentasi `location_text`, hanya menampilkan bagian lokasi yang diketahui | `app.py`, `templates/dashboard.html` |
| Statistik mengelompokkan laporan pada label lokasi yang tidak jelas | Tetap mempertahankan kelompok dan hitungan, label menjadi Wilayah belum tersedia / Area unavailable | `templates/statistics.html`, regression test data utuh |
| Detail dan popup peta dapat menerima sentinel lokasi | Fallback presentasi yang menyebut lokasi/koordinat; status laporan tidak diubah | `templates/detail.html`, `static/app.js` |
| Tabel memakai nowrap seluruh sel, area status/detail sulit dipindai pada layar kecil | Nama jalan dapat membungkus, tabel scroll terkontrol dengan petunjuk dan akses keyboard | `dashboard.html`, CSS |
| Sidebar aktif berupa blok warna dominan dan mobile menyembunyikan identitas | Navigasi aktif dengan border/indikator, ikon garis berlabel; navigasi mobile membungkus agar semua menu terlihat | `base.html`, CSS |
| Daftar akun menumpuk nama-email-role pada satu baris | Memisahkan identitas, label role di kanan, panel detail akun yang jelas | `users.html` |
| Beranda berupa teks panjang dengan ilustrasi lama disembunyikan | Hierarki manfaat dan CTA, ilustrasi SVG berlabel ilustrasi, tiga langkah sesuai alur aktual | `home.html` |
| Form/login dan hasil laporan kurang konsisten | Judul, instruksi, field, spacing, notice, tombol dan area pemeriksaan memakai komponen bersama | seluruh template utama dan CSS |
| Tidak ada skip link; tombol zoom hanya simbol | Skip-to-main, focus-visible, label zoom, aria-pressed pada tombol foto, caption tabel | `base.html`, `dashboard.html`, `detail.html`, JS |
| Submit upload dapat men-disable tombol meskipun validasi membatalkan submit | Menghormati `event.defaultPrevented`, aria-busy, reset saat pageshow | `static/app.js`, pemeriksaan browser |
| Font berpotensi bergantung jaringan Google Fonts | Menggunakan stack font sistem tanpa unduhan font tambahan | CSS |
| Cache stylesheet dapat menampilkan role warna lama | Query versi pada CSS/JS bersama | `base.html` |

## Design system yang digunakan

- Warna utama biru `#1465ae`; navy teks `#172f45`; teks sekunder `#536879`; latar `#f3f6fa`; surface putih; border `#d5dfe8`.
- Role warga teal: teks `#155e66`, latar `#e8f6f7`. Role petugas ungu: teks `#603b94`, latar `#f1edfc`. Teks role selalu ditampilkan; tidak ada nilai role/permission baru.
- Status: menunggu amber, ditangani biru, selesai hijau, ditolak merah. Role tidak memakai palet status yang sama.
- Heading 27–38 px sesuai viewport; body 15 px; label/metadata 12–14 px; tinggi tombol utama minimal 46 px. Zoom control, navigasi dan tombol sekunder memiliki focus ring.
- Spacing utama 8/12/16/20/24/32/40 px, radius input/tombol 8–9 px dan panel 12–16 px, shadow ringan.
- Grid dan breakpoint 1150/900/700/420 px; metric card menjadi dua kolom di mobile dan total satu baris; form bertumpuk; tabel digeser di dalam panel. `prefers-reduced-motion` didukung.
- Ikon garis SVG dengan label teks; ilustrasi beranda bukan foto hasil inference dan tidak memuat angka confidence/hasil eksperimen rekaan.
- Notice informasi, berhasil, peringatan, gagal, empty state, disabled, loading dan dialog mengikuti gaya bersama. Konfirmasi hapus akun native browser tetap digunakan.

## Penelusuran label lokasi

1. `location.py`: sentinel `Belum teridentifikasi` berasal dari reverse geocoding yang gagal menemukan wilayah. Tidak dihapus/diganti dalam data, cache, request/response atau database.
2. `i18n.py`: kamus lama memuat variasi huruf besar dan Unidentified. Tetap kompatibel untuk data lama. UI wilayah sekarang menggunakan helper yang menangani variasi kapitalisasi/spasi dan nilai kosong.
3. Dashboard: label wilayah kosong dihilangkan; locality yang diketahui tetap terlihat; tidak menampilkan separator menggantung atau duplikasi lokasi.
4. Statistik wilayah: kelompok yang tidak diketahui tetap dihitung, dengan teks eksplisit Wilayah belum tersedia. Tidak menghilangkan laporan dari total.
5. Detail lokasi dan popup peta: representasi yang jelas digunakan jika lokasi tidak tersedia. Koordinat dipertahankan. Kelola akun tidak memiliki field lokasi/sentinel pada source yang diperiksa.
6. Label status Menunggu Verifikasi, kategori Belum dinilai, dan nilai pengukuran Menunggu pemeriksaan dipertahankan karena memiliki arti fungsional. Semua itu bukan sentinel lokasi.
7. Narasi historis, textarea narasi asli, dan file ekspor lama tidak ditulis ulang massal. Jika teks sentinel pernah tersimpan di isi narasi pengguna/hasil lama, isi asli tetap menjadi catatan historis, bukan badge lokasi baru. Pembersihan ini bukan pengubahan fakta atau pengisian wilayah secara menebak.

## Validasi yang benar-benar dilakukan

### Lulus

- `python -m compileall -q redesign`: pemeriksaan sintaks Python.
- `node --check static/app.js` dan `static/validation.js`: sintaks JavaScript.
- **63 test pytest lulus** pada run akhir. Termasuk alur laporan dengan detector uji, CSRF, izin akses warga/petugas/petugas utama, create/update/delete, cloud-storage adapter tests, validasi narasi dengan SDK test double, ONNX privasi nyata, ekspor, lokasi dan kompilasi semua template.
- Test baru memastikan sentinel lokasi tidak muncul pada label dashboard/statistik dan nilai aslinya tetap ada di store.
- Dua test lama diperbarui: assertion slogan beranda sesuai copy baru; mock Gemini memakai `interactions.create` dan `output_text` sesuai pemanggilan aktual, bukan `models.generate_content`. Tidak mengubah integrasi Gemini produksi untuk meluluskan test.
- **24 pemuatan halaman di browser Chromium** pada lebar 1440, 768, 390 dan 320 px sesuai daftar di `preview/browser_checks.json`; 23 respons 200, satu respons 404 yang disengaja untuk memeriksa error state. Semua tidak memiliki overflow dokumen pada viewport yang diuji; tabel tetap bisa scroll secara lokal.
- **9 catatan pemeriksaan interaksi/style**: skip link keyboard, pindah fokus ke main, validasi upload kosong tidak mengunci tombol, tab foto, dialog foto/Escape, filter status, panel akun, computed warna role dan agregasi assertion. Total **33 catatan browser**, **0 error JavaScript** tercatat.
- Peta eksternal sengaja diblokir pada browser QA untuk menguji fallback saat Leaflet/tiles tidak tersedia. Daftar titik alternatif tetap dapat ditampilkan. Ini bukan bukti keberhasilan tile jaringan nyata.
- Delapan pasangan warna teks/latar yang dihitung memiliki rasio kontras di atas 4,5:1: warga 6,71; petugas 7,16; tombol utama 6,00; muted pada putih 5,79; status menunggu 6,41; selesai 6,84; ditolak 6,33; ditangani 6,01. Ini pemeriksaan pasangan warna terpilih, bukan sertifikasi WCAG penuh.
- **22 deklarasi route identik** dengan ZIP sumber. Modul `services.py`, `store.py`, `vision.py`, `privacy.py`, `narrative.py`, `photo_storage.py`, `controllers.py`, `models_data.py`, dan `location.py` identik byte dengan sumber. Perubahan Python aplikasi hanya helper presentasi dan context template; permission tidak diubah.
- Pemeriksaan akhir nama file arsip mengecualikan kredensial, konfigurasi rahasia, cache, database runtime, .git dan virtualenv.

### Masalah selama pemeriksaan yang sudah ditangani

- Test slogan lama gagal setelah copy beranda berubah: disesuaikan.
- Mock Gemini lama tidak sesuai metode SDK yang benar-benar digunakan: diperbaiki agar test memeriksa cabang sukses/gagal yang relevan.
- Browser pertama menemukan overflow mobile dari posisi elemen screen-reader di tabel: diperbaiki, pemeriksaan terakhir lulus.
- Unduhan browser otomatis awal gagal; pemeriksaan berhasil memakai Chromium headless yang kemudian tersedia. Screenshot yang disertakan dihasilkan oleh browser, bukan gambar AI/mockup.

### Belum diuji / batas bukti

- Tidak login ke Firebase/Supabase/Gemini produksi; tidak melakukan UAT dengan warga/petugas sesungguhnya.
- Tidak menguji inference model pothole terlatih karena bobot `.pt` tidak tersedia pada ZIP sumber. Screenshot deteksi memakai fixture QA, bukan bukti akurasi.
- Tidak menguji performa multiuser, latensi jaringan seluler, quota cloud, server produksi, atau pemulihan OOM.
- Belum melakukan audit screen reader penuh, audit WCAG menyeluruh, atau pengujian Safari/iOS/Firefox. Lebar viewport mobile diuji pada Chromium.
- Tidak memperbaiki konfigurasi Gunicorn/SSE atau RAM server dalam pekerjaan visual ini. Masalah tersebut memerlukan pengujian deployment terpisah.

## File utama yang diubah

`static/style.css`, `static/app.js`, `app.py` (helper presentasi/context saja), `templates/base.html`, `home.html`, `auth.html`, `dashboard.html`, `filters.html`, `users.html`, `statistics.html`, `new_report.html`, `detail.html`, `tests/test_workflow.py`.

## Penerapan dan pekerjaan tersisa

Baca `README_UIUX_REDESIGN.md`. Isi FIRST_STAFF_UID petugas utama, gunakan konfigurasi cloud dan model yang sudah dimiliki, jalankan aplikasi lokal, lalu uji akun asli warga/petugas utama/petugas lain sebelum deployment. Paket ini telah direvisi dan diperiksa lokal, belum dipasang ke server. Hasil screenshot/data QA tidak boleh dicantumkan sebagai hasil akurasi atau hasil UAT skripsi.
