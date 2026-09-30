from app.models.produto import Produto
from app.models.categoria import Categoria


# ============================================================
# LISTAGEM DE PRODUTOS
# ============================================================

def test_listar_produtos(cliente):
    resposta = cliente.get("/produtos/")

    assert resposta.status_code == 200


def test_listar_produtos_com_paginacao(cliente):
    resposta = cliente.get(
        "/produtos/?pagina=1&por_pagina=5"
    )

    assert resposta.status_code == 200


def test_listar_produtos_com_busca(cliente):
    resposta = cliente.get(
        "/produtos/?busca=vinho"
    )

    assert resposta.status_code == 200


def test_listar_produtos_com_filtro_categoria(
    cliente,
    db_session_test
):
    categoria = Categoria(nome="Vinhos")

    db_session_test.add(categoria)
    db_session_test.commit()

    resposta = cliente.get(
        "/produtos/?categoria_id=1"
    )

    assert resposta.status_code == 200


# ============================================================
# FORMULÁRIO DE NOVO PRODUTO
# ============================================================

def test_form_novo_produto(cliente):
    resposta = cliente.get("/produtos/novo")

    assert resposta.status_code == 200


# ============================================================
# CRIAÇÃO DE PRODUTO
# ============================================================

def test_criar_produto_com_sucesso(
    cliente,
    db_session_test
):
    resposta = cliente.post(
        "/produtos/novo",
        data={
            "nome": "Vinho Tinto",
            "preco": "50.00",
            "estoque_atual": "10"
        },
        follow_redirects=False
    )

    assert resposta.status_code == 302

    produto = db_session_test.query(Produto).filter(
        Produto.nome == "Vinho Tinto"
    ).first()

    assert produto is not None
    assert produto.preco == 50.00
    assert produto.estoque_atual == 10


def test_criar_produto_com_categoria(
    cliente,
    db_session_test
):
    categoria = Categoria(nome="Vinhos")

    db_session_test.add(categoria)
    db_session_test.commit()
    db_session_test.refresh(categoria)

    resposta = cliente.post(
        "/produtos/novo",
        data={
            "nome": "Vinho Tinto",
            "preco": "50.00",
            "estoque_atual": "10",
            "categoria_id": str(categoria.id)
        },
        follow_redirects=False
    )

    assert resposta.status_code == 302

    produto = db_session_test.query(Produto).filter(
        Produto.nome == "Vinho Tinto"
    ).first()

    assert produto is not None
    assert produto.categoria_id == categoria.id


def test_criar_produto_duplicado(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Vinho Tinto",
        preco=50.00,
        estoque_atual=10
    )

    db_session_test.add(produto)
    db_session_test.commit()

    resposta = cliente.post(
        "/produtos/novo",
        data={
            "nome": "Vinho Tinto",
            "preco": "60.00",
            "estoque_atual": "5"
        }
    )

    assert resposta.status_code in [200, 400]


def test_criar_produto_com_preco_zero(cliente):
    resposta = cliente.post(
        "/produtos/novo",
        data={
            "nome": "Produto Teste",
            "preco": "0",
            "estoque_atual": "10"
        }
    )

    assert resposta.status_code in [200, 302, 400]


def test_criar_produto_com_estoque_zero(cliente):
    resposta = cliente.post(
        "/produtos/novo",
        data={
            "nome": "Produto Sem Estoque",
            "preco": "50.00",
            "estoque_atual": "0"
        },
        follow_redirects=False
    )

    assert resposta.status_code in [200, 302, 400]


# ============================================================
# DETALHES
# ============================================================

def test_detalhes_produto(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Vinho Tinto",
        preco=50.00,
        estoque_atual=10
    )

    db_session_test.add(produto)
    db_session_test.commit()
    db_session_test.refresh(produto)

    resposta = cliente.get(
        f"/produtos/{produto.id}"
    )

    assert resposta.status_code == 200


def test_detalhes_produto_inexistente(cliente):
    resposta = cliente.get("/produtos/99999")

    assert resposta.status_code in [200, 302, 404]


# ============================================================
# EDIÇÃO
# ============================================================

def test_form_editar_produto(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Vinho Tinto",
        preco=50.00,
        estoque_atual=10
    )

    db_session_test.add(produto)
    db_session_test.commit()
    db_session_test.refresh(produto)

    resposta = cliente.get(
        f"/produtos/{produto.id}/editar"
    )

    assert resposta.status_code == 200


def test_editar_produto(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Vinho Tinto",
        preco=50.00,
        estoque_atual=10
    )

    db_session_test.add(produto)
    db_session_test.commit()
    db_session_test.refresh(produto)

    resposta = cliente.post(
        f"/produtos/{produto.id}/editar",
        data={
            "nome": "Vinho Tinto Especial",
            "preco": "75.00",
            "estoque_atual": "20"
        },
        follow_redirects=False
    )

    assert resposta.status_code == 302

    db_session_test.refresh(produto)

    assert produto.nome == "Vinho Tinto Especial"
    assert produto.preco == 75.00
    assert produto.estoque_atual == 20


def test_editar_produto_inexistente(cliente):
    resposta = cliente.get(
        "/produtos/99999/editar"
    )

    assert resposta.status_code in [200, 302, 404]

# ============================================================
# ATIVAÇÃO / DESATIVAÇÃO
# ============================================================

def test_produto_pode_ser_criado_ativo(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Vinho Ativo",
        preco=50.00,
        estoque_atual=10,
        ativo=True
    )

    db_session_test.add(produto)
    db_session_test.commit()
    db_session_test.refresh(produto)

    assert produto.id is not None
    assert produto.ativo is True


def test_produto_pode_ser_criado_inativo(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Vinho Inativo",
        preco=50.00,
        estoque_atual=10,
        ativo=False
    )

    db_session_test.add(produto)
    db_session_test.commit()
    db_session_test.refresh(produto)

    assert produto.id is not None
    assert produto.ativo is False

# ============================================================
# PROPRIEDADE DE ESTOQUE BAIXO
# ============================================================

def test_produto_com_estoque_baixo(
    db_session_test
):
    produto = Produto(
        nome="Vinho",
        preco=50.00,
        estoque_atual=5
    )

    db_session_test.add(produto)
    db_session_test.commit()

    assert produto.estoque_baixo is True


def test_produto_com_estoque_normal(
    db_session_test
):
    produto = Produto(
        nome="Vinho",
        preco=50.00,
        estoque_atual=20
    )

    db_session_test.add(produto)
    db_session_test.commit()

    assert produto.estoque_baixo is False


# ============================================================
# IMAGEM
# ============================================================

def test_produto_com_imagem():
    produto = Produto(
        nome="Vinho",
        preco=50.00,
        estoque_atual=10,
        imagem_path="uploads/vinho.jpg"
    )

    assert produto.imagem_url == "/static/uploads/vinho.jpg"


def test_produto_sem_imagem():
    produto = Produto(
        nome="Vinho",
        preco=50.00,
        estoque_atual=10
    )

    assert produto.imagem_url == "/static/img/produto-placeholder.png"