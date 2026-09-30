from app.models.produto import Produto
from app.models.categoria import Categoria
from app.models.cliente import Cliente
from app.models.usuarios import Usuario
from app.auth import hash_senha


def test_produto_com_preco_zero(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Produto Gratis",
        preco=0,
        estoque_atual=10,
        ativo=True
    )

    db_session_test.add(produto)
    db_session_test.commit()

    assert produto.id is not None
    assert produto.preco == 0


def test_produto_com_estoque_negativo(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Produto Estoque Negativo",
        preco=50,
        estoque_atual=-1,
        ativo=True
    )

    db_session_test.add(produto)
    db_session_test.commit()

    assert produto.id is not None
    assert produto.estoque_atual == -1


def test_categoria_nome_com_espacos(
    cliente,
    db_session_test
):
    categoria = Categoria(
        nome="  Vinhos  "
    )

    db_session_test.add(categoria)
    db_session_test.commit()

    assert categoria.id is not None


def test_cliente_sem_telefone(
    cliente,
    db_session_test
):
    cliente_teste = Cliente(
        nome="Cliente Sem Telefone"
    )

    db_session_test.add(cliente_teste)
    db_session_test.commit()

    assert cliente_teste.id is not None


def test_usuario_operador(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Operador Teste",
        email="operador_edge@test.com",
        senha_hash=hash_senha("123456"),
        role="operador",
        ativo=True
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    assert usuario.id is not None
    assert usuario.role == "operador"
    assert usuario.ativo is True


def test_usuario_inativo(
    cliente,
    db_session_test
):
    usuario = Usuario(
        nome="Usuario Inativo",
        email="inativo_edge@test.com",
        senha_hash=hash_senha("123456"),
        role="operador",
        ativo=False
    )

    db_session_test.add(usuario)
    db_session_test.commit()

    assert usuario.id is not None
    assert usuario.ativo is False


def test_produto_inativo(
    cliente,
    db_session_test
):
    produto = Produto(
        nome="Produto Inativo",
        preco=40,
        estoque_atual=5,
        ativo=False
    )

    db_session_test.add(produto)
    db_session_test.commit()

    assert produto.id is not None
    assert produto.ativo is False


def test_buscar_produto_inexistente(
    cliente,
    db_session_test
):
    produto = (
        db_session_test
        .query(Produto)
        .filter_by(id=999999)
        .first()
    )

    assert produto is None