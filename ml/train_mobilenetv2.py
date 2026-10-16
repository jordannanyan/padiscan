# %% [markdown]
# # Deteksi dan Klasifikasi Penyakit Daun Tanaman Padi Menggunakan CNN Berbasis MobileNetV2
#
# Notebook ini berisi seluruh tahapan pembangunan model untuk **BAB IV Hasil dan Pembahasan**:
#
# 1. Persiapan & eksplorasi dataset (Rice Leaf Disease Dataset, 5.932 citra, 4 kelas)
# 2. Pembagian dataset 80:10:10 (latih, validasi, uji)
# 3. Pre-processing (resize 224×224, normalisasi [0, 1], augmentasi)
# 4. Pembangunan model MobileNetV2 + transfer learning (bobot ImageNet)
# 5. Eksperimen konfigurasi hyperparameter
# 6. Pelatihan tahap 1 (feature extraction) dan tahap 2 (fine-tuning)
# 7. Evaluasi: akurasi, presisi, recall, F1-score, confusion matrix
# 8. Penyimpanan model untuk aplikasi web (Flask + React.js + MySQL)
#
# Semua tabel (`.csv`) dan gambar (`.png`) disimpan ke folder `outputs/` agar bisa langsung
# dimasukkan ke laporan.

# %% [markdown]
# ## 0. (Opsional) Google Colab
# Jika dijalankan di Google Colab, aktifkan GPU (*Runtime → Change runtime type → GPU*),
# lalu hapus tanda `#` pada baris di bawah untuk menghubungkan Google Drive.

# %%
# from google.colab import drive
# drive.mount('/content/drive')
# %cd /content/drive/MyDrive/skripsi_padi

# %% [markdown]
# ## 1. Import Library dan Konfigurasi

# %%
import os
import json
import time
import random
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from PIL import Image

# --- Konfigurasi utama (sesuai BAB III) ---
DATASET_DIR = Path(os.environ.get('DATASET_DIR', 'dataset'))  # folder dataset (dicari otomatis folder 4 kelasnya)
SPLIT_DIR = Path(os.environ.get('SPLIT_DIR', 'dataset_split'))   # hasil pembagian 80:10:10
OUTPUT_DIR = Path(os.environ.get('OUTPUT_DIR', 'outputs'))       # tabel & gambar untuk BAB IV
MODEL_DIR = Path(os.environ.get('MODEL_DIR', 'saved_model'))     # model untuk backend Flask

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42
SPLIT_RATIO = (0.8, 0.1, 0.1)

EPOCHS_FEATURE_EXTRACTION = int(os.environ.get('EPOCHS_FE', 20))
EPOCHS_FINE_TUNING = int(os.environ.get('EPOCHS_FT', 20))
EPOCHS_EXPERIMENT = int(os.environ.get('EPOCHS_EXP', 10))
FINE_TUNE_AT = 100            # layer MobileNetV2 ke-100 dst. ikut dilatih saat fine-tuning
FINE_TUNE_LR = 1e-5
DROPOUT = 0.5                 # dropout lebih besar untuk menekan overfitting (data asli sedikit)
LABEL_SMOOTHING = 0.1         # label smoothing pada loss agar model tidak terlalu "yakin"
USE_TTA = True                # Test-Time Augmentation saat evaluasi (rata-rata 8 rotasi/flip)
RUN_CV = os.environ.get('RUN_CV', '1') == '1'   # 5-fold cross-validation berbasis kelompok
CV_FOLDS = 5
EPOCHS_CV_FE = int(os.environ.get('EPOCHS_CV_FE', 10))
EPOCHS_CV_FT = int(os.environ.get('EPOCHS_CV_FT', 10))
RUN_EXPERIMENTS = os.environ.get('RUN_EXPERIMENTS', '1') == '1'

# Nama folder pada dataset -> nama kelas yang ditampilkan
CLASS_LABELS = {
    'Bacterialblight': 'Bacterial Blight',
    'Blast': 'Blast',
    'Brownspot': 'Brown Spot',
    'Tungro': 'Tungro',
}
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp'}

for d in (OUTPUT_DIR, MODEL_DIR):
    d.mkdir(parents=True, exist_ok=True)

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

print('TensorFlow :', tf.__version__)
print('GPU        :', tf.config.list_physical_devices('GPU') or 'Tidak ada (menggunakan CPU)')


def save_fig(name):
    path = OUTPUT_DIR / name
    plt.savefig(path, dpi=200, bbox_inches='tight')
    print('Disimpan:', path)


def save_table(df, name):
    path = OUTPUT_DIR / name
    df.to_csv(path, index=False)
    print('Disimpan:', path)

# %% [markdown]
# ## 2. Eksplorasi Dataset
# Dataset diunduh dari Mendeley Data / Kaggle (*Rice Leaf Disease Images*) lalu diekstrak ke
# `DATASET_DIR`, dengan struktur:
# ```
# dataset/Rice Leaf Disease Images/
# ├── Bacterialblight/
# ├── Blast/
# ├── Brownspot/
# └── Tungro/
# ```

# %%
# (Opsional) unduh langsung dari Kaggle; cukup dijalankan sekali.
# !pip install -q kaggle
# !kaggle datasets download -d nirmalsankalana/rice-leaf-disease-image -p dataset --unzip


def list_images(folder):
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in IMG_EXTS)


def find_dataset_dir(root):
    """Mencari folder yang berisi keempat subfolder kelas, apa pun nama folder induknya."""
    root = Path(root)
    if not root.exists():
        raise FileNotFoundError(f'Folder {root.resolve()} tidak ditemukan. Periksa lokasi dataset / jalankan sel unduh.')
    for d in [root, *sorted(p for p in root.rglob('*') if p.is_dir())]:
        if set(CLASS_LABELS) <= {c.name for c in d.iterdir() if c.is_dir()}:
            return d
    raise FileNotFoundError(f'Tidak ada folder berisi {list(CLASS_LABELS)} di dalam {root.resolve()}')


DATASET_DIR = find_dataset_dir(DATASET_DIR)
print('Folder dataset:', DATASET_DIR)
class_dirs = [DATASET_DIR / c for c in CLASS_LABELS]   # hanya 4 kelas penyakit

# Jumlah file pada dataset asli; selisih biasanya berarti ekstrak zip belum lengkap (sering terjadi di Google Drive)
EXPECTED_COUNTS = {'Bacterialblight': 1584, 'Blast': 1440, 'Brownspot': 1600, 'Tungro': 1308}
for d in class_dirs:
    n = len(list_images(d))
    if n != EXPECTED_COUNTS[d.name]:
        print(f'PERINGATAN: {d.name} berisi {n} citra, seharusnya {EXPECTED_COUNTS[d.name]}. '
              'Hapus folder dataset lalu unduh/ekstrak ulang.')
CLASS_NAMES = [d.name for d in class_dirs]
DISPLAY_NAMES = [CLASS_LABELS.get(c, c) for c in CLASS_NAMES]
NUM_CLASSES = len(CLASS_NAMES)

dataset_info = pd.DataFrame({
    'Kelas': DISPLAY_NAMES,
    'Folder': CLASS_NAMES,
    'Jumlah Citra': [len(list_images(d)) for d in class_dirs],
})
dataset_info['Persentase (%)'] = (dataset_info['Jumlah Citra'] / dataset_info['Jumlah Citra'].sum() * 100).round(2)
total_row = pd.DataFrame([{'Kelas': 'Total', 'Folder': '-', 'Jumlah Citra': dataset_info['Jumlah Citra'].sum(),
                           'Persentase (%)': 100.0}])
tabel_dataset = pd.concat([dataset_info, total_row], ignore_index=True)
save_table(tabel_dataset, 'tabel_4_1_distribusi_dataset.csv')
tabel_dataset

# %%
plt.figure(figsize=(8, 5))
ax = sns.barplot(data=dataset_info, x='Kelas', y='Jumlah Citra', hue='Kelas', palette='viridis', legend=False)
for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2, p.get_height()),
                ha='center', va='bottom', fontsize=11)
plt.title('Distribusi Jumlah Citra per Kelas Penyakit Daun Padi')
plt.ylabel('Jumlah Citra')
save_fig('gambar_4_1_distribusi_dataset.png')
plt.show()

# %%
# Contoh citra dari setiap kelas
fig, axes = plt.subplots(NUM_CLASSES, 4, figsize=(12, 3 * NUM_CLASSES))
for i, d in enumerate(class_dirs):
    samples = random.sample(list_images(d), 4)
    for j, img_path in enumerate(samples):
        img = keras.utils.load_img(img_path)
        axes[i, j].imshow(img)
        axes[i, j].axis('off')
        if j == 0:
            axes[i, j].set_title(DISPLAY_NAMES[i], loc='left', fontsize=12, fontweight='bold')
plt.tight_layout()
save_fig('gambar_4_2_contoh_citra_per_kelas.png')
plt.show()

# %%
# Variasi resolusi citra asli (alasan perlunya resize ke 224x224)
size_rows = []
for d, name in zip(class_dirs, DISPLAY_NAMES):
    for p in random.sample(list_images(d), min(50, len(list_images(d)))):
        w, h = keras.utils.load_img(p).size
        size_rows.append({'Kelas': name, 'Lebar': w, 'Tinggi': h})
sizes = pd.DataFrame(size_rows)
sizes.groupby('Kelas')[['Lebar', 'Tinggi']].agg(['min', 'max', 'mean']).round(0)

# %% [markdown]
# ## 3. Pembagian Dataset (80% Latih, 10% Validasi, 10% Uji) Berbasis Kelompok Citra Asli
# Dataset *Rice Leaf Disease Images* **sudah berisi hasil augmentasi**: satu citra asli disimpan
# berkali-kali dalam versi diputar/dibalik (contoh `BLAST1_001.jpg` s.d. `BLAST9_001.jpg` adalah daun yang
# sama). Jika dibagi acak per file, salinan citra yang sama akan muncul di data latih **dan** data uji
# sehingga akurasi uji menjadi semu (*data leakage*).
#
# Karena itu, citra dikelompokkan dulu berdasarkan kemiripan visual (*perceptual hash* dHash yang
# dibandingkan pada 8 variasi rotasi/flip). Semua anggota satu kelompok dimasukkan ke subset yang sama,
# lalu kelompok (citra asli) dibagi dengan rasio 80:10:10 per kelas (stratified).

# %%
SPLIT_MODE = os.environ.get('SPLIT_MODE', 'group')   # 'group' (disarankan) atau 'random' (pembanding)
HASH_THRESHOLD = 6                                   # maks. beda bit (dari 64) agar dianggap citra yang sama
_TRANSFORMS = [None, Image.FLIP_LEFT_RIGHT, Image.FLIP_TOP_BOTTOM, Image.ROTATE_90,
               Image.ROTATE_180, Image.ROTATE_270, Image.TRANSPOSE, Image.TRANSVERSE]


def dhash_variants(path, size=8):
    """dHash 64-bit untuk citra dan 7 variasi rotasi/flip-nya (8 x 64 boolean)."""
    gray = Image.open(path).convert('L')
    hashes = []
    for t in _TRANSFORMS:
        im = gray if t is None else gray.transpose(t)
        a = np.asarray(im.resize((size + 1, size), Image.BILINEAR), dtype=np.int16)
        hashes.append((a[:, 1:] > a[:, :-1]).flatten())
    return np.array(hashes)


def group_images(files, threshold=HASH_THRESHOLD):
    """Mengelompokkan file yang merupakan salinan (rotasi/flip) dari citra asli yang sama (union-find)."""
    variants = np.array([dhash_variants(f) for f in files])   # n x 8 x 64
    base = variants[:, 0]                                      # n x 64
    parent = list(range(len(files)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(files)):
        dist = (variants[i][:, None, :] != base[None, :, :]).sum(-1).min(0)
        for j in np.where(dist <= threshold)[0]:
            parent[find(i)] = find(int(j))
    return np.array([find(i) for i in range(len(files))]), base


def split_groups(groups, ratio, seed):
    """Membagi kelompok (citra asli) ke train/val/test dengan rasio 80:10:10 berdasarkan JUMLAH citra asli,
    sehingga data validasi & uji tiap kelas berisi cukup banyak daun yang berbeda."""
    rng = np.random.default_rng(seed)
    unique = rng.permutation(np.unique(groups))
    n_val = max(1, round(len(unique) * ratio[1]))
    n_test = max(1, round(len(unique) * ratio[2]))
    assign = {g: 'test' for g in unique[:n_test]}
    assign.update({g: 'val' for g in unique[n_test:n_test + n_val]})
    assign.update({g: 'train' for g in unique[n_test + n_val:]})
    return np.array([assign[g] for g in groups])


def split_dataset(class_dirs, dst_dir, ratio=SPLIT_RATIO, seed=SEED, mode=SPLIT_MODE):
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    info, hashes = [], {}
    for cls_dir in class_dirs:
        files = list_images(cls_dir)
        groups, base = group_images(files)
        hashes[cls_dir.name] = (files, base, groups)
        if mode == 'group':
            subsets = split_groups(groups, ratio, seed)
        else:
            subsets = np.empty(len(files), dtype=object)
            idx_train, idx_rest = train_test_split(np.arange(len(files)), train_size=ratio[0], random_state=seed)
            idx_val, idx_test = train_test_split(idx_rest, test_size=ratio[2] / (ratio[1] + ratio[2]),
                                                 random_state=seed)
            subsets[idx_train], subsets[idx_val], subsets[idx_test] = 'train', 'val', 'test'
        for f, subset in zip(files, subsets):
            out = dst_dir / subset / cls_dir.name
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, out / f.name)
        info.append({'Kelas': CLASS_LABELS.get(cls_dir.name, cls_dir.name), 'Jumlah File': len(files),
                     'Jumlah Citra Asli (kelompok)': len(np.unique(groups)),
                     'Citra Asli Latih/Val/Uji': '/'.join(str(len(np.unique(groups[subsets == s])))
                                                          for s in ('train', 'val', 'test')),
                     'Rata-rata Salinan per Citra Asli': round(len(files) / len(np.unique(groups)), 1)})
    return pd.DataFrame(info), hashes


tabel_kelompok, file_hashes = split_dataset(class_dirs, SPLIT_DIR)
print('Mode pembagian:', SPLIT_MODE)
save_table(tabel_kelompok, 'tabel_4_2a_citra_asli_vs_augmentasi.csv')
tabel_kelompok

# %%
split_rows = []
for cls, name in zip(CLASS_NAMES, DISPLAY_NAMES):
    row = {'Kelas': name}
    for subset, label in (('train', 'Data Latih'), ('val', 'Data Validasi'), ('test', 'Data Uji')):
        row[label] = len(list_images(SPLIT_DIR / subset / cls))
    row['Total'] = row['Data Latih'] + row['Data Validasi'] + row['Data Uji']
    split_rows.append(row)
tabel_split = pd.DataFrame(split_rows)
tabel_split.loc[len(tabel_split)] = ['Total'] + tabel_split.iloc[:, 1:].sum().tolist()
save_table(tabel_split, 'tabel_4_2_pembagian_dataset.csv')
tabel_split

# %%
# Pemeriksaan kebocoran data: apakah citra uji memiliki salinan (rotasi/flip) di data latih?
leak_rows = []
for cls, name in zip(CLASS_NAMES, DISPLAY_NAMES):
    files, base, _ = file_hashes[cls]
    index = {f.name: i for i, f in enumerate(files)}
    train_idx = [index[p.name] for p in list_images(SPLIT_DIR / 'train' / cls)]
    test_files = list_images(SPLIT_DIR / 'test' / cls)
    nearest = np.array([(dhash_variants(p)[:, None, :] != base[train_idx][None, :, :]).sum(-1).min()
                        for p in test_files])
    leak_rows.append({'Kelas': name, 'Data Uji': len(test_files),
                      'Punya Salinan di Data Latih': int((nearest <= HASH_THRESHOLD).sum()),
                      'Persentase (%)': round(float((nearest <= HASH_THRESHOLD).mean()) * 100, 2)})
tabel_leak = pd.DataFrame(leak_rows)
save_table(tabel_leak, f'tabel_4_2b_cek_kebocoran_{SPLIT_MODE}.csv')
tabel_leak

# %% [markdown]
# ## 4. Pre-processing dan Augmentasi Data
# - **Resize** seluruh citra menjadi 224×224 piksel (ukuran input MobileNetV2).
# - **Normalisasi** nilai piksel ke rentang [0, 1] (dibagi 255). Di dalam model, nilai ini
#   dipetakan lagi ke [-1, 1] sesuai format bobot pra-latih ImageNet MobileNetV2.
# - **Augmentasi** (hanya aktif saat pelatihan): flip horizontal/vertikal, rotasi, zoom, translasi,
#   perubahan kecerahan dan kontras untuk memperkaya variasi data latih dan mengurangi overfitting.

# %%
def load_subset(subset, shuffle):
    return keras.utils.image_dataset_from_directory(
        SPLIT_DIR / subset,
        labels='inferred',
        label_mode='categorical',
        class_names=CLASS_NAMES,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        shuffle=shuffle,
        seed=SEED,
    )


normalization = layers.Rescaling(1.0 / 255)
AUTOTUNE = tf.data.AUTOTUNE


def prepare(ds):
    return ds.map(lambda x, y: (normalization(x), y), num_parallel_calls=AUTOTUNE).prefetch(AUTOTUNE)


train_ds = prepare(load_subset('train', shuffle=True))
val_ds = prepare(load_subset('val', shuffle=False))
test_raw = load_subset('test', shuffle=False)
test_files = [Path(p) for p in test_raw.file_paths]   # urutan file = urutan prediksi
test_ds = prepare(test_raw)

x_batch, y_batch = next(iter(train_ds))
print('Bentuk batch citra :', x_batch.shape)
print('Rentang nilai piksel:', float(tf.reduce_min(x_batch)), '-', float(tf.reduce_max(x_batch)))

# %%
data_augmentation = keras.Sequential([
    layers.RandomFlip('horizontal_and_vertical'),
    layers.RandomRotation(0.25, fill_mode='reflect'),
    layers.RandomZoom((-0.3, 0.1), fill_mode='reflect'),
    layers.RandomTranslation(0.1, 0.1, fill_mode='reflect'),
    layers.RandomBrightness(0.2, value_range=(0.0, 1.0)),
    layers.RandomContrast(0.3),
], name='augmentasi')

# Visualisasi hasil augmentasi pada satu citra
sample = x_batch[:1]
plt.figure(figsize=(12, 3))
plt.subplot(1, 5, 1)
plt.imshow(sample[0])
plt.title('Asli')
plt.axis('off')
for i in range(4):
    plt.subplot(1, 5, i + 2)
    plt.imshow(tf.clip_by_value(data_augmentation(sample, training=True)[0], 0, 1))
    plt.title(f'Augmentasi {i + 1}')
    plt.axis('off')
save_fig('gambar_4_3_contoh_augmentasi.png')
plt.show()

# %% [markdown]
# ## 5. Pembangunan Model MobileNetV2 dengan Transfer Learning
# - **Tahap deteksi ciri visual**: lapisan konvolusi MobileNetV2 (bobot ImageNet) mengekstraksi
#   fitur warna bercak, tekstur, dan pola lesi.
# - **Tahap klasifikasi**: GlobalAveragePooling → Dense (ReLU) → Dropout → Dense softmax 4 kelas.

# %%
def build_model(dense_units=128, dropout=DROPOUT):
    base = keras.applications.MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights='imagenet')
    base.trainable = False  # tahap 1: feature extraction (bobot konvolusi dibekukan)

    inputs = keras.Input(shape=IMG_SIZE + (3,), name='citra_daun')
    x = data_augmentation(inputs)
    x = layers.Rescaling(2.0, offset=-1.0, name='skala_mobilenetv2')(x)   # [0,1] -> [-1,1]
    x = base(x, training=False)                                             # DETEKSI ciri visual
    x = layers.GlobalAveragePooling2D(name='global_avg_pool')(x)
    x = layers.Dense(dense_units, activation='relu', name='fully_connected')(x)
    x = layers.Dropout(dropout, name='dropout')(x)
    outputs = layers.Dense(NUM_CLASSES, activation='softmax', name='klasifikasi')(x)  # KLASIFIKASI
    return keras.Model(inputs, outputs, name='MobileNetV2_PenyakitPadi'), base


def make_loss():
    return keras.losses.CategoricalCrossentropy(label_smoothing=LABEL_SMOOTHING)


def make_optimizer(name, lr):
    return {'adam': keras.optimizers.Adam, 'rmsprop': keras.optimizers.RMSprop,
            'sgd': lambda learning_rate: keras.optimizers.SGD(learning_rate=learning_rate, momentum=0.9)
            }[name](learning_rate=lr)


model, base_model = build_model()
model.summary()

# %%
def count_params(weights):
    return int(sum(np.prod(w.shape) for w in weights))


tabel_param = pd.DataFrame([
    {'Bagian': 'MobileNetV2 (base model)', 'Jumlah Parameter': base_model.count_params()},
    {'Bagian': 'Trainable (tahap feature extraction)', 'Jumlah Parameter': count_params(model.trainable_weights)},
    {'Bagian': 'Non-trainable', 'Jumlah Parameter': count_params(model.non_trainable_weights)},
    {'Bagian': 'Total parameter model', 'Jumlah Parameter': model.count_params()},
])
save_table(tabel_param, 'tabel_4_3_parameter_model.csv')
tabel_param

# %% [markdown]
# ## 6. Eksperimen Konfigurasi Hyperparameter
# Sesuai metode eksperimental pada BAB III, beberapa konfigurasi optimizer dan learning rate
# dibandingkan pada tahap feature extraction. Konfigurasi dengan akurasi validasi tertinggi
# dipakai untuk pelatihan akhir. Set `RUN_EXPERIMENTS = False` untuk melewati tahap ini.

# %%
EXPERIMENTS = [
    {'optimizer': 'adam', 'learning_rate': 1e-3, 'dense_units': 128},
    {'optimizer': 'adam', 'learning_rate': 1e-4, 'dense_units': 128},
    {'optimizer': 'rmsprop', 'learning_rate': 1e-3, 'dense_units': 128},
    {'optimizer': 'rmsprop', 'learning_rate': 1e-4, 'dense_units': 128},
    {'optimizer': 'adam', 'learning_rate': 1e-3, 'dense_units': 64},
    {'optimizer': 'sgd', 'learning_rate': 1e-2, 'dense_units': 128},
]
BEST_CONFIG = {'optimizer': 'adam', 'learning_rate': 1e-3, 'dense_units': 128}

if RUN_EXPERIMENTS:
    exp_rows = []
    for i, cfg in enumerate(EXPERIMENTS, 1):
        tf.random.set_seed(SEED)
        m, _ = build_model(dense_units=cfg['dense_units'])
        m.compile(optimizer=make_optimizer(cfg['optimizer'], cfg['learning_rate']),
                  loss=make_loss(), metrics=['accuracy'])
        start = time.time()
        h = m.fit(train_ds, validation_data=val_ds, epochs=EPOCHS_EXPERIMENT, verbose=0)
        exp_rows.append({
            'No': i,
            'Optimizer': cfg['optimizer'].upper() if cfg['optimizer'] != 'rmsprop' else 'RMSprop',
            'Learning Rate': cfg['learning_rate'],
            'Dense Units': cfg['dense_units'],
            'Epoch': EPOCHS_EXPERIMENT,
            'Train Accuracy': round(h.history['accuracy'][-1], 4),
            'Val Accuracy': round(max(h.history['val_accuracy']), 4),
            'Val Loss': round(min(h.history['val_loss']), 4),
            'Waktu (detik)': round(time.time() - start, 1),
            '_cfg': cfg,
        })
        print(f"[{i}/{len(EXPERIMENTS)}] {cfg} -> val_acc={exp_rows[-1]['Val Accuracy']}")
        keras.backend.clear_session()

    tabel_exp = pd.DataFrame(exp_rows)
    BEST_CONFIG = tabel_exp.sort_values(['Val Accuracy', 'Val Loss'], ascending=[False, True]).iloc[0]['_cfg']
    tabel_exp = tabel_exp.drop(columns='_cfg')
    save_table(tabel_exp, 'tabel_4_4_eksperimen_hyperparameter.csv')
    print('Konfigurasi terbaik:', BEST_CONFIG)
    display(tabel_exp) if 'display' in globals() else print(tabel_exp)

    plt.figure(figsize=(9, 4))
    labels = [f"{r['Optimizer']}\nlr={r['Learning Rate']}\n{r['Dense Units']} unit" for _, r in tabel_exp.iterrows()]
    sns.barplot(x=labels, y=tabel_exp['Val Accuracy'], hue=labels, palette='crest', legend=False)
    plt.ylim(max(0, tabel_exp['Val Accuracy'].min() - 0.1), 1.0)
    plt.ylabel('Akurasi Validasi')
    plt.title('Perbandingan Konfigurasi Hyperparameter')
    save_fig('gambar_4_4_perbandingan_hyperparameter.png')
    plt.show()

# %% [markdown]
# ## 7. Pelatihan Tahap 1 — Feature Extraction
# Seluruh lapisan MobileNetV2 dibekukan; hanya lapisan klasifikasi yang dilatih.

# %%
tf.random.set_seed(SEED)
keras.backend.clear_session()
model, base_model = build_model(dense_units=BEST_CONFIG['dense_units'])
model.compile(optimizer=make_optimizer(BEST_CONFIG['optimizer'], BEST_CONFIG['learning_rate']),
              loss=make_loss(), metrics=['accuracy'])

best_path = MODEL_DIR / 'best_model.keras'
callbacks = [
    keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
    keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-7, verbose=1),
    keras.callbacks.ModelCheckpoint(best_path, monitor='val_loss', save_best_only=True),
]

start = time.time()
history_fe = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS_FEATURE_EXTRACTION, callbacks=callbacks)
time_fe = time.time() - start
print(f'Waktu pelatihan tahap 1: {time_fe / 60:.2f} menit')

# %% [markdown]
# ## 8. Pelatihan Tahap 2 — Fine-Tuning
# Lapisan MobileNetV2 mulai layer ke-`FINE_TUNE_AT` dibuka (*unfreeze*) dan dilatih ulang dengan
# learning rate kecil agar model beradaptasi dengan karakteristik citra daun padi.

# %%
base_model.trainable = True
for layer in base_model.layers[:FINE_TUNE_AT]:
    layer.trainable = False
for layer in base_model.layers:                    # BatchNorm tetap beku agar stabil
    if isinstance(layer, layers.BatchNormalization):
        layer.trainable = False

model.compile(optimizer=make_optimizer(BEST_CONFIG['optimizer'], FINE_TUNE_LR),
              loss=make_loss(), metrics=['accuracy'])
print('Jumlah layer base model      :', len(base_model.layers))
print('Parameter trainable fine-tune:', count_params(model.trainable_weights))

initial_epoch = len(history_fe.history['loss'])
start = time.time()
history_ft = model.fit(train_ds, validation_data=val_ds,
                       epochs=initial_epoch + EPOCHS_FINE_TUNING, initial_epoch=initial_epoch,
                       callbacks=callbacks)
time_ft = time.time() - start
print(f'Waktu pelatihan tahap 2: {time_ft / 60:.2f} menit')
print(f'Total waktu pelatihan  : {(time_fe + time_ft) / 60:.2f} menit')

# %%
# Tabel konfigurasi pelatihan akhir
tabel_config = pd.DataFrame([
    ['Arsitektur', 'MobileNetV2 (pre-trained ImageNet)'],
    ['Ukuran input', f'{IMG_SIZE[0]} x {IMG_SIZE[1]} x 3'],
    ['Batch size', BATCH_SIZE],
    ['Optimizer', BEST_CONFIG['optimizer']],
    ['Learning rate tahap 1', BEST_CONFIG['learning_rate']],
    ['Learning rate tahap 2 (fine-tuning)', FINE_TUNE_LR],
    ['Fine-tune mulai layer ke-', FINE_TUNE_AT],
    ['Dense units', BEST_CONFIG['dense_units']],
    ['Dropout', DROPOUT],
    ['Loss function', f'Categorical Cross-Entropy (label smoothing {LABEL_SMOOTHING})'],
    ['Test-Time Augmentation', '8 variasi rotasi/flip' if USE_TTA else 'Tidak'],
    ['Epoch tahap 1 (dijalankan)', initial_epoch],
    ['Epoch tahap 2 (dijalankan)', len(history_ft.history.get('loss', []))],
    ['Callback', 'EarlyStopping, ReduceLROnPlateau, ModelCheckpoint'],
    ['Waktu pelatihan total (menit)', round((time_fe + time_ft) / 60, 2)],
], columns=['Parameter', 'Nilai'])
save_table(tabel_config, 'tabel_4_5_konfigurasi_pelatihan.csv')
tabel_config

# %% [markdown]
# ## 9. Grafik Akurasi dan Loss Pelatihan

# %%
hist = {k: history_fe.history[k] + history_ft.history.get(k, []) for k in ('accuracy', 'val_accuracy', 'loss', 'val_loss')}
epochs_range = range(1, len(hist['accuracy']) + 1)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, metric, title in ((axes[0], 'accuracy', 'Akurasi'), (axes[1], 'loss', 'Loss')):
    ax.plot(epochs_range, hist[metric], marker='o', markersize=3, label=f'{title} Latih')
    ax.plot(epochs_range, hist[f'val_{metric}'], marker='o', markersize=3, label=f'{title} Validasi')
    ax.axvline(initial_epoch + 0.5, color='gray', linestyle='--', label='Mulai Fine-Tuning')
    ax.set_title(f'Grafik {title} Pelatihan dan Validasi')
    ax.set_xlabel('Epoch')
    ax.set_ylabel(title)
    ax.grid(alpha=0.3)
    ax.legend()
save_fig('gambar_4_5_grafik_akurasi_loss.png')
plt.show()

tabel_history = pd.DataFrame({'Epoch': list(epochs_range),
                              'Tahap': ['Feature Extraction'] * initial_epoch
                                       + ['Fine-Tuning'] * (len(hist['accuracy']) - initial_epoch),
                              **{k: np.round(v, 4) for k, v in hist.items()}})
save_table(tabel_history, 'tabel_4_6_riwayat_pelatihan.csv')
tabel_history

# %% [markdown]
# ## 10. Evaluasi Model pada Data Uji
# Model terbaik (berdasarkan akurasi validasi) dievaluasi pada data uji yang belum pernah dilihat.

# %%
model = keras.models.load_model(best_path)
test_loss, test_acc = model.evaluate(test_ds, verbose=0)
print(f'Test loss     : {test_loss:.4f}')
print(f'Test accuracy : {test_acc * 100:.2f}%')



def dihedral(x, k):
    """Variasi ke-k (0-7) dari batch citra: rotasi 0/90/180/270 derajat, dengan/tanpa flip."""
    x = tf.image.rot90(x, k % 4)
    return tf.image.flip_left_right(x) if k >= 4 else x


def predict_tta(m, ds):
    """Test-Time Augmentation: rata-rata probabilitas dari 8 variasi rotasi/flip tiap citra."""
    return np.mean([m.predict(ds.map(lambda x, y: (dihedral(x, k), y)), verbose=0) for k in range(8)], axis=0)


def macro_metrics(y_t, y_p):
    p, r, f1, _ = precision_recall_fscore_support(y_t, y_p, average='macro', zero_division=0)
    return {'Akurasi': round(accuracy_score(y_t, y_p), 4), 'Presisi': round(p, 4),
            'Recall': round(r, 4), 'F1-Score': round(f1, 4)}


y_true = np.concatenate([np.argmax(y, axis=1) for _, y in test_ds])
y_prob_plain = model.predict(test_ds, verbose=0)
y_prob_tta = predict_tta(model, test_ds)

tabel_tta = pd.DataFrame([{'Metode Prediksi': name, **macro_metrics(y_true, prob.argmax(1))}
                          for name, prob in (('Tanpa TTA', y_prob_plain), ('Dengan TTA (8 rotasi/flip)', y_prob_tta))])
save_table(tabel_tta, 'tabel_4_7a_pengaruh_tta.csv')
display(tabel_tta) if 'display' in globals() else print(tabel_tta)

y_prob = y_prob_tta if USE_TTA else y_prob_plain     # hasil akhir yang dilaporkan
y_pred = np.argmax(y_prob, axis=1)
print(f"Akurasi akhir data uji: {accuracy_score(y_true, y_pred) * 100:.2f}% ({'dengan' if USE_TTA else 'tanpa'} TTA)")

# %%
# Classification report: presisi, recall, F1-score per kelas
report = classification_report(y_true, y_pred, target_names=DISPLAY_NAMES, digits=4,
                               output_dict=True, zero_division=0)
print(classification_report(y_true, y_pred, target_names=DISPLAY_NAMES, digits=4, zero_division=0))

tabel_report = pd.DataFrame(report).T.reset_index().rename(columns={
    'index': 'Kelas', 'precision': 'Presisi', 'recall': 'Recall', 'f1-score': 'F1-Score', 'support': 'Jumlah Data Uji'})
tabel_report.loc[tabel_report['Kelas'] == 'accuracy', ['Presisi', 'Recall']] = np.nan
tabel_report.loc[tabel_report['Kelas'] == 'accuracy', 'Jumlah Data Uji'] = len(y_true)
tabel_report['Kelas'] = tabel_report['Kelas'].replace({'accuracy': 'Akurasi', 'macro avg': 'Macro Average',
                                                       'weighted avg': 'Weighted Average'})
tabel_report[['Presisi', 'Recall', 'F1-Score']] = tabel_report[['Presisi', 'Recall', 'F1-Score']].round(4)
tabel_report['Jumlah Data Uji'] = tabel_report['Jumlah Data Uji'].astype(int)
save_table(tabel_report, 'tabel_4_7_classification_report.csv')
tabel_report

# %%
# Confusion matrix (jumlah dan ternormalisasi)
cm = confusion_matrix(y_true, y_pred)
cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True)

fig, axes = plt.subplots(1, 2, figsize=(15, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=DISPLAY_NAMES, yticklabels=DISPLAY_NAMES, ax=axes[0])
axes[0].set_title('Confusion Matrix (Jumlah Citra)')
sns.heatmap(cm_norm, annot=True, fmt='.2%', cmap='Greens', xticklabels=DISPLAY_NAMES, yticklabels=DISPLAY_NAMES, ax=axes[1])
axes[1].set_title('Confusion Matrix (Ternormalisasi)')
for ax in axes:
    ax.set_xlabel('Label Prediksi')
    ax.set_ylabel('Label Aktual')
plt.tight_layout()
save_fig('gambar_4_6_confusion_matrix.png')
plt.show()

pd.DataFrame(cm, index=[f'Aktual: {n}' for n in DISPLAY_NAMES],
             columns=[f'Prediksi: {n}' for n in DISPLAY_NAMES]).to_csv(OUTPUT_DIR / 'tabel_4_8_confusion_matrix.csv')

# %%
# Nilai TP, FP, FN, TN per kelas dan perhitungan manual metrik (untuk pembahasan rumus BAB II)
rows = []
total = cm.sum()
for i, name in enumerate(DISPLAY_NAMES):
    tp = cm[i, i]
    fp = cm[:, i].sum() - tp
    fn = cm[i, :].sum() - tp
    tn = total - tp - fp - fn
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    rows.append({'Kelas': name, 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn,
                 'Accuracy': round((tp + tn) / total, 4), 'Precision': round(precision, 4),
                 'Recall': round(recall, 4), 'F1-Score': round(f1, 4)})
tabel_tpfp = pd.DataFrame(rows)
save_table(tabel_tpfp, 'tabel_4_9_tp_fp_fn_tn.csv')
tabel_tpfp

# %%
# Grafik metrik per kelas
per_class = tabel_report[tabel_report['Kelas'].isin(DISPLAY_NAMES)].melt(
    id_vars='Kelas', value_vars=['Presisi', 'Recall', 'F1-Score'], var_name='Metrik', value_name='Nilai')
plt.figure(figsize=(10, 5))
ax = sns.barplot(data=per_class, x='Kelas', y='Nilai', hue='Metrik', palette='Set2')
for c in ax.containers:
    ax.bar_label(c, fmt='%.3f', fontsize=8)
plt.ylim(max(0, per_class['Nilai'].min() - 0.1), 1.02)
plt.title('Presisi, Recall, dan F1-Score per Kelas pada Data Uji')
plt.legend(loc='lower right')
save_fig('gambar_4_7_metrik_per_kelas.png')
plt.show()

# %%
# Contoh hasil prediksi pada data uji (hijau = benar, merah = salah)
idx = np.random.choice(len(test_files), min(12, len(test_files)), replace=False)
plt.figure(figsize=(14, 11))
for k, i in enumerate(idx):
    img = keras.utils.load_img(test_files[i], target_size=IMG_SIZE)
    actual = DISPLAY_NAMES[y_true[i]]
    pred = DISPLAY_NAMES[y_pred[i]]
    plt.subplot(3, 4, k + 1)
    plt.imshow(img)
    plt.axis('off')
    plt.title(f'Aktual: {actual}\nPrediksi: {pred} ({y_prob[i].max() * 100:.1f}%)',
              color='green' if actual == pred else 'red', fontsize=10)
plt.tight_layout()
save_fig('gambar_4_8_contoh_prediksi.png')
plt.show()

# %%
# Daftar citra yang salah diklasifikasi (bahan pembahasan)
wrong = np.where(y_true != y_pred)[0]
tabel_salah = pd.DataFrame({
    'File': [test_files[i].name for i in wrong],
    'Aktual': [DISPLAY_NAMES[y_true[i]] for i in wrong],
    'Prediksi': [DISPLAY_NAMES[y_pred[i]] for i in wrong],
    'Confidence (%)': [round(float(y_prob[i].max()) * 100, 2) for i in wrong],
})
save_table(tabel_salah, 'tabel_4_10_kesalahan_klasifikasi.csv')
print(f'Jumlah citra salah klasifikasi: {len(wrong)} dari {len(y_true)}')
tabel_salah

# %% [markdown]
# ## 10b. Validasi Silang 5-Fold Berbasis Kelompok (Group K-Fold)
# Data uji hanya berisi sedikit citra asli, sehingga satu daun yang salah dapat menggeser akurasi
# beberapa persen. Untuk estimasi yang lebih andal, data latih + validasi dibagi menjadi 5 *fold*
# berdasarkan kelompok citra asli (StratifiedGroupKFold). Model dilatih 5 kali; setiap kali satu fold
# menjadi data validasi. Hasil dilaporkan sebagai **rata-rata ± simpangan baku**. Prediksi kelima model
# juga digabung (*ensemble*) dan diuji pada data uji. Set `RUN_CV = False` untuk melewati tahap ini.

# %%
def make_ds(paths, labels, shuffle):
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(len(paths), seed=SEED)

    def load(path, label):
        img = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        return tf.image.resize(img, IMG_SIZE) / 255.0, tf.one_hot(label, NUM_CLASSES)

    return ds.map(load, num_parallel_calls=AUTOTUNE).batch(BATCH_SIZE).prefetch(AUTOTUNE)


def train_two_stage(train_data, val_data, ckpt, epochs_fe, epochs_ft, verbose=0):
    keras.backend.clear_session()
    tf.random.set_seed(SEED)
    m, base = build_model(dense_units=BEST_CONFIG['dense_units'])
    cbs = [keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
           keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, min_lr=1e-7),
           keras.callbacks.ModelCheckpoint(ckpt, monitor='val_loss', save_best_only=True)]
    m.compile(optimizer=make_optimizer(BEST_CONFIG['optimizer'], BEST_CONFIG['learning_rate']),
              loss=make_loss(), metrics=['accuracy'])
    h1 = m.fit(train_data, validation_data=val_data, epochs=epochs_fe, callbacks=cbs, verbose=verbose)
    base.trainable = True
    for layer in base.layers[:FINE_TUNE_AT]:
        layer.trainable = False
    for layer in base.layers:
        if isinstance(layer, layers.BatchNormalization):
            layer.trainable = False
    m.compile(optimizer=make_optimizer(BEST_CONFIG['optimizer'], FINE_TUNE_LR), loss=make_loss(), metrics=['accuracy'])
    start_ep = len(h1.history['loss'])
    m.fit(train_data, validation_data=val_data, epochs=start_ep + epochs_ft, initial_epoch=start_ep,
          callbacks=cbs, verbose=verbose)
    return keras.models.load_model(ckpt)


if RUN_CV:
    # kumpulkan file latih + validasi beserta label kelas dan id kelompok citra asli
    cv_paths, cv_labels, cv_groups = [], [], []
    for ci, cls in enumerate(CLASS_NAMES):
        files, _, groups = file_hashes[cls]
        group_of = {f.name: f'{cls}_{g}' for f, g in zip(files, groups)}
        for subset in ('train', 'val'):
            for p in list_images(SPLIT_DIR / subset / cls):
                cv_paths.append(str(p))
                cv_labels.append(ci)
                cv_groups.append(group_of[p.name])
    cv_paths, cv_labels, cv_groups = np.array(cv_paths), np.array(cv_labels), np.array(cv_groups)

    cv_rows, ensemble_prob = [], np.zeros_like(y_prob_tta)
    sgkf = StratifiedGroupKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    for fold, (tr, va) in enumerate(sgkf.split(cv_paths, cv_labels, cv_groups), 1):
        start = time.time()
        va_ds = make_ds(cv_paths[va], cv_labels[va], False)
        fold_model = train_two_stage(make_ds(cv_paths[tr], cv_labels[tr], True), va_ds,
                                     MODEL_DIR / f'cv_fold{fold}.keras', EPOCHS_CV_FE, EPOCHS_CV_FT)
        ensemble_prob += predict_tta(fold_model, test_ds) / CV_FOLDS
        cv_rows.append({'Fold': fold, 'Citra Validasi': len(va), 'Citra Asli Validasi': len(np.unique(cv_groups[va])),
                        **macro_metrics(cv_labels[va], predict_tta(fold_model, va_ds).argmax(1)),
                        'Waktu (menit)': round((time.time() - start) / 60, 2)})
        print(cv_rows[-1])

    tabel_cv = pd.DataFrame(cv_rows)
    metric_cols = ['Akurasi', 'Presisi', 'Recall', 'F1-Score']
    summary = [{'Fold': 'Rata-rata', **tabel_cv[metric_cols].mean().round(4).to_dict()},
               {'Fold': 'Simpangan baku', **tabel_cv[metric_cols].std().round(4).to_dict()}]
    tabel_cv = pd.concat([tabel_cv, pd.DataFrame(summary)], ignore_index=True)
    save_table(tabel_cv, 'tabel_4_12_cross_validation.csv')
    display(tabel_cv) if 'display' in globals() else print(tabel_cv)

    tabel_ens = pd.DataFrame([{'Model': 'Model tunggal (+TTA)', **macro_metrics(y_true, y_pred)},
                              {'Model': f'Ensemble {CV_FOLDS} model CV (+TTA)',
                               **macro_metrics(y_true, ensemble_prob.argmax(1))}])
    save_table(tabel_ens, 'tabel_4_13_ensemble_cv.csv')
    display(tabel_ens) if 'display' in globals() else print(tabel_ens)

# %% [markdown]
# ## 11. Efisiensi Model (Ukuran dan Waktu Inferensi)

# %%
final_path = MODEL_DIR / 'mobilenetv2_padi.keras'
model.save(final_path)
size_mb = final_path.stat().st_size / (1024 * 1024)

single = x_batch[:1]
model.predict(single, verbose=0)  # warm-up
n_runs = 50
start = time.time()
for _ in range(n_runs):
    model.predict(single, verbose=0)
infer_ms = (time.time() - start) / n_runs * 1000

tabel_efisiensi = pd.DataFrame([
    ['Total parameter', f'{model.count_params():,}'],
    ['Ukuran file model (MB)', round(size_mb, 2)],
    ['Rata-rata waktu inferensi per citra (ms)', round(infer_ms, 2)],
    ['Perangkat', 'GPU' if tf.config.list_physical_devices('GPU') else 'CPU'],
], columns=['Aspek', 'Nilai'])
save_table(tabel_efisiensi, 'tabel_4_11_efisiensi_model.csv')
tabel_efisiensi

# %% [markdown]
# ## 12. Simpan Model dan Metadata untuk Aplikasi Web
# Salin isi folder `saved_model/` (`mobilenetv2_padi.keras`, `class_names.json`, `model_info.json`)
# ke folder `backend/models/` agar dapat digunakan oleh API Flask.

# %%
precision_m, recall_m, f1_m, _ = precision_recall_fscore_support(y_true, y_pred, average='macro',
                                                                zero_division=0)
with open(MODEL_DIR / 'class_names.json', 'w') as f:
    json.dump(CLASS_NAMES, f, indent=2)
model_info = {
    'nama': 'MobileNetV2 Penyakit Daun Padi',
    'arsitektur': 'MobileNetV2 + Transfer Learning (ImageNet)',
    'versi': '1.0',
    'file': final_path.name,
    'input_size': list(IMG_SIZE),
    'class_names': CLASS_NAMES,
    'display_names': DISPLAY_NAMES,
    'akurasi': round(float(accuracy_score(y_true, y_pred)), 4),
    'presisi': round(float(precision_m), 4),
    'recall': round(float(recall_m), 4),
    'f1_score': round(float(f1_m), 4),
    'tanggal_pelatihan': time.strftime('%Y-%m-%d'),
    'konfigurasi': {k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in BEST_CONFIG.items()},
}
with open(MODEL_DIR / 'model_info.json', 'w') as f:
    json.dump(model_info, f, indent=2)
print(json.dumps(model_info, indent=2))

# %%
# Ringkasan akhir untuk BAB IV
print('=' * 60)
print('RINGKASAN HASIL')
print('=' * 60)
print(f"Akurasi  : {model_info['akurasi'] * 100:.2f}%")
print(f"Presisi  : {model_info['presisi'] * 100:.2f}% (macro)")
print(f"Recall   : {model_info['recall'] * 100:.2f}% (macro)")
print(f"F1-Score : {model_info['f1_score'] * 100:.2f}% (macro)")
print('Target akurasi > 90% :', 'TERCAPAI' if model_info['akurasi'] > 0.9 else 'BELUM TERCAPAI (lakukan tuning ulang)')
