"""Memuat model MobileNetV2 dan menjalankan proses deteksi & klasifikasi citra daun padi."""
import json
import re
import tempfile
import threading
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

from config import Config

_lock = threading.Lock()
_cache = {'path': None, 'model': None, 'class_names': None}


def _resolve(model_path):
    model_path = Path(model_path)
    return model_path if model_path.is_absolute() else Config.MODEL_DIR / model_path


def _strip_kwarg(node, class_name, key):
    """Menghapus argumen `key` dari konfigurasi layer `class_name` (rekursif di seluruh config model)."""
    if isinstance(node, dict):
        if node.get('class_name') == class_name and isinstance(node.get('config'), dict):
            node['config'].pop(key, None)
        for v in node.values():
            _strip_kwarg(v, class_name, key)
    elif isinstance(node, list):
        for v in node:
            _strip_kwarg(v, class_name, key)


def _load_keras_compat(model_path, max_fix=20):
    """Memuat model .keras. Jika model disimpan dengan Keras yang lebih baru (mis. di Google Colab), argumen
    layer yang belum dikenal Keras lokal (contoh: `quantization_config`, `value_range`) dihapus dari config.
    Argumen tersebut tidak memengaruhi prediksi; bobot model tetap sama persis."""
    import tensorflow as tf

    try:
        return tf.keras.models.load_model(model_path)
    except (TypeError, ValueError) as first_error:
        error = first_error

    with zipfile.ZipFile(model_path) as zf:
        members = {name: zf.read(name) for name in zf.namelist()}
    config = json.loads(members['config.json'])

    for _ in range(max_fix):
        match = re.search(r"Unrecognized keyword arguments passed to (\w+): \{'(\w+)'", str(error))
        if not match:
            raise error
        _strip_kwarg(config, match.group(1), match.group(2))
        members['config.json'] = json.dumps(config).encode()
        with tempfile.TemporaryDirectory() as tmp:
            fixed = Path(tmp) / model_path.name
            with zipfile.ZipFile(fixed, 'w') as zf:
                for name, data in members.items():
                    zf.writestr(name, data)
            try:
                return tf.keras.models.load_model(fixed)
            except (TypeError, ValueError) as e:
                error = e
    raise error


def _load(model_path):
    if not model_path.exists():
        raise FileNotFoundError(f'File model tidak ditemukan: {model_path}')

    class_file = model_path.parent / 'class_names.json'
    class_names = json.loads(class_file.read_text()) if class_file.exists() else \
        ['Bacterialblight', 'Blast', 'Brownspot', 'Tungro']

    _cache.update(path=str(model_path), model=_load_keras_compat(model_path), class_names=class_names)


def preprocess(image_path):
    """Pre-processing: konversi RGB, resize 224x224, normalisasi piksel ke [0, 1].
    Resize memakai tf.image.resize (bilinear) agar identik dengan pre-processing saat training."""
    import tensorflow as tf

    img = np.asarray(Image.open(image_path).convert('RGB'), dtype=np.float32)
    arr = tf.image.resize(img, Config.IMG_SIZE).numpy() / 255.0
    return np.expand_dims(arr, axis=0)


def predict(image_path, model_path):
    """Mengembalikan (kode_kelas, confidence %, {kode_kelas: probabilitas %})."""
    model_path = _resolve(model_path)
    with _lock:
        if _cache['path'] != str(model_path):
            _load(model_path)
        model, class_names = _cache['model'], _cache['class_names']

    # Test-Time Augmentation (sama seperti evaluasi di notebook): rata-rata prediksi 8 variasi rotasi/flip
    img = preprocess(image_path)[0]
    variants = [np.rot90(img, k) for k in range(4)]
    variants += [np.fliplr(v) for v in variants]
    probs = model.predict(np.stack(variants), verbose=0).mean(axis=0)
    idx = int(np.argmax(probs))
    probabilities = {name: round(float(p) * 100, 2) for name, p in zip(class_names, probs)}
    return class_names[idx], round(float(probs[idx]) * 100, 2), probabilities
