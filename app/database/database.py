from sqlmodel import SQLModel, Session, create_engine 
from .config import get_settings
from sqlalchemy import inspect

def get_database_engine():
    """
    Create and configure the SQLAlchemy engine.
    
    Returns:
        Engine: Configured SQLAlchemy engine
    """
    settings = get_settings()
    
    engine = create_engine(
        url=settings.DATABASE_URL_psycopg,
        echo=settings.DEBUG,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    return engine

engine = get_database_engine()

def get_session():
    with Session(engine) as session:
        yield session

def drop_all_tables_safe(engine):
    """Безопасно удаляет все таблицы, игнорируя несуществующие."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if not table_names:
        return
    SQLModel.metadata.drop_all(engine, checkfirst=True)  
        
def init_db(drop_all: bool = False) -> None:
    """
    Initialize database schema.
    
    Args:
        drop_all: If True, drops all tables before creation
    
    Raises:
        Exception: Any database-related exception
    """
    try:
        engine = get_database_engine()
        if drop_all:
            drop_all_tables_safe(engine)

        
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        raise

