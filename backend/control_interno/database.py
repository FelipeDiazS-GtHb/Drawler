from sqlalchemy import create_engine

# check_same_thread=False es vital para evitar errores en FastAPI con SQLite
engine = create_engine("sqlite:///./prototipo.db", connect_args={"check_same_thread": False})