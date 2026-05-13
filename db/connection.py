from sqlalchemy import URL, create_engine
from config.settings import DB_CONFIG


def get_engine():
    connection_url = URL.create(
        "postgresql+psycopg2",
        username=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        host=DB_CONFIG["host"],
        port=int(DB_CONFIG["port"]),
        database=DB_CONFIG["database"],
    )

    engine = create_engine(connection_url)
    return engine
