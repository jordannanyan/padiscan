from flask import Blueprint, g, jsonify

from auth import login_required
from db import execute, query
from routes.detect_routes import DETAIL_SQL, serialize_hasil

bp = Blueprint('history', __name__, url_prefix='/api/history')


@bp.get('')
@login_required
def list_history():
    rows = query(DETAIL_SQL + ' WHERE c.id_pengguna = %s ORDER BY h.tanggal_deteksi DESC, h.id_hasil DESC',
                 (g.user['id_pengguna'],))
    return jsonify([serialize_hasil(r) for r in rows])


@bp.get('/<int:id_hasil>')
@login_required
def detail_history(id_hasil):
    row = query(DETAIL_SQL + ' WHERE h.id_hasil = %s', (id_hasil,), one=True)
    if not row or (row['id_pengguna'] != g.user['id_pengguna'] and g.user['role'] != 'admin'):
        return jsonify(message='Riwayat tidak ditemukan'), 404
    execute('INSERT INTO riwayat_deteksi (id_pengguna, id_hasil) VALUES (%s, %s)', (g.user['id_pengguna'], id_hasil))
    hasil = serialize_hasil(row)
    hasil['nama_kelas'] = {p['kode_kelas']: p['nama'] for p in query('SELECT kode_kelas, nama FROM penyakit')}
    return jsonify(hasil)


@bp.delete('/<int:id_hasil>')
@login_required
def delete_history(id_hasil):
    row = query(DETAIL_SQL + ' WHERE h.id_hasil = %s', (id_hasil,), one=True)
    if not row or row['id_pengguna'] != g.user['id_pengguna']:
        return jsonify(message='Riwayat tidak ditemukan'), 404
    execute('DELETE FROM citra_daun WHERE id_citra = %s', (row['id_citra'],))  # cascade ke hasil & riwayat
    return jsonify(message='Riwayat dihapus')
