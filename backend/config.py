import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_env():
    """Membaca file .env sederhana (KEY=VALUE) tanpa dependensi tambahan."""
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())


_load_env()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ganti-dengan-kunci-rahasia')
    TOKEN_EXPIRES = int(os.environ.get('TOKEN_EXPIRES', 60 * 60 * 24))  # detik

    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'db_penyakit_padi')

    MODEL_DIR = Path(os.environ.get('MODEL_DIR', BASE_DIR / 'models'))
    UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', BASE_DIR / 'uploads'))
    MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', 5))
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    IMG_SIZE = (224, 224)
