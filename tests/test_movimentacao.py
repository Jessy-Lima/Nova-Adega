from app.models.movimentacao import Movimentacao, TipoMovimentacao
from app.models.produto import Produto


def criar_produto(db_session_test, nome="Vinho Teste"):
    produto = Produto(
        nome=nome,
        preco=50.00,
        estoque_atual=10,
        ativo=True
    )

    db_session_test.add(produto)
    db_session_test.commit()
    db_session_test.refresh(produto)

    return produto


def test_criar_movimentacao_entrada(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    movimentacao = Movimentacao(
        produto_id=produto.id,
        tipo=TipoMovimentacao.ENTRADA,
        quantidade=5
    )

    db_session_test.add(movimentacao)
    db_session_test.commit()
    db_session_test.refresh(movimentacao)

    assert movimentacao.id is not None
    assert movimentacao.produto_id == produto.id
    assert movimentacao.quantidade == 5
    assert movimentacao.tipo == TipoMovimentacao.ENTRADA


def test_criar_movimentacao_saida(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    movimentacao = Movimentacao(
        produto_id=produto.id,
        tipo=TipoMovimentacao.SAIDA,
        quantidade=3
    )

    db_session_test.add(movimentacao)
    db_session_test.commit()
    db_session_test.refresh(movimentacao)

    assert movimentacao.id is not None
    assert movimentacao.produto_id == produto.id
    assert movimentacao.quantidade == 3
    assert movimentacao.tipo == TipoMovimentacao.SAIDA


def test_movimentacao_possui_produto(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    movimentacao = Movimentacao(
        produto_id=produto.id,
        tipo=TipoMovimentacao.ENTRADA,
        quantidade=10
    )

    db_session_test.add(movimentacao)
    db_session_test.commit()
    db_session_test.refresh(movimentacao)

    assert movimentacao.produto is not None
    assert movimentacao.produto.id == produto.id
    assert movimentacao.produto.nome == "Vinho Teste"


def test_movimentacao_quantidade_positiva(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    movimentacao = Movimentacao(
        produto_id=produto.id,
        tipo=TipoMovimentacao.ENTRADA,
        quantidade=1
    )

    db_session_test.add(movimentacao)
    db_session_test.commit()

    assert movimentacao.quantidade > 0


def test_movimentacao_pode_ser_consultada(
    cliente,
    db_session_test
):
    produto = criar_produto(db_session_test)

    movimentacao = Movimentacao(
        produto_id=produto.id,
        tipo=TipoMovimentacao.ENTRADA,
        quantidade=7
    )

    db_session_test.add(movimentacao)
    db_session_test.commit()

    resultado = (
        db_session_test
        .query(Movimentacao)
        .filter_by(produto_id=produto.id)
        .first()
    )

    assert resultado is not None
    assert resultado.quantidade == 7


def test_movimentacoes_de_produtos_diferentes(
    cliente,
    db_session_test
):
    produto1 = criar_produto(
        db_session_test,
        "Vinho Tinto"
    )

    produto2 = criar_produto(
        db_session_test,
        "Vinho Branco"
    )

    movimentacao1 = Movimentacao(
        produto_id=produto1.id,
        tipo=TipoMovimentacao.ENTRADA,
        quantidade=5
    )

    movimentacao2 = Movimentacao(
        produto_id=produto2.id,
        tipo=TipoMovimentacao.SAIDA,
        quantidade=2
    )

    db_session_test.add_all([
        movimentacao1,
        movimentacao2
    ])
    db_session_test.commit()

    resultados1 = (
        db_session_test
        .query(Movimentacao)
        .filter_by(produto_id=produto1.id)
        .all()
    )

    resultados2 = (
        db_session_test
        .query(Movimentacao)
        .filter_by(produto_id=produto2.id)
        .all()
    )

    assert len(resultados1) == 1
    assert len(resultados2) == 1
    assert resultados1[0].tipo == TipoMovimentacao.ENTRADA
    assert resultados2[0].tipo == TipoMovimentacao.SAIDA