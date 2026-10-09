
from app.models.categoria import Categoria
from app.models.produto import Produto


# ============================================================
# LISTAGEM
# ============================================================

def test_listar_categorias(cliente):
    resposta = cliente.get("/categorias/")

    assert resposta.status_code == 200


def test_listar_categorias_com_paginacao(cliente):
    resposta = cliente.get(
        "/categorias/?pagina=1&por_pagina=3"
    )

    assert resposta.status_code == 200


def test_listar_categorias_pagina_invalida(cliente):
    resposta = cliente.get(
        "/categorias/?pagina=0"
    )

    assert resposta.status_code == 200


# ============================================================
# FORMULÁRIO DE NOVA CATEGORIA
# ============================================================

def test_form_nova_categoria(cliente):
    resposta = cliente.get("/categorias/nova")

    assert resposta.status_code == 200


# ============================================================
# CRIAÇÃO
# ============================================================

def test_criar_categoria_com_sucesso(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/categorias/nova",
        data={"nome": "Vinhos"},
        follow_redirects=False
    )

    assert resposta.status_code == 302
    assert "/categorias" in resposta.headers["location"]

    categoria = db_session_test.query(Categoria).filter(
        Categoria.nome == "Vinhos"
    ).first()

    assert categoria is not None
    assert categoria.nome == "Vinhos"


def test_criar_categoria_com_nome_com_espacos(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/categorias/nova",
        data={"nome": "  Vinhos  "},
        follow_redirects=False
    )

    assert resposta.status_code == 302

    categoria = db_session_test.query(Categoria).filter(
        Categoria.nome == "Vinhos"
    ).first()

    assert categoria is not None
    assert categoria.nome == "Vinhos"


def test_criar_categoria_duplicada(
    cliente,
    db_session_test
):
    categoria = Categoria(nome="Vinhos")

    db_session_test.add(categoria)
    db_session_test.commit()

    resposta = cliente.post(
        "/categorias/nova",
        data={"nome": "Vinhos"}
    )

    assert resposta.status_code == 400
    assert "Já existe uma categoria" in resposta.text


def test_criar_categoria_duplicada_ignorando_maiusculas(
    cliente,
    db_session_test
):
    categoria = Categoria(nome="Vinhos")

    db_session_test.add(categoria)
    db_session_test.commit()

    resposta = cliente.post(
        "/categorias/nova",
        data={"nome": "VINHOS"}
    )

    assert resposta.status_code == 400
    assert "Já existe uma categoria" in resposta.text


# ============================================================
# EDIÇÃO
# ============================================================

def test_form_editar_categoria(
    cliente,
    db_session_test
):
    categoria = Categoria(nome="Vinhos")

    db_session_test.add(categoria)
    db_session_test.commit()
    db_session_test.refresh(categoria)

    resposta = cliente.get(
        f"/categorias/{categoria.id}/editar"
    )

    assert resposta.status_code == 200


def test_editar_categoria_com_sucesso(
    cliente,
    db_session_test
):
    categoria = Categoria(nome="Vinhos")

    db_session_test.add(categoria)
    db_session_test.commit()
    db_session_test.refresh(categoria)

    resposta = cliente.post(
        f"/categorias/{categoria.id}/editar",
        data={"nome": "Vinhos Tintos"},
        follow_redirects=False
    )

    assert resposta.status_code == 302

    db_session_test.refresh(categoria)

    assert categoria.nome == "Vinhos Tintos"


def test_editar_categoria_inexistente(cliente):
    resposta = cliente.get(
        "/categorias/99999/editar",
        follow_redirects=False
    )

    assert resposta.status_code == 302
    assert "/categorias" in resposta.headers["location"]


def test_editar_categoria_inexistente_post(cliente):
    resposta = cliente.post(
        "/categorias/99999/editar",
        data={"nome": "Nova Categoria"},
        follow_redirects=False
    )

    assert resposta.status_code == 302
    assert "/categorias" in resposta.headers["location"]


def test_editar_categoria_com_nome_duplicado(
    cliente,
    db_session_test
):
    categoria1 = Categoria(nome="Vinhos")
    categoria2 = Categoria(nome="Cervejas")

    db_session_test.add_all([categoria1, categoria2])
    db_session_test.commit()
    db_session_test.refresh(categoria1)
    db_session_test.refresh(categoria2)

    resposta = cliente.post(
        f"/categorias/{categoria2.id}/editar",
        data={"nome": "Vinhos"}
    )

    assert resposta.status_code == 400
    assert "Já existe outra categoria" in resposta.text


def test_editar_categoria_ignorando_proprio_nome(
    cliente,
    db_session_test
):
    categoria = Categoria(nome="Vinhos")

    db_session_test.add(categoria)
    db_session_test.commit()
    db_session_test.refresh(categoria)

    resposta = cliente.post(
        f"/categorias/{categoria.id}/editar",
        data={"nome": "Vinhos"},
        follow_redirects=False
    )

    assert resposta.status_code == 302

    db_session_test.refresh(categoria)

    assert categoria.nome == "Vinhos"


# ============================================================
# ATIVAR / DESATIVAR
# ============================================================

def test_desativar_categoria(
    cliente,
    db_session_test
):
    categoria = Categoria(
        nome="Vinhos",
        ativo=True
    )

    db_session_test.add(categoria)
    db_session_test.commit()
    db_session_test.refresh(categoria)

    resposta = cliente.post(
        f"/categorias/{categoria.id}/toggle-ativo",
        follow_redirects=False
    )

    assert resposta.status_code == 302

    db_session_test.refresh(categoria)

    assert categoria.ativo is False


def test_ativar_categoria(
    cliente,
    db_session_test
):
    categoria = Categoria(
        nome="Vinhos",
        ativo=False
    )

    db_session_test.add(categoria)
    db_session_test.commit()
    db_session_test.refresh(categoria)

    resposta = cliente.post(
        f"/categorias/{categoria.id}/toggle-ativo",
        follow_redirects=False
    )

    assert resposta.status_code == 302

    db_session_test.refresh(categoria)

    assert categoria.ativo is True


def test_toggle_categoria_inexistente(cliente):
    resposta = cliente.post(
        "/categorias/99999/toggle-ativo",
        follow_redirects=False
    )

    assert resposta.status_code == 302
    assert "/categorias" in resposta.headers["location"]


# ============================================================
# CATEGORIA COM PRODUTO VINCULADO
# ============================================================

def test_nao_desativar_categoria_com_produto_ativo(
    cliente,
    db_session_test
):
    categoria = Categoria(
        nome="Vinhos",
        ativo=True
    )

    db_session_test.add(categoria)
    db_session_test.commit()
    db_session_test.refresh(categoria)

    produto = Produto(
        nome="Vinho Tinto",
        preco=50.00,
        estoque_atual=10,
        ativo=True,
        categoria_id=categoria.id
    )

    db_session_test.add(produto)
    db_session_test.commit()

    resposta = cliente.post(
        f"/categorias/{categoria.id}/toggle-ativo",
        follow_redirects=False
    )

    assert resposta.status_code == 302
    assert "produtos_vinculados" in resposta.headers["location"]

    db_session_test.refresh(categoria)

    assert categoria.ativo is True