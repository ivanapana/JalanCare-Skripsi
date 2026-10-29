# Revisi 2.3

1. Hentikan website di CMD dengan Ctrl+C.
2. Ekstrak ZIP ini ke folder sementara. Salin isi folder website_lubang_jalan ke folder website yang sudah berjalan, pilih Replace untuk file kode. Pertahankan .venv, models/best_potholes.pt, .env, secrets, dan private milikmu. Jangan menghapusnya.
3. Jalankan run.bat di folder website yang sudah terpasang. Tidak perlu instal ulang requirements; dependensi tidak berubah.
4. Di browser tekan Ctrl+F5. Footer harus menampilkan Revisi 2.3.
5. Label hasil lama maupun baru digambar ulang dari kotak yang sudah tersimpan, tanpa training atau prediksi ulang. Tekan gambar untuk membuka pembesaran pada halaman, gunakan +/− dan gulir, tutup dengan tombol atau Esc.

EN menerjemahkan status, wilayah belum teridentifikasi, pemberitahuan duplikat, dan disclaimer. Ringkasan fakta hasil deteksi tersedia dalam Inggris. Narasi asli tersimpan dan ekspor administratif tetap bahasa Indonesia; narasi edit pengguna/Gemini tidak diklaim diterjemahkan otomatis.

Peta: kebijakan referrer diperbaiki agar browser mengirim origin website ke penyedia tile. Data titik tetap tersedia melalui daftar lokasi dan tautan peta apabila penyedia memblokir koneksi. Jika pemblokiran tetap terjadi, gunakan penyedia tile berizin dengan mengatur MAP_TILE_URL dan MAP_ATTRIBUTION di .env sesuai layanan penyedia; jangan menyamarkan identitas atau memakai proxy untuk melewati blokir.

Deteksi: perubahan tampilan tidak mengubah bobot model atau confidence. Lubang besar yang tidak terdeteksi adalah false negative jika objek memang lubang menurut anotasi/pemeriksaan. Ukuran tidak menjamin confidence. Air, pantulan, sudut, dan perbedaan foto dari data latihan merupakan dugaan yang perlu diuji. Simpan foto asli, bobot, confidence dan hasil prediksi untuk evaluasi; jangan mengklaim semua lubang terdeteksi atau melatih ulang sebelum audit anotasi.
