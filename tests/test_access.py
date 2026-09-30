def test_acesso_pagina_inicial(cliente):
    resposta = cliente.get("/")

    assert resposta.status_code == 200


def test_acesso_produtos(cliente):
    resposta = cliente.get("/produtos/")

    assert resposta.status_code == 200


def test_acesso_novo_produto(cliente):
    resposta = cliente.get("/produtos/novo")

    assert resposta.status_code == 200


def test_acesso_categorias(cliente):
    resposta = cliente.get("/categorias/")

    assert resposta.status_code == 200


def test_acesso_nova_categoria(cliente):
    resposta = cliente.get("/categorias/nova")

    assert resposta.status_code == 200


def test_acesso_clientes(cliente):
    resposta = cliente.get("/clientes/")

    assert resposta.status_code == 200


def test_acesso_novo_cliente(cliente):
    resposta = cliente.get("/clientes/novo")

    assert resposta.status_code == 200


def test_acesso_usuarios(cliente):
    resposta = cliente.get("/usuarios")

    assert resposta.status_code == 200


def test_acesso_novo_usuario(cliente):
    resposta = cliente.get("/usuarios/novo")

    assert resposta.status_code == 200


def test_acesso_pdv(cliente):
    resposta = cliente.get("/pdv/")

    assert resposta.status_code == 200


def test_acesso_movimentacoes(cliente):
    resposta = cliente.get("/movimentacoes/")

    assert resposta.status_code == 200