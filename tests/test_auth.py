from app.models.usuarios import Usuario
from app.auth import hash_senha


# ============================================================
# TELA DE LOGIN
# ============================================================

def test_pagina_login(cliente):
    resposta = cliente.get("/auth/login")

    assert resposta.status_code == 200


# ============================================================
# LOGIN COM CREDENCIAIS INVÁLIDAS
# ============================================================

def test_login_com_usuario_inexistente(cliente):
    resposta = cliente.post(
        "/auth/login",
        data={
            "email": "naoexiste@test.com",
            "senha": "123456",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 200


def test_login_com_senha_incorreta(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario Teste",
        email="login@test.com",
        senha_hash=hash_senha("senha_correta"),
        role="operador",
        ativo=True,
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    resposta = cliente.post(
        "/auth/login",
        data={
            "email": "login@test.com",
            "senha": "senha_errada",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 200


# ============================================================
# LOGIN DE USUÁRIO INATIVO
# ============================================================

def test_login_usuario_inativo(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario Inativo",
        email="inativo_login@test.com",
        senha_hash=hash_senha("senha123"),
        role="operador",
        ativo=False,
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    resposta = cliente.post(
        "/auth/login",
        data={
            "email": "inativo_login@test.com",
            "senha": "senha123",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 200


# ============================================================
# LOGIN COM SUCESSO
# ============================================================

def test_login_com_sucesso(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario Ativo",
        email="sucesso@test.com",
        senha_hash=hash_senha("senha123"),
        role="operador",
        ativo=True,
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    resposta = cliente.post(
        "/auth/login",
        data={
            "email": "sucesso@test.com",
            "senha": "senha123",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/"
    assert "access_token" in resposta.cookies


# ============================================================
# LOGOUT
# ============================================================

def test_logout(cliente):
    resposta = cliente.get(
        "/auth/logout",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/auth/login"


# ============================================================
# ACESSO À ÁREA PROTEGIDA
# ============================================================

def test_acesso_usuarios_com_usuario_logado(cliente):
    resposta = cliente.get("/usuarios")

    assert resposta.status_code == 200


def test_acesso_pagina_novo_usuario_com_usuario_logado(cliente):
    resposta = cliente.get("/usuarios/novo")

    assert resposta.status_code == 200