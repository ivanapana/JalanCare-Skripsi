# Tambahan audit 2.7

Implementasi tambahan berdasarkan formulir dinas yang diberikan: survei aspal manual lengkap empat kelompok, metadata ruas/STA/surveyor, pengukuran diameter, klasifikasi kecil/besar-dangkal/dalam, label kondisi Rusak Ringan yang kompatibel dengan kode Rusak, PDF empat kelompok dengan lampiran, Excel analisis/rekap/legenda, sumber PDF terlindung login petugas.

Deteksi YOLO tetap satu kelas pothole. Retak, bekas roda, bahu, saluran dan lainnya merupakan input surveyor, tidak ditambahkan sebagai hasil deteksi model. Tidak ada perhitungan diameter/depth/SDI dari foto atau confidence. Formula SDI otomatis belum tersedia karena acuan tidak memuat formula lengkap.

Narasi lama, data pengguna, bobot model dan konfigurasi laptop tidak dimigrasikan/dihapus. Perubahan hanya kode/asset yang tercantum patch. Jika kode pengguna setelah ZIP terakhir berubah, bandingkan file terkait sebelum Replace.

Batas pengujian terkini tercantum di HASIL_PENGUJIAN.md; audit2.6 tetap sebagai riwayat dan tidak menandakan seluruh revisi2.7 sudah diuji di browser/Firebase.
