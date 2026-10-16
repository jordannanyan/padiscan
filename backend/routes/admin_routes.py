from pathlib import Path

from flask import Blueprint, g, jsonify, request
from werkzeug.security import generate_password_hash

from auth import admin_required
from config import Config
from db import execute, query
from routes.auth_routes import EMAIL_RE
from routes.detect_routes import DETAIL_SQL, serialize_hasil

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _fmt_dates(rows, *keys):
    for r in rows:
        for k in keys:
            if r.get(k):
                r[k] = r[k].strftime('%Y-%m-%d %H:%M:%S') if hasattr(r[k], 'hour') else r[k].isoformat()
    return rows


# ---------------------------------------------------------------- dashboard
@bp.get('/stats')
@admin_required
def stats():
    total = query('''SELECT
        (SELECT COUNT(*) FROM pengguna WHERE role = 'pengguna') AS total_pengguna,
        (SELECT COUNT(*) FROM pengguna WHERE role = 'pengguna' AND status_aktif = 1) AS pengguna_aktif,
        (SELECT COUNT(*) FROM hasil_deteksi) AS total_deteksi,
        (SELECT COUNT(*) FROM hasil_deteksi WHERE DATE(tanggal_deteksi) = CURDATE()) AS deteksi_hari_ini,
        (SELECT ROUND(AVG(confidence_score), 2) FROM hasil_deteksi) AS rata_confidence''', one=True)
    per_penyakit = query('''SELECT p.nama, p.kode_kelas, COUNT(h.id_hasil) AS jumlah
        FROM penyakit p LEFT JOIN hasil_deteksi h ON h.id_penyakit = p.id_penyakit
        GROUP BY p.id_penyakit ORDER BY p.id_penyakit''')
    per_hari = query('''SELECT DATE(tanggal_deteksi) AS tanggal, COUNT(*) AS jumlah FROM hasil_deteksi
        WHERE tanggal_deteksi >= CURDATE() - INTERVAL 6 DAY GROUP BY DATE(tanggal_deteksi) ORDER BY tanggal''')
    model = query('SELECT nama, versi, akurasi FROM model_cnn WHERE aktif = 1 LIMIT 1', one=True)
    if total['rata_confidence'] is not None:
        total['rata_confidence'] = float(total['rata_confidence'])
    if model and model['akurasi'] is not None:
        model['akurasi'] = float(model['akurasi'])
    return jsonify(total=total, per_penyakit=per_penyakit, per_hari=_fmt_dates(per_hari, 'tanggal'), model_aktif=model)


# ---------------------------------------------------------------- pengguna
@bp.get('/users')
@admin_required
def list_users():
    rows = query('''SELECT u.id_pengguna, u.nama, u.email, u.role, u.tanggal_daftar, u.status_aktif,
                           COUNT(c.id_citra) AS jumlah_deteksi
                    FROM pengguna u LEFT JOIN citra_daun c ON c.id_pengguna = u.id_pengguna
                    GROUP BY u.id_pengguna ORDER BY u.id_pengguna''')
    return jsonify(_fmt_dates(rows, 'tanggal_daftar'))


@bp.post('/users')
@admin_required
def create_user():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    if not (data.get('nama') or '').strip() or not EMAIL_RE.match(email) or len(data.get('password') or '') < 6:
        return jsonify(message='Nama, email valid, dan password (min. 6 karakter) wajib diisi'), 400
    if query('SELECT 1 FROM pengguna WHERE email = %s', (email,), one=True):
        return jsonify(message='Email sudah terdaftar'), 409
    role = data.get('role') if data.get('role') in ('admin', 'pengguna') else 'pengguna'
    new_id = execute('INSERT INTO pengguna (nama, email, password, role) VALUES (%s, %s, %s, %s)',
                     (data['nama'].strip(), email, generate_password_hash(data['password']), role))
    return jsonify(message='Pengguna ditambahkan', id_pengguna=new_id), 201


@bp.put('/users/<int:id_pengguna>')
@admin_required
def update_user(id_pengguna):
    data = request.get_json(silent=True) or {}
    user = query('SELECT * FROM pengguna WHERE id_pengguna = %s', (id_pengguna,), one=True)
    if not user:
        return jsonify(message='Pengguna tidak ditemukan'), 404
    if id_pengguna == g.user['id_pengguna'] and (data.get('status_aktif') == 0 or data.get('role') == 'pengguna'):
        return jsonify(message='Tidak dapat menonaktifkan atau menurunkan role akun sendiri'), 400

    nama = (data.get('nama') or user['nama']).strip()
    role = data.get('role') if data.get('role') in ('admin', 'pengguna') else user['role']
    status = int(data['status_aktif']) if 'status_aktif' in data else user['status_aktif']
    execute('UPDATE pengguna SET nama = %s, role = %s, status_aktif = %s WHERE id_pengguna = %s',
            (nama, role, status, id_pengguna))
    if data.get('password'):
        execute('UPDATE pengguna SET password = %s WHERE id_pengguna = %s',
                (generate_password_hash(data['password']), id_pengguna))
    return jsonify(message='Data pengguna diperbarui')


# ---------------------------------------------------------------- log deteksi
@bp.get('/logs')
@admin_required
def logs():
    rows = query(DETAIL_SQL.replace('FROM hasil_deteksi h',
                                    ', u.nama AS nama_pengguna, u.email FROM hasil_deteksi h')
                 + ' JOIN pengguna u ON u.id_pengguna = c.id_pengguna ORDER BY h.tanggal_deteksi DESC, h.id_hasil DESC')
    return jsonify([serialize_hasil(r) for r in rows])


# ---------------------------------------------------------------- model CNN
@bp.get('/models')
@admin_required
def list_models():
    rows = query('SELECT * FROM model_cnn ORDER BY id_model DESC')
    for r in rows:
        r['akurasi'] = float(r['akurasi']) if r['akurasi'] is not None else None
        p = Path(r['path_file'])
        r['file_tersedia'] = (p if p.is_absolute() else Config.MODEL_DIR / p).exists()
    return jsonify(_fmt_dates(rows, 'tanggal_pelatihan'))


@bp.post('/models')
@admin_required
def add_model():
    """Mendaftarkan model baru. Dapat berupa unggahan file .keras/.h5 atau path file yang sudah ada."""
    form = request.form if (request.form or request.files) else (request.get_json(silent=True) or {})
    file = request.files.get('file')
    if file and file.filename:
        if not file.filename.lower().endswith(('.keras', '.h5')):
            return jsonify(message='File model harus berformat .keras atau .h5'), 400
        Config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path_file = Path(file.filename).name
        file.save(Config.MODEL_DIR / path_file)
    else:
        path_file = (form.get('path_file') or '').strip()
    if not path_file or not (form.get('nama') or '').strip() or not (form.get('versi') or '').strip():
        return jsonify(message='Nama, versi, dan file model wajib diisi'), 400

    akurasi = form.get('akurasi')
    new_id = execute('''INSERT INTO model_cnn (nama, arsitektur, versi, akurasi, path_file, tanggal_pelatihan)
                        VALUES (%s, %s, %s, %s, %s, %s)''',
                     (form['nama'].strip(), form.get('arsitektur') or 'MobileNetV2', form['versi'].strip(),
                      float(akurasi) if akurasi not in (None, '') else None, path_file,
                      form.get('tanggal_pelatihan') or None))
    return jsonify(message='Model ditambahkan', id_model=new_id), 201


@bp.put('/models/<int:id_model>/aktifkan')
@admin_required
def activate_model(id_model):
    model = query('SELECT * FROM model_cnn WHERE id_model = %s', (id_model,), one=True)
    if not model:
        return jsonify(message='Model tidak ditemukan'), 404
    p = Path(model['path_file'])
    if not (p if p.is_absolute() else Config.MODEL_DIR / p).exists():
        return jsonify(message='File model tidak ditemukan di server'), 400
    execute('UPDATE model_cnn SET aktif = (id_model = %s)', (id_model,))
    return jsonify(message=f"Model {model['nama']} v{model['versi']} diaktifkan")


@bp.delete('/models/<int:id_model>')
@admin_required
def delete_model(id_model):
    model = query('SELECT aktif FROM model_cnn WHERE id_model = %s', (id_model,), one=True)
    if not model:
        return jsonify(message='Model tidak ditemukan'), 404
    if model['aktif']:
        return jsonify(message='Model yang sedang aktif tidak dapat dihapus'), 400
    execute('DELETE FROM model_cnn WHERE id_model = %s', (id_model,))
    return jsonify(message='Model dihapus')
