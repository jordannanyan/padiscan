from flask import Blueprint, jsonify, request

from auth import admin_required, login_required
from db import execute, query

bp = Blueprint('penyakit', __name__, url_prefix='/api/penyakit')

FIELDS = ('nama', 'nama_latin', 'deskripsi', 'gejala', 'penanganan')


@bp.get('')
@login_required
def list_penyakit():
    return jsonify(query('SELECT * FROM penyakit ORDER BY id_penyakit'))


@bp.get('/<int:id_penyakit>')
@login_required
def get_penyakit(id_penyakit):
    row = query('SELECT * FROM penyakit WHERE id_penyakit = %s', (id_penyakit,), one=True)
    return (jsonify(row), 200) if row else (jsonify(message='Data penyakit tidak ditemukan'), 404)


@bp.put('/<int:id_penyakit>')
@admin_required
def update_penyakit(id_penyakit):
    data = request.get_json(silent=True) or {}
    if not (data.get('nama') or '').strip():
        return jsonify(message='Nama penyakit wajib diisi'), 400
    if not query('SELECT 1 FROM penyakit WHERE id_penyakit = %s', (id_penyakit,), one=True):
        return jsonify(message='Data penyakit tidak ditemukan'), 404
    execute(f"UPDATE penyakit SET {', '.join(f'{f} = %s' for f in FIELDS)} WHERE id_penyakit = %s",
            tuple(data.get(f) for f in FIELDS) + (id_penyakit,))
    return jsonify(message='Data penyakit diperbarui')
