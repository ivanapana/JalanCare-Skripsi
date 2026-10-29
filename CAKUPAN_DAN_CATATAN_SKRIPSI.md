# Pemetaan terhadap Skripsi2_V15

Dibaca ulang dari naskah yang diunggah, khususnya Bab 1.5, use case Bab 4, dan rancangan koleksi pengguna/laporan. ZIP lama berisi prototipe dasar deteksi tiga foto dengan threshold 0.25; perubahan lokal pengguna di Windows tidak ada dalam ZIP yang diunggah. Paket baru memakai 0.25 sebagai nilai awal yang dapat diubah pada `.env`, bukan threshold final yang sudah dioptimasi.

| Kebutuhan naskah | Implementasi dalam paket | Yang perlu diverifikasi |
|---|---|---|
| Flask, YOLOv8n fine-tuned | Flask + lazy loading best_potholes.pt | Uji bobot asli pada komputer pengguna |
| Registrasi, login, logout, warga/petugas | Mode Firebase Auth + sesi server; demo SQLite terpisah | Uji akun live Firebase |
| UI Indonesia/Inggris | Halaman, menu, form utama dan status dua bahasa; narasi tetap Indonesia | UAT bahasa; beberapa pesan server tetap Indonesia |
| Tiga citra kiri/kanan/atas | Satu input untuk tiga foto; hapus/ganti tiap foto, pratinjau, deteksi, zoom | Sudut tidak diverifikasi otomatis, sesuai batasan naskah |
| JPG/PNG, maks 10 MB, min 640x640 | Diperiksa di server sebelum inference | HEIC harus diekspor JPG dahulu |
| GPS metadata | Pembacaan EXIF sebelum transposisi/penghapusan metadata | GPS dari EXIF saja; tanpa EXIF semua foto ditolak; nama daerah dari reverse geocoding |
| Anti-duplikasi 30 m | Haversine; hanya laporan aktif; cek atomik saat simpan | Uji GPS lapangan dan concurrent submission live |
| Gaussian Blur privasi | Revisi 2.5: wajah YuNet + plat YOLOv8n pretrained → Gaussian blur sebelum penyimpanan | Perlu UAT privasi pada wajah/plat Indonesia; otomatis tidak menjamin seluruh objek terdeteksi |
| Gemini teks terstruktur | Prompt + JSON schema + validasi struktur, fallback template transparan | Uji respons live, grounding, waktu dan quota |
| Firebase Firestore & Storage | Koleksi pengguna/laporan; bucket privat; foto lewat Flask berizin | Kredensial + billing Storage + aturan perlu dikonfigurasi |
| Riwayat dan status | Menunggu Verifikasi, Sedang Ditangani, Selesai, Ditolak; alasan penolakan wajib | Firestore listener → SSE pada detail/riwayat; demo SQLite tiap 1 detik. Uji live Firebase diperlukan. |
| Dashboard, rekap, filter | Kartu status, tabel, grafik wilayah/status/bulan, filter | Uji data realistis dan skala baca Firestore |
| Ekspor PDF/Excel | Ekspor berdasarkan filter, escaping Excel formula | Uji tampilan PDF/Excel dengan data uji |
| Petugas kelola akun | Create/update/disable/delete, role server-side | Uji Firebase Auth & Firestore live; current staff dilindungi |
| Cakupan jalan provinsi Sulut | Batas koordinat kasar + verifikasi petugas + penolakan jika di luar kewenangan | Tidak ada database GIS kewenangan ruas jalan |

## Penyesuaian metodologis yang perlu disepakati

1. Naskah menyebut pengukuran fisik dilakukan surveyor (Bab 1.5.2) tetapi contoh output Gemini mengestimasi kecil/besar, dangkal/dalam, dan prioritas dari proporsi box (Bab 2.13). Implementasi mengikuti batasan pengukuran: tidak menebak dimensi, kedalaman, SDI, maupun prioritas. Petugas memasukkan hasil survei manual. Bahas penyelarasan bagian prompt/narasi dengan pembimbing.
2. Jumlah bounding box pada tiga foto tidak sama dengan jumlah lubang unik. Field `jumlahDeteksi` berisi jumlah kotak per foto; `jumlahLubang` null sampai diverifikasi petugas. Perbaiki definisi field/narasi naskah agar tidak menghitung lubang yang sama berkali-kali.
3. Luas box terhadap seluruh gambar bukan luas lubang terhadap permukaan jalan yang terukur. Tidak ada segmentasi jalan, kalibrasi, atau depth. Jangan menyebut box area sebagai luas nyata/SDI.
4. Revisi 2.1 memakai EXIF saja sesuai permintaan pengguna. Lokasi perangkat dan input lintang/bujur dihapus. Nama daerah diperoleh dari layanan reverse geocoding, bukan EXIF itu sendiri.
5. Revisi 2.2 mematikan otomasi face-cascade secara default karena false positives pada tekstur jalan; blur wajah/plat dipilih manual. Naskah mengharapkan privasi otomatis, sehingga detektor wajah/plat yang lebih andal masih dapat menjadi pengembangan berikutnya. Klaim privasi otomatis penuh belum terpenuhi.
6. Revisi 2.4 menggunakan listener Firestore yang diteruskan melalui SSE untuk status pada detail dan riwayat. Demo menggunakan SQLite tiap 1 detik. Baris laporan baru dan angka rekap masih diperbarui saat refresh.
7. Storage Firebase sekarang membutuhkan Blaze. Estimasi layanan "gratis" pada naskah perlu diperbarui sesuai konfigurasi/kuota aktual. Paket tidak mengaktifkan billing sendiri.
8. Model satu kelas potholes tidak dapat memastikan foto di luar konteks jalan selalu ditolak: false positives masih mungkin. Tidak ada klasifikasi konteks jalan terpisah. Nol deteksi tidak membuat laporan; deteksi palsu tetap perlu verifikasi.
9. Tahap pelatihan naskah menyebut Colab, tetapi eksperimen pengguna di Kaggle. Catat lingkungan yang benar. Dataset campuran, exclusion training/test, split aktual, dan optimizer aktual harus dilaporkan; perbaikan data masih terpisah dari pekerjaan website ini.

## Checklist uji manual (catat hasil aktual, jangan diisi seolah lulus)

- [ ] Bobot asli tersedia, inference pada tiga foto sukses.
- [ ] Foto kosong, format salah, <640px, >10MB ditolak.
- [ ] Foto tanpa deteksi tidak menghasilkan laporan.
- [ ] Foto negatif diuji untuk mengidentifikasi false positives.
- [ ] GPS EXIF terbaca; lokasi perangkat tidak digunakan; nama daerah sesuai data peta.
- [ ] Wajah/plat telah blur; foto unblur tidak tersimpan.
- [ ] Draf Gemini sumber benar; kegagalan API memberi fallback berlabel.
- [ ] Warga tidak dapat mengakses laporan/foto milik warga lain.
- [ ] Warga tidak bisa menetapkan role petugas lewat registrasi.
- [ ] Laporan aktif <30m diblokir, status Selesai/Ditolak mengizinkan ulang.
- [ ] Status petugas tampil di halaman warga melalui listener/SSE.
- [ ] PDF dan Excel filter tanggal/wilayah/status benar.
- [ ] Akun dibuat/diubah/dinonaktifkan/dihapus live Firebase.
- [ ] Koleksi pengguna/laporan dan foto cloud benar-benar tersimpan.
- [ ] UAT warga/petugas sesuai jumlah responden yang disepakati naskah.

## Dasar UI revisi 2.1

Gambar 4.17–4.24 diperiksa secara visual. Login/register berpusat, unggahan tiga pratinjau, hasil/draf dua kolom, riwayat tabel, sidebar petugas, detail foto/narasi/status dan alasan penolakan, serta statistik berupa tren/peta/ringkasan. Form tetap tidak mengarang ukuran fisik, kategori ukuran, prioritas atau nilai SDI dari bounding box meskipun contoh wireframe memuat kategori tersebut. Pengukuran ditaruh pada bagian survei petugas. Status Ditolak sudah terlihat pada wireframe walaupun beberapa tabel database menyebut hanya tiga status; penyelarasan teks naskah diperlukan.

## Revisi diagram 2.4

Pemetaan kelas, fungsi dan urutan proses lengkap ada di KESESUAIAN_DIAGRAM_2_4.md. Kategori kerusakan saat ini disediakan sebagai hasil pemeriksaan petugas, tidak ditebak dari confidence. Laporan tersimpan sebelum halaman hasil sesuai sequence diagram. Tambahan sesuai revisi pengguna (blur manual, tiga foto sekaligus, Ditolak, EN ringkasan) tetap dipertahankan.

## Pembaruan 2.5

Detektor wajah/plat pretrained disertakan dan berjalan otomatis. Menu manual dihapus sesuai permintaan terbaru. Model privasi gagal/hilang membatalkan penyimpanan. Endpoint demo bypass dihapus; akun demo sekarang menggunakan password. Pernyataan manual pada bagian riwayat revisi 2.2/2.4 tidak lagi menggambarkan default 2.5.
