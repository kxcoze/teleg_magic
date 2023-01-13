from dataclasses import dataclass
from os import getenv

ADMIN_TOKEN = getenv("ADMIN_TOKEN")
ADMINS_CHAT_ID = getenv("ADMINS_CHAT_ID")


@dataclass
class DB:
    host: str
    db_name: str
    user: str
    password: str


@dataclass
class API:
    id: int
    hash: str


@dataclass
class Config:
    db: DB
    api: API
    sleep_time: int


def load_config():
    return Config(
        db = DB(
            host=getenv('DB_HOST'),
            db_name=getenv('DB_NAME'),
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD'),
        ),
        api = API(
            id=getenv('API_ID'),
            hash=getenv('API_HASH'),
        ),
        sleep_time=int(getenv('SLEEP_TIME')),
    )


dict_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "telegram_formatter": {
            "format": "{levelname} — {module}:{funcName}:{lineno} — {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "WARNING",
            "filename": "messages.log",
        },
        "telegram": {
            "level": "WARNING",
            "class": "aiolog.telegram.Handler",
            "formatter": "telegram_formatter",
            "timeout": 60,  # 60 by default
            "queue_size": 1000,  # 1000 by default
            "token": ADMIN_TOKEN,
            "chats": ADMINS_CHAT_ID,
        }
    },
    "root": {
        "level": 'INFO',
        "handlers": ["console", "file", "telegram"],
    },
}