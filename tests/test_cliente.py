
from app.models.cliente import Cliente


# ============================================================
# LISTAGEM
# ============================================================

def test_listar_clientes(cliente):
    resposta = cliente.get("/clientes/")

    assert resposta.status_code == 200


def test_listar_clientes_pagina_invalida(cliente):
    resposta = cliente.get(
        "/clientes/",
        params={"pagina": 0}
    )

    assert resposta.status_code == 200


def test_listar_clientes_pagina_alta(
    cliente,
    db_session_test
):
    db_session_test.add_all([
        Cliente(nome="Ana"),
        Cliente(nome="Bruno"),
        Cliente(nome="Carlos"),
        Cliente(nome="Daniel"),
    ])

    db_session_test.commit()

    resposta = cliente.get(
        "/clientes/",
        params={
            "pagina": 999,
            "por_pagina": 2
        }
    )

    assert resposta.status_code == 200
    assert "Carlos" in resposta.text
    assert "Daniel" in resposta.text
    assert "Ana" not in resposta.text
    assert "Bruno" not in resposta.text


# ============================================================
# BUSCA
# ============================================================

def test_buscar_cliente_por_nome(
    cliente,
    db_session_test
):
    db_session_test.add_all([
        Cliente(nome="Jose", telefone="1111"),
        Cliente(nome="Helen", telefone="2222"),
    ])

    db_session_test.commit()

    resposta = cliente.get(
        "/clientes/",
        params={"busca": "Jose"}
    )

    assert resposta.status_code == 200
    assert "Jose" in resposta.text
    assert "Helen" not in resposta.text


def test_buscar_cliente_por_telefone(
    cliente,
    db_session_test
):
    db_session_test.add_all([
        Cliente(
            nome="Jose",
            telefone="11111111"
        ),
        Cliente(
            nome="Helen",
            telefone="22222222"
        ),
    ])

    db_session_test.commit()

    resposta = cliente.get(
        "/clientes/",
        params={"busca": "1111"}
    )

    assert resposta.status_code == 200
    assert "Jose" in resposta.text
    assert "Helen" not in resposta.text


def test_busca_cliente_sem_resultado(cliente):
    resposta = cliente.get(
        "/clientes/",
        params={"busca": "ClienteQueNaoExiste"}
    )

    assert resposta.status_code == 200


# ============================================================
# FORMULÁRIO DE NOVO CLIENTE
# ============================================================

def test_form_novo_cliente(cliente):
    resposta = cliente.get("/clientes/novo")

    assert resposta.status_code == 200


# ============================================================
# CRIAÇÃO
# ============================================================

def test_criar_cliente(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/clientes/novo",
        data={
            "nome": "Maria",
            "telefone": "11999999999",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/clientes?criado=ok"

    cliente_db = (
        db_session_test
        .query(Cliente)
        .filter_by(nome="Maria")
        .first()
    )

    assert cliente_db is not None
    assert cliente_db.telefone == "11999999999"
    assert cliente_db.is_associado is False
    assert cliente_db.ativo is True


def test_criar_cliente_associado(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/clientes/novo",
        data={
            "nome": "Associado",
            "telefone": "11988888888",
            "is_associado": "on",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    cliente_db = (
        db_session_test
        .query(Cliente)
        .filter_by(nome="Associado")
        .first()
    )

    assert cliente_db is not None
    assert cliente_db.is_associado is True
    assert cliente_db.ativo is True


def test_criar_cliente_sem_telefone(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/clientes/novo",
        data={
            "nome": "Cliente Sem Telefone",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    cliente_db = (
        db_session_test
        .query(Cliente)
        .filter_by(nome="Cliente Sem Telefone")
        .first()
    )

    assert cliente_db is not None
    assert cliente_db.telefone is None


def test_criar_cliente_remove_espacos(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/clientes/novo",
        data={
            "nome": "   Maria Silva   ",
            "telefone": "   11999999999   ",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    cliente_db = (
        db_session_test
        .query(Cliente)
        .filter_by(nome="Maria Silva")
        .first()
    )

    assert cliente_db is not None
    assert cliente_db.telefone == "11999999999"


# ============================================================
# EDIÇÃO
# ============================================================

def test_form_editar_cliente(
    cliente,
    db_session_test
):
    cliente_db = Cliente(
        nome="Antigo",
        telefone="1111"
    )

    db_session_test.add(cliente_db)
    db_session_test.commit()

    resposta = cliente.get(
        f"/clientes/{cliente_db.id}/editar"
    )

    assert resposta.status_code == 200
    assert "Antigo" in resposta.text


def test_editar_cliente(
    cliente,
    db_session_test
):
    cliente_db = Cliente(
        nome="Antigo",
        telefone="1111"
    )

    db_session_test.add(cliente_db)
    db_session_test.commit()

    resposta = cliente.post(
        f"/clientes/{cliente_db.id}/editar",
        data={
            "nome": "Novo",
            "telefone": "2222",
            "is_associado": "on",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/clientes?editado=ok"

    db_session_test.refresh(cliente_db)

    assert cliente_db.nome == "Novo"
    assert cliente_db.telefone == "2222"
    assert cliente_db.is_associado is True


def test_editar_cliente_remove_espacos(
    cliente,
    db_session_test
):
    cliente_db = Cliente(
        nome="Antigo",
        telefone="1111"
    )

    db_session_test.add(cliente_db)
    db_session_test.commit()

    resposta = cliente.post(
        f"/clientes/{cliente_db.id}/editar",
        data={
            "nome": "   Novo Nome   ",
            "telefone": "   3333   ",
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302

    db_session_test.refresh(cliente_db)

    assert cliente_db.nome == "Novo Nome"
    assert cliente_db.telefone == "3333"
    assert cliente_db.is_associado is False


def test_editar_cliente_inexistente(cliente):
    resposta = cliente.post(
        "/clientes/99999/editar",
        data={
            "nome": "Novo",
            "telefone": "2222"
        },
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/clientes"


def test_form_editar_cliente_inexistente(cliente):
    resposta = cliente.get(
        "/clientes/99999/editar",
        follow_redirects=False
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/clientes"


# ============================================================
# ATIVAR / DESATIVAR
# ============================================================

def test_desativar_cliente(
    cliente,
    db_session_test
):
    cliente_db = Cliente(
        nome="Cliente",
        ativo=True
    )

    db_session_test.add(cliente_db)
    db_session_test.commit()

    resposta = cliente.post(
        f"/clientes/{cliente_db.id}/toggle-ativo",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/clientes"

    db_session_test.refresh(cliente_db)

    assert cliente_db.ativo is False


def test_ativar_cliente(
    cliente,
    db_session_test
):
    cliente_db = Cliente(
        nome="Cliente Inativo",
        ativo=False
    )

    db_session_test.add(cliente_db)
    db_session_test.commit()

    resposta = cliente.post(
        f"/clientes/{cliente_db.id}/toggle-ativo",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/clientes"

    db_session_test.refresh(cliente_db)

    assert cliente_db.ativo is True


def test_toggle_cliente_inexistente(cliente):
    resposta = cliente.post(
        "/clientes/99999/toggle-ativo",
        follow_redirects=False,
    )

    assert resposta.status_code == 302
    assert resposta.headers["location"] == "/clientes"