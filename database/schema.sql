-- =====================================================================
-- Basis Data Sistem Deteksi dan Klasifikasi Penyakit Daun Padi
-- Struktur tabel mengacu pada Class Diagram (Gambar 3.7)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS db_penyakit_padi
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_penyakit_padi;

-- Kelas Pengguna
CREATE TABLE IF NOT EXISTS pengguna (
  id_pengguna     INT AUTO_INCREMENT PRIMARY KEY,
  nama            VARCHAR(100) NOT NULL,
  email           VARCHAR(100) NOT NULL UNIQUE,
  password        VARCHAR(255) NOT NULL,
  role            ENUM('admin', 'pengguna') NOT NULL DEFAULT 'pengguna',
  tanggal_daftar  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status_aktif    TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

-- Kelas Penyakit (data referensi 4 jenis penyakit)
CREATE TABLE IF NOT EXISTS penyakit (
  id_penyakit  INT AUTO_INCREMENT PRIMARY KEY,
  kode_kelas   VARCHAR(50)  NOT NULL UNIQUE,   -- nama folder kelas pada dataset / output model
  nama         VARCHAR(100) NOT NULL,
  nama_latin   VARCHAR(150),
  deskripsi    TEXT,
  gejala       TEXT,
  penanganan   TEXT
) ENGINE=InnoDB;

-- Kelas ModelCNN
CREATE TABLE IF NOT EXISTS model_cnn (
  id_model           INT AUTO_INCREMENT PRIMARY KEY,
  nama               VARCHAR(100) NOT NULL,
  arsitektur         VARCHAR(100) NOT NULL DEFAULT 'MobileNetV2',
  versi              VARCHAR(20)  NOT NULL,
  akurasi            DECIMAL(6,4),
  path_file          VARCHAR(255) NOT NULL,
  tanggal_pelatihan  DATE,
  aktif              TINYINT(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB;

-- Kelas CitraDaun (1 pengguna -> banyak citra)
CREATE TABLE IF NOT EXISTS citra_daun (
  id_citra        INT AUTO_INCREMENT PRIMARY KEY,
  id_pengguna     INT NOT NULL,
  nama_file       VARCHAR(255) NOT NULL,
  path_file       VARCHAR(255) NOT NULL,
  ukuran_kb       DECIMAL(10,2) NOT NULL,
  tanggal_upload  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_citra_pengguna FOREIGN KEY (id_pengguna) REFERENCES pengguna(id_pengguna) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Kelas HasilDeteksi (1 citra -> 1 hasil; banyak hasil -> 1 penyakit; model menghasilkan hasil)
CREATE TABLE IF NOT EXISTS hasil_deteksi (
  id_hasil          INT AUTO_INCREMENT PRIMARY KEY,
  id_citra          INT NOT NULL UNIQUE,
  id_penyakit       INT NOT NULL,
  id_model          INT,
  confidence_score  DECIMAL(6,2) NOT NULL,       -- dalam persen
  probabilitas      JSON,                        -- probabilitas seluruh kelas
  tanggal_deteksi   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_hasil_citra    FOREIGN KEY (id_citra)    REFERENCES citra_daun(id_citra) ON DELETE CASCADE,
  CONSTRAINT fk_hasil_penyakit FOREIGN KEY (id_penyakit) REFERENCES penyakit(id_penyakit),
  CONSTRAINT fk_hasil_model    FOREIGN KEY (id_model)    REFERENCES model_cnn(id_model) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Kelas RiwayatDeteksi (histori akses hasil deteksi oleh pengguna)
CREATE TABLE IF NOT EXISTS riwayat_deteksi (
  id_riwayat     INT AUTO_INCREMENT PRIMARY KEY,
  id_pengguna    INT NOT NULL,
  id_hasil       INT NOT NULL,
  tanggal_akses  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_riwayat_pengguna FOREIGN KEY (id_pengguna) REFERENCES pengguna(id_pengguna) ON DELETE CASCADE,
  CONSTRAINT fk_riwayat_hasil    FOREIGN KEY (id_hasil)    REFERENCES hasil_deteksi(id_hasil) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Data awal: referensi 4 penyakit daun padi
-- ---------------------------------------------------------------------
INSERT INTO penyakit (kode_kelas, nama, nama_latin, deskripsi, gejala, penanganan) VALUES
('Bacterialblight', 'Bacterial Blight (Hawar Daun Bakteri)', 'Xanthomonas oryzae pv. oryzae',
 'Penyakit yang disebabkan oleh bakteri Xanthomonas oryzae pv. oryzae. Dapat menyerang sejak fase persemaian hingga menjelang panen dan menyebabkan daun mengering.',
 'Bercak berair di tepi daun yang berkembang menjadi garis memanjang berwarna kuning hingga putih keabu-abuan. Pada serangan berat daun menjadi kering dan mati (kresek).',
 'Gunakan varietas tahan (misalnya Inpari 32, Conde); hindari pemupukan N berlebihan; atur jarak tanam dan sanitasi lahan; keringkan lahan secara berkala; aplikasikan bakterisida berbahan aktif tembaga sesuai anjuran.'),
('Blast', 'Blast (Blas)', 'Pyricularia oryzae',
 'Penyakit jamur yang dapat menyerang daun, leher malai, dan batang padi. Serangan pada leher malai dapat menyebabkan bulir hampa.',
 'Bercak berbentuk belah ketupat (diamond-shaped) dengan bagian tengah berwarna abu-abu atau putih dan tepi berwarna cokelat.',
 'Gunakan benih sehat dan varietas tahan; hindari pupuk N berlebihan; tambahkan pupuk kalium; aplikasikan fungisida berbahan aktif trisiklazol atau azoksistrobin saat gejala awal.'),
('Brownspot', 'Brown Spot (Bercak Cokelat)', 'Bipolaris oryzae',
 'Penyakit jamur yang umumnya muncul pada tanaman kekurangan unsur hara atau pada lahan dengan drainase buruk.',
 'Bercak bulat hingga oval berwarna cokelat dengan bagian tengah keabu-abuan pada permukaan daun.',
 'Perbaiki kesuburan tanah dengan pemupukan berimbang (N, P, K, dan silika); gunakan benih sehat atau perlakuan benih dengan fungisida; perbaiki drainase; aplikasikan fungisida berbahan aktif mankozeb atau difenokonazol bila serangan meluas.'),
('Tungro', 'Tungro', 'Rice Tungro Bacilliform Virus (RTBV) & Rice Tungro Spherical Virus (RTSV)',
 'Penyakit virus yang ditularkan oleh wereng hijau (Nephotettix virescens). Pernah menyebabkan puso seluas 3.134 Ha di Kabupaten Kapuas pada tahun 2022.',
 'Daun berwarna kuning hingga oranye dimulai dari ujung daun, jumlah anakan berkurang, dan pertumbuhan tanaman kerdil.',
 'Tanam serempak dan gunakan varietas tahan wereng hijau; cabut dan musnahkan tanaman terinfeksi (eradikasi); kendalikan wereng hijau dengan insektisida sesuai anjuran; lakukan pergiliran varietas.')
ON DUPLICATE KEY UPDATE nama = VALUES(nama);

-- Akun administrator dan data model dibuat oleh backend/init_db.py
-- (password perlu di-hash terlebih dahulu).
