import os

from urllib.parse import quote_plus


def _get_env(name, default=None, required=True):
    val = os.getenv(name, default)
    if required and (val is None or val == ''):
        raise ValueError('missing required env var: %s' % name)
    return val


def _get_env_int(name, default=None, required=True):
    raw = _get_env(name, default=default, required=required)
    try:
        return int(raw)
    except ValueError:
        raise ValueError('invalid int for env var: %s = %s' % (name, raw))


def _join_url(base_url, path):
    base_url = str(base_url).rstrip('/')
    path = str(path).strip()
    if not path.startswith('/'):
        raise ValueError('redirect path must start with "/": %s' % path)
    return base_url + path


class Config:
    def __init__(self):
        # Flask/App
        self.SECRET_KEY = _get_env('SECRET_KEY')
        self.APP_BASE_URL = _get_env('APP_BASE_URL')
        
        # Google SSO
        self.GOOGLE_OAUTH_CLIENT_ID = _get_env('GOOGLE_OAUTH_CLIENT_ID')
        self.GOOGLE_OAUTH_CLIENT_SECRET = _get_env('GOOGLE_OAUTH_CLIENT_SECRET')
        self.GOOGLE_OAUTH_REDIRECT_PATH = _get_env(
            'GOOGLE_OAUTH_REDIRECT_PATH',
            default='/oauth/callback',
            required=False,
        )

        # DB (used by app for CRUD ops)
        self.DB_USER = _get_env('DB_USER')
        self.DB_PASSWORD = _get_env('DB_PASSWORD')
        self.DB_NAME = _get_env('DB_NAME')
        self.DB_HOST = _get_env('DB_HOST')
        self.DB_PORT = _get_env_int('DB_PORT')

        # DB (used by Alembic for migrations)
        self.MIGRATE_DB_USER = _get_env(
            'MIGRATE_DB_USER',
            default=self.DB_USER,
            required=False
        )
        self.MIGRATE_DB_PASSWORD = _get_env(
            'MIGRATE_DB_PASSWORD',
            default=self.DB_PASSWORD,
            required=False
        )

    @property
    def GOOGLE_OAUTH_REDIRECT_URI(self):
        return _join_url(self.APP_BASE_URL, self.GOOGLE_OAUTH_REDIRECT_PATH)

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        pw = quote_plus(self.DB_PASSWORD)
        return (
            'mysql+pymysql://'
            + self.DB_USER + ':' + pw
            + '@' + self.DB_HOST + ':' + str(self.DB_PORT)
            + '/' + self.DB_NAME
            + '?charset=utf8mb4'
        )

    @property
    def MIGRATE_DATABASE_URI(self):
        pw = quote_plus(self.MIGRATE_DB_PASSWORD)
        return (
            'mysql+pymysql://'
            + self.MIGRATE_DB_USER + ':' + pw
            + '@' + self.DB_HOST + ':' + str(self.DB_PORT)
            + '/' + self.DB_NAME
            + '?charset=utf8mb4'
        )


class DevConfig(Config):
    pass


class ProdConfig(Config):
    pass
