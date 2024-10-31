from sqlalchemy import create_engine
from config import MONGO_URL


def optimize_database():
    engine = create_engine(MONGO_URL)
    with engine.connect() as conn:
        conn.execute("VACUUM;")
        conn.execute("ANALYZE;")
