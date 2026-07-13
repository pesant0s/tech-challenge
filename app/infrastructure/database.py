from sqlalchemy import create_engine
from sqlalchemy.orm import registry, sessionmaker
from app.infrastructure.config import settings


# Registry de mapeamento imperativo. As entidades de domínio permanecem puras
# (sem qualquer import de SQLAlchemy); o mapeamento objeto-relacional vive em
# app/infrastructure/orm_mapping.py e é registrado neste registry.
mapper_registry = registry()
metadata = mapper_registry.metadata

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Carrega (e registra) os mapeamentos imperativos ao importar a infraestrutura
# de banco. Fica ao fim do módulo para evitar import circular: orm_mapping
# importa `mapper_registry`/`metadata` daqui, que já estão definidos acima.
from app.infrastructure import orm_mapping  # noqa: E402,F401
