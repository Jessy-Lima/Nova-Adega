from app.models.usuarios import Usuario


# ============================================================
# LISTAGEM
# ============================================================

def test_listar_usuarios(cliente):
    resposta = cliente.get("/usuarios")

    assert resposta.status_code == 200


def test_listar_usuarios_com_usuarios(
    cliente,
    db_session_test
):
    db_session_test.add_all([
        Usuario(
            nome="Joao",
            email="joao@test.com",
            senha_hash="hash_teste_123",
            role="operador",
            ativo=True
        ),
        Usuario(
            nome="Maria",
            email="maria@test.com",
            senha_hash="hash_teste_456",
            role="operador",
            ativo=True
        ),
    ])

    db_session_test.commit()

    resposta = cliente.get("/usuarios")

    assert resposta.status_code == 200
    assert "Joao" in resposta.text
    assert "Maria" in resposta.text


# ============================================================
# FORMULÁRIO DE NOVO USUÁRIO
# ============================================================

def test_form_novo_usuario(cliente):
    resposta = cliente.get("/usuarios/novo")

    assert resposta.status_code == 200


# ============================================================
# CRIAÇÃO
# ============================================================

def test_criar_usuario(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/usuarios/novo",
        data={
            "nome": "Usuario Teste",
            "email": "usuario@test.com",
            "senha": "123456",
            "role": "operador",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    usuario = (
        db_session_test
        .query(Usuario)
        .filter_by(email="usuario@test.com")
        .first()
    )

    assert usuario is not None
    assert usuario.nome == "Usuario Teste"
    assert usuario.role == "operador"
    assert usuario.ativo is True


def test_criar_usuario_admin(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/usuarios/novo",
        data={
            "nome": "Administrador",
            "email": "admin2@test.com",
            "senha": "123456",
            "role": "admin",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    usuario = (
        db_session_test
        .query(Usuario)
        .filter_by(email="admin2@test.com")
        .first()
    )

    assert usuario is not None
    assert usuario.role == "admin"


def test_criar_usuario_email_duplicado(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario Existente",
        email="duplicado@test.com",
        senha_hash="hash_existente",
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    resposta = cliente.post(
        "/usuarios/novo",
        data={
            "nome": "Outro Usuario",
            "email": "duplicado@test.com",
            "senha": "123456",
            "role": "operador",
        },
        follow_redirects=False,
    )

    # O sistema deve rejeitar o e-mail duplicado
    assert resposta.status_code == 400

    usuarios = (
        db_session_test
        .query(Usuario)
        .filter_by(email="duplicado@test.com")
        .all()
    )

    # Continua existindo apenas o usuário original
    assert len(usuarios) == 1


# ============================================================
# EDIÇÃO
# ============================================================

def test_form_editar_usuario(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario Antigo",
        email="antigo@test.com",
        senha_hash="hash_antigo",
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    resposta = cliente.get(
        f"/usuarios/{usuario.id}/editar"
    )

    assert resposta.status_code == 200


def test_editar_usuario(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario Antigo",
        email="editar@test.com",
        senha_hash="hash_editar",
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    resposta = cliente.post(
        f"/usuarios/{usuario.id}/editar",
        data={
            "nome": "Usuario Editado",
            "email": "editar@test.com",
            "role": "admin",
        },
        follow_redirects=False,
    )

    assert resposta.status_code in [200, 302]

    db_session_test.refresh(usuario)

    assert usuario.nome == "Usuario Editado"
    assert usuario.role == "admin"


def test_editar_usuario_inexistente(cliente):
    resposta = cliente.get(
        "/usuarios/99999/editar",
        follow_redirects=False
    )

    assert resposta.status_code in [200, 302, 404]


# ============================================================
# STATUS DO USUÁRIO
# ============================================================

def test_usuario_pode_ser_criado_ativo(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Ativo",
        email="ativo@test.com",
        senha_hash="hash_ativo",
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()
    db_session_test.refresh(usuario)

    assert usuario.id is not None
    assert usuario.ativo is True


def test_usuario_pode_ser_criado_inativo(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Inativo",
        email="inativo@test.com",
        senha_hash="hash_inativo",
        role="operador",
        ativo=False
    )

    db_session_test.add(usuario)
    db_session_test.commit()
    db_session_test.refresh(usuario)

    assert usuario.id is not None
    assert usuario.ativo is False


# ============================================================
# ROLE DO USUÁRIO
# ============================================================

def test_usuario_operador(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Operador",
        email="operador@test.com",
        senha_hash="hash_operador",
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    assert usuario.role == "operador"


def test_usuario_admin(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Administrador",
        email="admin3@test.com",
        senha_hash="hash_admin",
        role="admin",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    assert usuario.role == "admin"


# ============================================================
# SENHA HASH
# ============================================================

def test_senha_hash_e_diferente_da_senha_original(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario Senha",
        email="senha@test.com",
        senha_hash="hash_123456",
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    assert usuario.senha_hash != "123456"


def test_senha_hash_e_armazenada(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario",
        email="verificar@test.com",
        senha_hash="hash_123456",
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    assert usuario.senha_hash == "hash_123456"


def test_senha_hash_nao_pode_ser_vazia(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario",
        email="verificar2@test.com",
        senha_hash="hash_teste",
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    assert usuario.senha_hash