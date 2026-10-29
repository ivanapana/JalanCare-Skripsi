# Pengujian revisi2.8

11 tes unittest lulus:8 tes skema/ekspor versi2.7 yang dipertahankan untuk data lama dan3 tes tambahan untuk alur sederhana (template tidak menyertakan formulir dinas lengkap; Excel hanya3lembar pothole; PDF berupa laporan indikasi lubang). Tes narasi memeriksa tidak ada daftar retak atau data survei rekaan.

KompilasiPython dan pemeriksaan sintaksJavaScript dijalankan. PDF ringkas diekspor dan dirender untuk pemeriksaan visual. Pemeriksaan template adalah pemeriksaan sumber, bukan bukti halaman berhasil dirender oleh Jinja.

Flask/Jinja2/pytest/OpenCV tidak tersedia, sehingga32tes integrasi dari versi2.6 tidak dijalankan ulang pada revisiini. Browsernyata, Firebase, Gemini, modelpothole dan database laptop belum diuji. Uji loginpetugas -> detail -> simpanstatus tanpa pengukuran -> cek kategori manual -> eksporPDF/Excel di laptop sebelum dipakai.
