from functools import wraps

from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config
from db import query

_serializer = URLSafeTimedSerializer(Config.SECRET_KEY, salt='auth-token')


def create_token(user):
    return _serializer.dumps({'id': user['id_pengguna'], 'role': user['role']})


def _current_user():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    try:
        data = _serializer.loads(header[7:], max_age=Config.TOKEN_EXPIRES)
    except (BadSignature, SignatureExpired):
        return None
    return query('SELECT id_pengguna, nama, email, role, status_aktif FROM pengguna WHERE id_pengguna = %s',
                 (data['id'],), one=True)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = _current_user()
        if not user or not user['status_aktif']:
            return jsonify(message='Sesi tidak valid, silakan login kembali'), 401
        g.user = user
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if g.user['role'] != 'admin':
            return jsonify(message='Akses khusus administrator'), 403
        return fn(*args, **kwargs)
    return wrapper
