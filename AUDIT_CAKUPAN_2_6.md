# Cakupan Skripsi2_V15 — audit implementasi 2.6

Acuan: 1.5.1–1.5.2 (hal.14–17), kebutuhan fungsional/nonfungsional (hal.83–85), use case (hal.88–98), basis data (hal.119–121), serta diagram Ivana. Naskah PDF tidak diubah.

| Cakupan | Implementasi | Bukti/batas saat ini |
|---|---|---|
| Registrasi/login/logout dua role | AuthService; warga register, petugas jalur tertutup; kredensial wajib; logout ke login | Tes akses/login dan password salah; Firebase nyata perlu konfigurasi |
| RBAC dan kepemilikan foto/laporan | Server menolak akses lintas pengguna/role | Tes backend |
| Tiga JPG/JPEG/PNG, 10MB, min640×640 | Validasi server, upload sekaligus, hapus/ganti sebelum kirim | Tes backend; UI file picker perlu UAT |
| GPS EXIF dan nama lokasi | EXIF sebelum transformasi; geocoding cached; GPS pertama yang tersedia, titik lain dicek | Tanpa seluruh GPS ditolak; API geocoder live dan foto asli perlu UAT |
| Deteksi pothole YOLOv8 fine-tuned | best_potholes.pt, boxes/confidence, nol deteksi tidak membuat laporan | Bobot/mAP aktual dan foto negatif perlu evaluasi; detector uji bukan model asli |
| Zoom dan confidence setiap kotak | Modal, zoom, nomor # per foto | JS dan render diperiksa; UAT browser diperlukan |
| Duplikasi aktif <30m | Haversine, cek awal + transaksi saat simpan | Tes rollback; concurrent Firestore live perlu uji |
| Gaussian Blur | Face YuNet dan plate YOLOv8 pretrained → Gaussian Blur OpenCV sebelum simpan | Model ONNX disertakan; detektor dapat melewatkan objek; evaluasi plat Indonesia diperlukan |
| Gemini berbasis deteksi | Prompt/JSON schema, data terbatas, narasi Indonesia dan fakta disusun aplikasi | Mode Firebase memerlukan Gemini berhasil; kegagalan membatalkan simpan. Demo boleh template berlabel |
| Draf mengacu SDI | Kolom identitas/GPS/deteksi/deskripsi/data lapangan/tindak lanjut/validasi | Tata letak sementara. Formulir dinas belum diterima; belum diklaim format resmi |
| Kategori dalam skripsi | Baik, Sedang, Rusak, Rusak Berat; petugas mengisi | Sesuai label/batas SDI pada hal.27; tidak mengestimasi kategori dari confidence |
| Dimensi, SDI, prioritas | Pengisian surveyor; data terbaru ditampilkan terpisah dari narasi awal | Tidak menebak ukuran fisik/depth/luas/SDI dari foto; prioritas ditetapkan petugas |
| Firestore dan Storage | Koleksi pengguna/laporan, reference UID, timestamps, tiga tautan foto blur | Mode Firebase memerlukan bucket; tidak diam-diam menyimpan foto lokal. Koneksi live perlu diuji |
| Riwayat/status realtime | Firestore listener → SSE, status/detail/riwayat; baris baru + rekap diambil ulang sesuai filter | Demo menggunakan SQLite; listener diuji callback pengganti, live memerlukan konfigurasi |
| Dashboard, filter, statistik/peta | Filter status/lokasi/tanggal; grafik wilayah/bulan; peta rekap dan detail | DOM live-update diuji; provider tile/geocoder tidak dijamin tersedia |
| Ekspor PDF/Excel | Filter yang sama; kolom survei/kategori/prioritas; escaping | Tes struktur berkas; belum template dokumen dinas resmi |
| CRUD akun | Tambah/ubah/hapus/nonaktifkan role server-side | Tes demo; Auth/Firestore live perlu UAT |
| Bahasa ID/EN | Menu/status/form, validasi website dan ringkasan EN; original laporan ID | User text tidak diterjemahkan otomatis; UAT bahasa diperlukan |
| Tampilan responsif | CSS responsif, modal dan error inline/summary | DOM diuji, browser desktop/mobile perlu UAT |
| Jalan provinsi Sulut | GPS rentang kasar + petugas memeriksa kewenangan; dapat Ditolak beralasan | Belum GIS otoritas otomatis; tidak menganggap semua koordinat dalam Sulut pasti jalan provinsi |

## Batas penelitian yang tidak bisa diselesaikan dengan mengganti UI

- mAP@50 minimal75%, Precision/Recall/IoU dan split dataset: harus dibuktikan dengan eksperimen/data uji. Tidak mengklaim model semua foto benar.
- Data primer Sulut, kondisi terang/tajam, jarak kamera0.5–2m, perangkat yang ditetapkan: protokol pengambilan/evaluasi, bukan jaminan dari website.
- Foto nonjalan: nol deteksi menghentikan laporan; false positive masih mungkin. Tidak ada classifier konteks jalan terpisah.
- Sudut kiri/kanan/atas tidak diverifikasi otomatis, sesuai batasan naskah. Tidak ada rekonstruksi360/stitching.
- Tidak menerima video/audio/live-stream. Mode demo lokal adalah lingkungan pengujian; produksi penuh memerlukan internet/Firebase/Gemini.
- Pelaksanaan training Kaggle vs penyebutan Colab perlu mengikuti arahan pembimbing; kode/hasil training dan naskah tidak diganti pada revisi ini.
- UAT minimal3 staf dinas, respons time dan serah terima website harus dilaksanakan dan dicatat; tes otomatis tidak menggantikannya.

## Bagian naskah yang tidak konsisten (tidak diedit)

Hal.17 menyebut tanpa anonimisasi otomatis, tetapi hal.84–85 meminta Gaussian Blur. Implementasi mengikuti Bab4 dan permintaan terbaru: privasi otomatis. Hal.93 menyebut estimasi kategori/prioritas, sedangkan Bab1 menyerahkan kategori/ukuran kepada surveyor; implementasi tidak mengarang parameter fisik. Status Ditolak dipertahankan sesuai revisi dan wireframe. jumlahDeteksi per foto dipisahkan dari jumlahLubang unik terverifikasi agar tidak menghitung lubang sama berulang.

Kategori lama Ringan/Berat tidak otomatis diubah menjadi kategori SDI; petugas memilih ulang dan kategori sebelumnya dicatat bila diperbarui. Data lama tidak dihapus.
