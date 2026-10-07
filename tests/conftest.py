import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.auth import (
    get_admin,
    get_usuario_logado,
    get_usuario_opcional
)


# ============================================================
# BANCO DE DADOS DE TESTE
# ============================================================

@pytest.fixture()
def db_session_test():
    """
    Cria um banco SQLite em memória para os testes.

    O banco existe somente durante o teste e não altera
    o banco.db real do projeto.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # Cria todas as tabelas do projeto
    Base.metadata.create_all(bind=engine)

    SessionTest = sessionmaker(
        autoflush=False,
        autocommit=False,
        bind=engine
    )

    session = SessionTest()

    try:
        yield session

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


# ============================================================
# CLIENTE DE TESTE
# ============================================================

@pytest.fixture()
def cliente(db_session_test):
    """
    Cria um TestClient do FastAPI usando o banco de teste.

    Também simula um usuário administrador logado.
    """

    # Substitui o get_db original pelo banco de teste
    def override_get_db():
        yield db_session_test

    # Usuário falso para os testes
    def usuario_falso():
        return {
            "sub": "teste@admin.com",
            "nome": "Admin Teste",
            "role": "admin",
            "roles": "admin",
            "id": 1
        }

    # Substitui as dependências reais
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_usuario_logado] = usuario_falso
    app.dependency_overrides[get_usuario_opcional] = usuario_falso
    app.dependency_overrides[get_admin] = usuario_falso

    # Cria o cliente usado pelos testes
    with TestClient(app) as teste_cliente:
        yield teste_cliente

    # Remove as substituições depois do teste
    app.dependency_overrides.clear()