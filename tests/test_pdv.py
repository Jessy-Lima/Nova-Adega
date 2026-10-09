import json
from app.models.produto import Produto
from app.models.venda import Venda, ItemVenda

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

def criar_dados_venda(produto, **dados_extras):
    dados = {
        "carrinho_json": json.dumps([
            {
                "produto_id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco,
                "quantidade": 1
            }
        ]),
        "cliente_id": 0,
        "observacao": "",
        "desconto_manual": 0,
        "tipo_desconto": "valor",
        "forma_pagamento_1": "dinheiro",
        "valor_pagamento_1": 50,
        "forma_pagamento_2": "",
        "valor_pagamento_2": 0
    }

    dados.update(dados_extras)

    return dados

# ============================================================
# TESTES DA TELA DO PDV
# ============================================================

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

def test_produto_inativo_nao_aparece_no_pdv(
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
    assert produto.nome not in resposta.text

def test_produto_sem_estoque_nao_aparece_no_pdv(
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
    assert produto.nome not in resposta.text
    assert produto.estoque_atual == 0

# ============================================================
# TESTES DE FINALIZAÇÃO DE VENDA
# ============================================================

def test_finalizar_venda_com_um_pagamento(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(produto)

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303

    venda = db_session_test.query(Venda).first()

    assert venda is not None
    assert venda.total_bruto == 50.00
    assert venda.total_liquido == 50.00
    assert venda.forma_pagamento_1 == "dinheiro"
    assert venda.valor_pagamento_1 == 50.00
    assert venda.valor_pagamento_2 == 0
    assert venda.forma_pagamento_2 is None

    assert produto.estoque_atual == 9

    item = db_session_test.query(ItemVenda).filter_by(
        venda_id=venda.id
    ).first()

    assert item is not None
    assert item.produto_id == produto.id
    assert item.quantidade == 1

def test_finalizar_venda_com_dois_pagamentos(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(
        produto,
        forma_pagamento_1="dinheiro",
        valor_pagamento_1=30,
        forma_pagamento_2="pix",
        valor_pagamento_2=20
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303

    venda = db_session_test.query(Venda).first()

    assert venda is not None
    assert venda.total_liquido == 50.00
    assert venda.forma_pagamento_1 == "dinheiro"
    assert venda.valor_pagamento_1 == 30.00
    assert venda.forma_pagamento_2 == "pix"
    assert venda.valor_pagamento_2 == 20.00

def test_nao_finalizar_venda_quando_pagamentos_nao_fecham_total(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(
        produto,
        valor_pagamento_1=30,
        forma_pagamento_2="pix",
        valor_pagamento_2=10
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=valor_pagamento" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0
    assert produto.estoque_atual == 10

def test_nao_finalizar_venda_com_primeiro_pagamento_zero(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(
        produto,
        valor_pagamento_1=0
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=pagamento_1" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0

def test_nao_finalizar_venda_com_pagamento_negativo(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(
        produto,
        valor_pagamento_1=-10
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=pagamento" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0

# ============================================================
# TESTES DE DESCONTO MANUAL
# ============================================================

def test_finalizar_venda_com_desconto_em_reais(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(
        produto,
        desconto_manual=10,
        tipo_desconto="valor",
        valor_pagamento_1=40
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303

    venda = db_session_test.query(Venda).first()

    assert venda is not None
    assert venda.total_bruto == 50.00
    assert venda.desconto == 10.00
    assert venda.total_liquido == 40.00
    assert venda.tipo_desconto == "valor"
    assert venda.valor_pagamento_1 == 40.00

def test_finalizar_venda_com_desconto_percentual_calculado(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    # O front-end calcula 10% de R$ 50,00 e envia R$ 5,00
    # no campo desconto_manual.
    dados = criar_dados_venda(
        produto,
        desconto_manual=5,
        tipo_desconto="percentual",
        valor_pagamento_1=45
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303

    venda = db_session_test.query(Venda).first()

    assert venda is not None
    assert venda.total_bruto == 50.00
    assert venda.desconto == 5.00
    assert venda.total_liquido == 45.00
    assert venda.tipo_desconto == "percentual"

def test_nao_finalizar_venda_com_desconto_negativo(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(
        produto,
        desconto_manual=-5
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=desconto" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0
    assert produto.estoque_atual == 10

def test_nao_finalizar_venda_com_desconto_maior_que_subtotal(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(
        produto,
        desconto_manual=60,
        valor_pagamento_1=50
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=desconto_maior" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0
    assert produto.estoque_atual == 10

# ============================================================
# TESTES DE DADOS INVÁLIDOS NO CARRINHO
# ============================================================

def test_nao_finalizar_venda_com_carrinho_vazio(
    cliente,
    db_session_test
):
    dados = criar_dados_venda(
        criar_produto(db_session_test),
        carrinho_json="[]"
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=vazio" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0

def test_nao_finalizar_venda_com_json_invalido(
    cliente,
    db_session_test
):
    dados = criar_dados_venda(
        criar_produto(db_session_test),
        carrinho_json="{json invalido"
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=json" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0

def test_nao_finalizar_venda_com_quantidade_zero(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    dados = criar_dados_venda(
        produto,
        carrinho_json=json.dumps([
            {
                "produto_id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco,
                "quantidade": 0
            }
        ])
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=quantidade" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0
    assert produto.estoque_atual == 10

def test_nao_finalizar_venda_com_estoque_insuficiente(
    cliente,
    db_session_test
):
    produto = criar_produto(
        db_session_test,
        estoque=1
    )

    dados = criar_dados_venda(
        produto,
        carrinho_json=json.dumps([
            {
                "produto_id": produto.id,
                "nome": produto.nome,
                "preco": produto.preco,
                "quantidade": 2
            }
        ]),
        valor_pagamento_1=100
    )

    resposta = cliente.post(
        "/pdv/finalizar",
        data=dados,
        follow_redirects=False
    )

    assert resposta.status_code == 303
    assert "erro=estoque" in resposta.headers["location"]

    assert db_session_test.query(Venda).count() == 0
    assert produto.estoque_atual == 1