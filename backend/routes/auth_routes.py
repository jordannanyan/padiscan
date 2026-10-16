import re

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from auth import create_token, login_required
from db import execute, query

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _public(user):
    return {k: user[k] for k in ('id_pengguna', 'nama', 'email', 'role')}


@bp.post('/register')
def register():
    data = request.get_json(silent=True) or {}
    nama = (data.get('nama') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not nama or not EMAIL_RE.match(email):
        return jsonify(message='Nama dan email yang valid wajib diisi'), 400
    if len(password) < 6:
        return jsonify(message='Password minimal 6 karakter'), 400
    if query('SELECT 1 FROM pengguna WHERE email = %s', (email,), one=True):
        return jsonify(message='Email sudah terdaftar'), 409

    user_id = execute('INSERT INTO pengguna (nama, email, password, role) VALUES (%s, %s, %s, %s)',
                      (nama, email, generate_password_hash(password), 'pengguna'))
    return jsonify(message='Registrasi berhasil, silakan login', id_pengguna=user_id), 201


@bp.post('/login')
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    user = query('SELECT * FROM pengguna WHERE email = %s', (email,), one=True)

    if not user or not check_password_hash(user['password'], data.get('password') or ''):
        return jsonify(message='Email atau password salah'), 401
    if not user['status_aktif']:
        return jsonify(message='Akun Anda dinonaktifkan, hubungi administrator'), 403

    return jsonify(token=create_token(user), user=_public(user))


@bp.get('/me')
@login_required
def me():
    return jsonify(user=_public(g.user))


@bp.put('/profil')
@login_required
def update_profil():
    data = request.get_json(silent=True) or {}
    nama = (data.get('nama') or '').strip()
    if not nama:
        return jsonify(message='Nama wajib diisi'), 400
    execute('UPDATE pengguna SET nama = %s WHERE id_pengguna = %s', (nama, g.user['id_pengguna']))
    if data.get('password'):
        if len(data['password']) < 6:
            return jsonify(message='Password minimal 6 karakter'), 400
        execute('UPDATE pengguna SET password = %s WHERE id_pengguna = %s',
                (generate_password_hash(data['password']), g.user['id_pengguna']))
    return jsonify(message='Profil diperbarui')


@bp.post('/logout')
@login_required
def logout():
    # Token bersifat stateless; frontend cukup menghapus token yang tersimpan.
    return jsonify(message='Logout berhasil')
