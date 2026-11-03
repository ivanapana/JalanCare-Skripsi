# JalanCare — revisi UI/UX

Basis: ZIP `website_lubang_jalan_revisi_2_2 - Copy(3).zip` yang diunggah pengguna. Ini revisi project Flask asli, bukan aplikasi terpisah. Tanggal pengerjaan: 3 November 2026.

## Jalankan di Windows / VS Code

1. Ekstrak paket dan buka folder yang berisi `app.py`.
2. Gunakan Python environment project yang sudah berfungsi. Untuk environment baru:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Salin konfigurasi `.env` dan folder `secrets` MILIKMU dari project lama ke folder lokal ini. File tersebut sengaja tidak dibagikan. Jangan menimpa konfigurasi cloud dengan `.env.example`. Pastikan `APP_MODE=firebase` bila menggunakan data Firebase. Jika ingin demo lokal terpisah, gunakan `APP_MODE=demo` (tidak menggunakan data produksi).
4. Pertahankan model YOLO terlatih pada lokasi `MODEL_PATH`, atau `models/best_potholes.pt`. Bobot pothole terlatih tidak ditemukan di ZIP sumber, sehingga harus menggunakan bobot milikmu. Dua model privasi ONNX yang ada pada unggahan dipertahankan beserta lisensinya.
5. `FIRST_STAFF_UID` tetap harus berisi UID Firebase akun petugas pertama yang berhak mengelola akun. Konfigurasi kosong menolak akses pengelolaan akun; jangan menghapus pemeriksaan ini.
6. Jalankan:

```powershell
.\.venv\Scripts\python.exe app.py
```

7. Buka http://127.0.0.1:5000 . Jika server lama masih berjalan, hentikan terminalnya dengan Ctrl+C dahulu. Gunakan Ctrl+Shift+R jika tampilan lama masih tersimpan di browser.

Tidak ada frontend build/npm yang diperlukan. Teknologi tetap Flask, Jinja, CSS, dan JavaScript biasa.

## Jika dipasang ke server

Backup source dan konfigurasi terlebih dahulu. Paket belum di-deploy. Gunakan direktori baru atau salin file yang tercatat pada laporan perubahan; jangan menimpa `.env`, `secrets`, data privat, atau model terlatih. Setelah source siap, restart service `jalancare` sesuai konfigurasi server yang sudah ada.

Perubahan visual ini tidak memperbaiki keterbatasan RAM/OOM atau konfigurasi Gunicorn sync/SSE yang terlihat pada log server sebelumnya. Keandalan produksi harus diuji terpisah sebelum dipakai banyak pengguna.

## Isi hasil pekerjaan

- `LAPORAN_UIUX_DAN_PENGUJIAN.md`: audit, design system, perubahan dan batas pengujian.
- `preview/`: screenshot browser desktop/mobile serta log pemeriksaan. Akun/laporan pada screenshot adalah data uji SQLite terpisah, bukan data warga dan bukan pengganti integrasi produksi.
- Source, test, file dependensi dan referensi asli yang diperlukan tetap disertakan.
