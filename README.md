# Program BAB IV — Deteksi dan Klasifikasi Penyakit Daun Padi (MobileNetV2)

```
program/
├── ml/                     # Pembangunan & evaluasi model (BAB 4.1 – 4.x)
│   ├── train_mobilenetv2.ipynb   # notebook (Google Colab / Jupyter)
│   ├── train_mobilenetv2.py      # isi sama, versi script
│   └── requirements.txt
├── database/schema.sql     # struktur tabel MySQL sesuai Class Diagram (Gambar 3.7)
├── backend/                # REST API Python Flask + model CNN
│   ├── app.py, config.py, db.py, auth.py, model_service.py, init_db.py
│   ├── routes/             # /api/auth, /api/detect, /api/history, /api/penyakit, /api/admin
│   ├── models/             # taruh hasil training di sini
│   └── uploads/            # citra yang diunggah pengguna
└── frontend/               # React.js (Vite)
    └── src/pages/          # halaman Pengguna & Administrator
```

---

## Langkah 1 — Training model (Google Colab, disarankan pakai GPU)

1. Unduh dataset **Rice Leaf Disease Images** (5.932 citra) dari Kaggle/Mendeley, ekstrak sehingga strukturnya:
   ```
   dataset/Rice Leaf Disease Images/Bacterialblight | Blast | Brownspot | Tungro
   ```
2. Upload `ml/train_mobilenetv2.ipynb` dan folder `dataset` ke Google Drive, buka notebook di Colab,
   aktifkan GPU (*Runtime → Change runtime type → T4 GPU*), buka komentar sel Google Drive, lalu *Run all*.
3. Lama proses dengan GPU T4 kira-kira 45–70 menit (6 eksperimen hyperparameter + training akhir +
   5-fold cross-validation). Untuk mempercepat, ubah `RUN_EXPERIMENTS = False` dan/atau `RUN_CV = False`.
   Yang perlu disalin ke backend hanya `mobilenetv2_padi.keras`, `class_names.json`, `model_info.json`
   (file `cv_fold*.keras` tidak dipakai aplikasi web).
4. Hasil:
   - `outputs/` → seluruh tabel (`.csv`) dan gambar (`.png`) untuk BAB IV
   - `saved_model/` → `mobilenetv2_padi.keras`, `class_names.json`, `model_info.json`

> **Penting:** dataset ini sudah berisi salinan augmentasi (rotasi/flip) dari ±60–115 citra asli per kelas.
> Notebook membagi data **per kelompok citra asli** (`SPLIT_MODE = 'group'`) agar tidak terjadi kebocoran data.
> Pembagian acak per file (`SPLIT_MODE = 'random'`) menghasilkan akurasi semu ±100% karena 100% citra uji
> memiliki salinan di data latih. Ekstrak dataset di `/content` (bukan Google Drive) agar tidak ada file yang hilang.

Pengaturan yang mengikuti BAB III: input 224×224×3, normalisasi [0,1], split 80:10:10 stratified,
bobot ImageNet, tahap *feature extraction* lalu *fine-tuning*, metrik akurasi/presisi/recall/F1/confusion matrix.

### Output untuk BAB IV

| File di `outputs/` | Isi | Usulan subbab |
|---|---|---|
| `tabel_4_1_distribusi_dataset.csv`, `gambar_4_1_distribusi_dataset.png` | Jumlah citra per kelas | Hasil pengumpulan dataset |
| `gambar_4_2_contoh_citra_per_kelas.png` | Contoh citra tiap penyakit | Hasil pengumpulan dataset |
| `tabel_4_2_pembagian_dataset.csv` | Jumlah data latih/validasi/uji per kelas | Pembagian dataset |
| `tabel_4_2a_citra_asli_vs_augmentasi.csv` | Jumlah citra asli vs salinan augmentasi bawaan dataset | Pembagian dataset (alasan split berbasis kelompok) |
| `tabel_4_2b_cek_kebocoran_group.csv` | Persentase citra uji yang punya salinan di data latih (harus 0%) | Pembagian dataset / validitas evaluasi |
| `gambar_4_3_contoh_augmentasi.png` | Citra asli vs augmentasi | Pre-processing |
| `tabel_4_3_parameter_model.csv` + output `model.summary()` | Jumlah parameter MobileNetV2 | Arsitektur model |
| `tabel_4_4_eksperimen_hyperparameter.csv`, `gambar_4_4_...png` | Perbandingan optimizer & learning rate | Eksperimen hyperparameter |
| `tabel_4_5_konfigurasi_pelatihan.csv` | Konfigurasi akhir & waktu training | Pelatihan model |
| `gambar_4_5_grafik_akurasi_loss.png`, `tabel_4_6_riwayat_pelatihan.csv` | Kurva akurasi & loss per epoch | Hasil pelatihan |
| `tabel_4_7a_pengaruh_tta.csv` | Metrik tanpa vs dengan Test-Time Augmentation | Evaluasi model |
| `tabel_4_7_classification_report.csv` | Presisi, recall, F1 per kelas + macro/weighted | Evaluasi model |
| `gambar_4_6_confusion_matrix.png`, `tabel_4_8_confusion_matrix.csv` | Confusion matrix | Evaluasi model |
| `tabel_4_9_tp_fp_fn_tn.csv` | TP, FP, FN, TN per kelas (untuk contoh perhitungan rumus) | Evaluasi model |
| `gambar_4_7_metrik_per_kelas.png` | Grafik metrik per kelas | Pembahasan |
| `gambar_4_8_contoh_prediksi.png`, `tabel_4_10_kesalahan_klasifikasi.csv` | Contoh prediksi & citra yang salah | Pembahasan |
| `tabel_4_11_efisiensi_model.csv` | Ukuran file & waktu inferensi | Pembahasan efisiensi MobileNetV2 |
| `tabel_4_12_cross_validation.csv` | Akurasi/presisi/recall/F1 tiap fold + rata-rata ± simpangan baku | Validasi silang (estimasi paling andal) |
| `tabel_4_13_ensemble_cv.csv` | Model tunggal vs ensemble 5 model CV pada data uji | Pembahasan |

---

## Langkah 2 — Database MySQL (XAMPP)

1. Jalankan **MySQL** dari XAMPP Control Panel.
2. Salin isi folder `saved_model/` hasil training ke `backend/models/`.
3. Di folder `backend`:
   ```bash
   pip install -r requirements.txt
   copy .env.example .env        # sesuaikan DB_USER / DB_PASSWORD bila perlu
   python init_db.py
   ```
   Script ini membuat database `db_penyakit_padi`, 6 tabel, data 4 penyakit, akun admin,
   serta mendaftarkan dan mengaktifkan model dari `model_info.json`.

Akun admin default: **admin@padi.id / admin123** (ganti lewat menu Profil).

## Langkah 3 — Menjalankan backend Flask

```bash
cd backend
python app.py            # http://localhost:5000
```
Deteksi pertama memakan waktu ±10–20 detik karena TensorFlow memuat model; deteksi berikutnya < 1 detik.

## Langkah 4 — Menjalankan frontend React.js

```bash
cd frontend
npm install
npm run dev              # buka http://localhost:5173
```

---

## Endpoint REST API

| Method | Endpoint | Fungsi | Akses |
|---|---|---|---|
| POST | `/api/auth/register` | Registrasi pengguna | Publik |
| POST | `/api/auth/login` | Login, menghasilkan token | Publik |
| GET | `/api/auth/me` · PUT `/api/auth/profil` · POST `/api/auth/logout` | Data akun, ubah profil, logout | Login |
| POST | `/api/detect` | Upload citra → pre-processing → deteksi & klasifikasi MobileNetV2 → simpan ke MySQL | Login |
| GET | `/api/history` · `/api/history/<id>` | Daftar & detail riwayat deteksi | Login |
| DELETE | `/api/history/<id>` | Hapus riwayat | Login |
| GET | `/api/penyakit` · PUT `/api/penyakit/<id>` | Informasi penyakit / edit (admin) | Login / Admin |
| GET | `/api/admin/stats` | Statistik dashboard | Admin |
| GET/POST/PUT | `/api/admin/users` | Kelola data pengguna | Admin |
| GET | `/api/admin/logs` | Log seluruh deteksi | Admin |
| GET/POST/PUT/DELETE | `/api/admin/models` | Kelola versi model CNN, aktifkan model | Admin |

## Kesesuaian dengan rancangan BAB III

| Rancangan | Implementasi |
|---|---|
| Use case Administrator: login, dashboard, kelola pengguna, kelola penyakit, log deteksi, kelola model, logout | `pages/admin/*`, `routes/admin_routes.py` |
| Use case Pengguna: login/registrasi, upload, deteksi & klasifikasi, hasil, riwayat, info penyakit, logout | `pages/Deteksi.jsx`, `Riwayat*.jsx`, `InfoPenyakit.jsx`, `routes/detect_routes.py` |
| Activity diagram login (validasi kredensial, arahkan sesuai role) | `pages/Login.jsx`, `routes/auth_routes.py` |
| Activity diagram deteksi (validasi JPG/PNG & ukuran → resize 224×224 → normalisasi → deteksi → klasifikasi → tampil + simpan) | `routes/detect_routes.py`, `model_service.py` |
| Activity diagram riwayat (ambil dari MySQL, urut terbaru, pesan bila kosong, detail) | `pages/Riwayat.jsx`, `routes/history_routes.py` |
| Class diagram: Pengguna, CitraDaun, HasilDeteksi, ModelCNN, Penyakit, RiwayatDeteksi | `database/schema.sql` |

## Skenario pengujian black-box (bahan tabel pengujian BAB IV)

| No | Skenario | Hasil yang diharapkan |
|---|---|---|
| 1 | Login dengan email & password benar (admin) | Masuk ke Dashboard Administrator |
| 2 | Login dengan email & password benar (pengguna) | Masuk ke Beranda Pengguna |
| 3 | Login dengan password salah | Muncul pesan "Email atau password salah" |
| 4 | Registrasi dengan email yang sudah terdaftar | Muncul pesan "Email sudah terdaftar" |
| 5 | Registrasi dengan password < 6 karakter | Muncul pesan validasi password |
| 6 | Upload citra format selain JPG/PNG | Muncul pesan "Format file harus JPG atau PNG" |
| 7 | Upload file > 5 MB | Muncul pesan ukuran maksimal |
| 8 | Upload citra daun Blast yang valid lalu klik Deteksi | Tampil nama penyakit, confidence score, probabilitas 4 kelas, info penanganan |
| 9 | Membuka menu Riwayat setelah deteksi | Daftar riwayat tampil urut terbaru |
| 10 | Membuka menu Riwayat tanpa pernah deteksi | Muncul pesan belum ada riwayat |
| 11 | Klik Detail pada riwayat | Tampil citra, hasil, confidence, tanggal |
| 12 | Membuka menu Informasi Penyakit | Tampil deskripsi, gejala, penanganan 4 penyakit |
| 13 | Admin menonaktifkan akun pengguna | Pengguna tersebut tidak dapat login |
| 14 | Admin mengedit data penyakit | Perubahan tampil pada halaman informasi penyakit |
| 15 | Admin menambah versi model & mengaktifkannya | Deteksi berikutnya memakai model baru |
| 16 | Pengguna biasa membuka URL `/admin` | Dialihkan ke Beranda (akses ditolak) |
| 17 | Logout | Kembali ke halaman login, token dihapus |
