# Implementasi diagram Ivana — Revisi 2.4

Acuan: classdiagram3, activity dan sequence diagram registrasi/login/logout/unggah/kelola/perbarui status yang dikirim 6 Oktober 2026. File diagram asli tidak diubah.

## Struktur kelas yang digunakan oleh aplikasi

| Kelas diagram | Implementasi | Peran |
|---|---|---|
| FlaskApp | controllers.py | Controller HTTP; handleRegistrasi, handleLogin, handleLoginPetugas, handleLogout, handleUnggahFoto, handleKelolaLaporanMasuk, handleDetailLaporan, handlePerbaruiStatus, handleRekapStatistik, handleEksporLaporan, handleKelolaAkun terhubung ke endpoint Flask. Validasi HTTP/CSRF/otorisasi dipertahankan pada adapter route di app.py. |
| AuthService | services.py | Registrasi warga; login dengan expectedRole; logout; tambah, ubah, hapus, daftar akun. |
| FirebaseService | services.py + FirebaseStore di store.py | Adapter autentikasi, akun, Firestore, duplikasi, penyimpanan foto, dan pembaruan data. LocalStore digunakan hanya sebagai pengganti demo yang diberi label. |
| LaporanService | services.py | Mengatur pipeline laporan, daftar/detail, status, statistik, ekspor. |
| YOLODetectionService | services.py + vision.py | Membaca EXIF sebelum transformasi; OpenCV menyiapkan piksel RGB/BGR; model melakukan letterbox/normalisasi inferensi; GaussianBlur OpenCV pada area pilihan. |
| GeminiReportService | services.py + narrative.py | Memanggil Gemini dengan data deteksi; respons gagal/tanpa API key memakai template yang diberi label jelas. |
| Pengguna | models_data.py | uid, nama, email, role, createdAt, toDict/fromDict. |
| Laporan | models_data.py | Atribut diagram, toDict/fromDict dan kompatibilitas nama field paket sebelumnya. |

## Urutan proses sesuai activity/sequence

Registrasi: validasi → buat akun warga → notifikasi → halaman login.

Login warga: verifikasi kredensial dan role warga → halaman Buat Laporan. Login petugas: /login/petugas → verifikasi expectedRole petugas → dashboard petugas. Role berasal dari database, bukan pilihan pengguna untuk mendapat akses.

Logout: AuthService → FirebaseService.hapusSesiAutentikasi → hapus sesi browser → halaman login. Sesi Firebase yang dicabut ditolak oleh server melalui daftar hash sesi persisten sampai batas masa berlaku 8 jam. Ini mencabut sesi aplikasi tersebut; sesi perangkat lain tidak dicabut.

Unggah: tiga file → EXIF dan praproses → cek duplikasi aktif 30 m → YOLO → berhenti jika tidak ada kotak → Gemini/template → Gaussian blur area pilihan → simpan foto dan laporan → tampilkan hasil/draf. Duplikasi diperiksa lagi dalam transaksi penyimpanan untuk mencegah dua permintaan bersamaan. Upload foto dibersihkan jika transaksi gagal.

**Menekan Kirim laporan & analisis foto sekarang menyimpan laporan sebelum halaman hasil.** Edit narasi setelah itu memperbarui laporan yang sama dan tidak menimpa status/catatan petugas. Laporan baru diberi Menunggu Verifikasi. Preview tidak lagi merupakan laporan yang belum dikirim. Preview 2.3 yang belum dikirim tetap dapat disimpan lewat tombol narasi.

Kelola: daftar laporan → pilih laporan → tampilkan foto privat, kotak/confidence, narasi, GPS → verifikasi → perbarui status.

Status: perbarui data dan waktu → Firestore on_snapshot → SSE terautentikasi → badge status/catatan pada detail dan status baris riwayat diperbarui tanpa refresh. Listener warga dibatasi ke referensi pengguna tersebut; data warga lain tidak dikirim. Listener dihentikan saat koneksi selesai. Demo lokal menggunakan pemeriksaan SQLite tiap 1 detik, bukan listener Firestore. Laporan baru dan angka rekap dashboard masih memerlukan refresh; SSE ini memperbarui status laporan yang sudah tampil.

## Data laporan dan batas interpretasi

Nama lama tetap didukung: idLaporan↔laporanId; idPengguna↔wargaId; latitude/longitude↔koordinatLat/koordinatLng; timestamp/updatedAt↔waktuDibuat/waktuDiperbarui; boundingBoxes↔boundingBox. Timestamp Firestore disimpan sebagai DateTime lalu dinormalisasi untuk UI.

citraKiri/citraKanan/citraAtas menyediakan referensi tiga slot foto untuk kompatibilitas diagram. Ini tidak membuktikan arah pengambilan: UI tetap tiga foto sekaligus dan sistem tidak mengklasifikasi sudut kamera, sesuai revisi pengguna sebelumnya. Daftar foto per slot tetap disimpan.

confidenceScores menyimpan setiap kotak; confidenceScore tunggal pada diagram diisi nilai tertinggi sebagai ringkasan. Nilai tersebut **bukan kategori kerusakan**, SDI atau kedalaman. kategoriKerusakan awal null/Belum dinilai; petugas dapat mengisi Ringan/Sedang/Berat berdasarkan pemeriksaan. Panjang/lebar/kedalaman/SDI tetap hasil survei manual, bukan karangan model.

Revisi pengguna tetap dipertahankan: tiga foto sekaligus, hapus foto sebelum upload, EXIF saja, blur manual, label nomor deteksi, zoom dalam halaman, status Ditolak dengan alasan, EN untuk UI/ringkasan fakta dan laporan asli Indonesia. Diagram lama perlu mencatat tambahan ini pada naskah final.

## Aktivasi dan pengujian

Kode Firebase, Storage dan Gemini belum berarti layanan nyata sudah aktif. Isi konfigurasi .env dan kredensial privat sesuai README. Jangan mengirim file service-account/API key ke percakapan. Foto dapat tetap lokal jika bucket belum dikonfigurasi; untuk penyimpanan cloud sesuai diagram gunakan bucket aktif. Provider peta/geocoder dan ketepatan model memerlukan uji koneksi/foto nyata.

Referensi implementasi listener: https://docs.cloud.google.com/firestore/docs/samples/firestore-listen-document dan https://github.com/GoogleCloudPlatform/python-docs-samples/blob/main/firestore/cloud-client/snippets.py . OpenCV Gaussian blur: https://docs.opencv.org/4.11.0/d4/d86/group__imgproc__filter.html .

## Pembaruan 2.5

Permintaan terbaru memulihkan privasi otomatis: YuNet mendeteksi wajah, YOLOv8n pretrained mendeteksi plat, Gaussian blur diterapkan sebelum simpan. Pemrosesan dihentikan bila model privasi gagal/hilang. Model privasi tambahan tidak menggantikan best_potholes.pt. Login demo sekarang melalui kredensial dan role yang sama dengan alur login; bypass dihapus. Menu manual penandaan dihapus. Catatan blur manual sebelumnya merupakan riwayat revisi 2.4, bukan perilaku 2.5.
