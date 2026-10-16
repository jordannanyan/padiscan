import pymysql
from flask import g

from config import Config


def connect(database=True):
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME if database else None,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4',
        autocommit=True,
    )


def get_db():
    if 'db' not in g:
        g.db = connect()
    return g.db


def close_db(_exc=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query(sql, params=None, one=False):
    with get_db().cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone() if one else cur.fetchall()


def execute(sql, params=None):
    """Menjalankan INSERT/UPDATE/DELETE dan mengembalikan lastrowid."""
    with get_db().cursor() as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid
