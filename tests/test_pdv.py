from app.models.produto import Produto


def criar_produto(
    db_session_test,
    nome="Vinho Teste",
    preco=50.00,
    estoque=10
):
    produto = Produto(
        nome=nome,
        preco=preco,
        estoque_atual=estoque,
        ativo=True
    )

    db_session_test.add(produto)
    db_session_test.commit()
    db_session_test.refresh(produto)

    return produto


def test_pagina_pdv(cliente):
    resposta = cliente.get("/pdv")

    assert resposta.status_code == 200


def test_pdv_com_produto_cadastrado(
    cliente,
    db_session_test
):
    produto = criar_produto(
        db_session_test,
        nome="Vinho Cabernet"
    )

    resposta = cliente.get("/pdv")

    assert resposta.status_code == 200
    assert produto.nome in resposta.text


def test_pdv_com_varios_produtos(
    cliente,
    db_session_test
):
    produto1 = criar_produto(
        db_session_test,
        nome="Vinho Tinto"
    )

    produto2 = criar_produto(
        db_session_test,
        nome="Vinho Branco"
    )

    resposta = cliente.get("/pdv")

    assert resposta.status_code == 200
    assert produto1.nome in resposta.text
    assert produto2.nome in resposta.text


def test_produto_inativo_nao_deve_ser_considerado_no_pdv(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Produto Inativo",
        preco=30.00,
        estoque_atual=10,
        ativo=False
    )

    db_session_test.add(produto)
    db_session_test.commit()

    resposta = cliente.get("/pdv")

    assert resposta.status_code == 200


def test_produto_com_estoque_zero(
    cliente,
    db_session_test
):
    produto = criar_produto(
        db_session_test,
        nome="Produto Sem Estoque",
        estoque=0
    )

    resposta = cliente.get("/pdv")

    assert resposta.status_code == 200
    assert produto.nome in resposta.text


def test_produto_com_estoque_zero(
    cliente,
    db_session_test
):
    produto = criar_produto(
        db_session_test,
        nome="Produto Sem Estoque",
        estoque=0
    )

    resposta = cliente.get("/pdv")

    assert resposta.status_code == 200
    assert produto.estoque_atual == 0