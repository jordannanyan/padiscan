import json
import time
import uuid

from flask import Blueprint, g, jsonify, request
from PIL import Image, UnidentifiedImageError

import model_service
from auth import login_required
from config import Config
from db import execute, query

bp = Blueprint('detect', __name__, url_prefix='/api')

DETAIL_SQL = '''
    SELECT h.id_hasil, h.confidence_score, h.probabilitas, h.tanggal_deteksi,
           c.id_citra, c.nama_file, c.path_file, c.ukuran_kb, c.tanggal_upload, c.id_pengguna,
           p.id_penyakit, p.kode_kelas, p.nama AS nama_penyakit, p.nama_latin, p.deskripsi, p.gejala, p.penanganan,
           m.nama AS nama_model, m.versi AS versi_model
    FROM hasil_deteksi h
    JOIN citra_daun c ON c.id_citra = h.id_citra
    JOIN penyakit p ON p.id_penyakit = h.id_penyakit
    LEFT JOIN model_cnn m ON m.id_model = h.id_model
'''


def serialize_hasil(row):
    row = dict(row)
    row['confidence_score'] = float(row['confidence_score'])
    row['ukuran_kb'] = float(row['ukuran_kb'])
    row['probabilitas'] = json.loads(row['probabilitas']) if row.get('probabilitas') else {}
    row['url_citra'] = f"/uploads/{row['path_file']}"
    for key in ('tanggal_deteksi', 'tanggal_upload'):
        if row.get(key):
            row[key] = row[key].strftime('%Y-%m-%d %H:%M:%S')
    return row


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@bp.post('/detect')
@login_required
def detect():
    file = request.files.get('citra')
    if not file or not file.filename:
        return jsonify(message='Citra daun padi wajib diunggah'), 400
    if not _allowed(file.filename):
        return jsonify(message='Format file harus JPG atau PNG'), 400

    data = file.read()
    size_kb = len(data) / 1024
    if size_kb > Config.MAX_UPLOAD_MB * 1024:
        return jsonify(message=f'Ukuran file maksimal {Config.MAX_UPLOAD_MB} MB'), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    stored_name = f'{uuid.uuid4().hex}.{ext}'
    Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = Config.UPLOAD_DIR / stored_name
    stored_path.write_bytes(data)

    try:
        Image.open(stored_path).verify()
    except (UnidentifiedImageError, OSError):
        stored_path.unlink(missing_ok=True)
        return jsonify(message='File bukan citra yang valid'), 400

    active_model = query('SELECT * FROM model_cnn WHERE aktif = 1 ORDER BY id_model DESC LIMIT 1', one=True)
    if not active_model:
        stored_path.unlink(missing_ok=True)
        return jsonify(message='Belum ada model CNN yang aktif, hubungi administrator'), 503

    # Tahap deteksi ciri visual (lapisan konvolusi) + klasifikasi (fully connected + softmax)
    start = time.time()
    try:
        kode_kelas, confidence, probabilities = model_service.predict(stored_path, active_model['path_file'])
    except FileNotFoundError as e:
        stored_path.unlink(missing_ok=True)
        return jsonify(message=str(e)), 503
    waktu_ms = round((time.time() - start) * 1000, 1)

    penyakit = query('SELECT id_penyakit FROM penyakit WHERE kode_kelas = %s', (kode_kelas,), one=True)
    if not penyakit:
        return jsonify(message=f'Kelas "{kode_kelas}" belum terdaftar pada tabel penyakit'), 500

    id_citra = execute(
        'INSERT INTO citra_daun (id_pengguna, nama_file, path_file, ukuran_kb) VALUES (%s, %s, %s, %s)',
        (g.user['id_pengguna'], file.filename, stored_name, round(size_kb, 2)))
    id_hasil = execute(
        'INSERT INTO hasil_deteksi (id_citra, id_penyakit, id_model, confidence_score, probabilitas) '
        'VALUES (%s, %s, %s, %s, %s)',
        (id_citra, penyakit['id_penyakit'], active_model['id_model'], confidence, json.dumps(probabilities)))
    execute('INSERT INTO riwayat_deteksi (id_pengguna, id_hasil) VALUES (%s, %s)', (g.user['id_pengguna'], id_hasil))

    hasil = serialize_hasil(query(DETAIL_SQL + ' WHERE h.id_hasil = %s', (id_hasil,), one=True))
    hasil['waktu_proses_ms'] = waktu_ms
    hasil['nama_kelas'] = {p['kode_kelas']: p['nama'] for p in query('SELECT kode_kelas, nama FROM penyakit')}
    return jsonify(hasil), 201
