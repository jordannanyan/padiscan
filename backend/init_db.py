"""Membuat database, tabel, data penyakit, akun admin, dan mendaftarkan model hasil training.

Jalankan sekali:  python init_db.py
"""
import json
import os
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

from config import Config
from db import connect

SCHEMA = Path(__file__).resolve().parent.parent / 'database' / 'schema.sql'
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@padi.id')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def split_sql(sql):
    """Memecah skrip SQL per ';' dengan mengabaikan ';' di dalam string dan komentar '--'."""
    statements, buf, quote, i = [], [], None, 0
    while i < len(sql):
        ch = sql[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif sql.startswith('--', i):
            i = sql.find('\n', i)
            if i == -1:
                break
            continue
        elif ch == ';':
            statements.append(''.join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        i += 1
    statements.append(''.join(buf).strip())
    return [s for s in statements if s]


def run_schema(conn):
    sql = SCHEMA.read_text(encoding='utf-8').replace('db_penyakit_padi', Config.DB_NAME)
    with conn.cursor() as cur:
        for stmt in split_sql(sql):
            cur.execute(stmt)


def main():
    conn = connect(database=False)
    run_schema(conn)
    print(f'[OK] Database "{Config.DB_NAME}" dan tabel siap')

    with conn.cursor() as cur:
        cur.execute(f'USE `{Config.DB_NAME}`')
        cur.execute('SELECT 1 FROM pengguna WHERE email = %s', (ADMIN_EMAIL,))
        if not cur.fetchone():
            cur.execute("INSERT INTO pengguna (nama, email, password, role) VALUES (%s, %s, %s, 'admin')",
                        ('Administrator', ADMIN_EMAIL, generate_password_hash(ADMIN_PASSWORD)))
            print(f'[OK] Akun admin dibuat -> {ADMIN_EMAIL} / {ADMIN_PASSWORD}')

        info_file = Config.MODEL_DIR / 'model_info.json'
        if info_file.exists():
            info = json.loads(info_file.read_text())
            cur.execute('SELECT 1 FROM model_cnn WHERE path_file = %s AND versi = %s', (info['file'], info['versi']))
            if not cur.fetchone():
                cur.execute('UPDATE model_cnn SET aktif = 0')
                cur.execute('''INSERT INTO model_cnn (nama, arsitektur, versi, akurasi, path_file, tanggal_pelatihan, aktif)
                               VALUES (%s, %s, %s, %s, %s, %s, 1)''',
                            (info['nama'], info['arsitektur'], info['versi'], info['akurasi'], info['file'],
                             info['tanggal_pelatihan']))
                print(f"[OK] Model {info['file']} (akurasi {info['akurasi']}) didaftarkan dan diaktifkan")
        else:
            print(f'[!] {info_file} belum ada. Salin hasil training (folder saved_model) ke {Config.MODEL_DIR}',
                  file=sys.stderr)
    conn.close()


if __name__ == '__main__':
    main()
