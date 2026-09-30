from app.models.usuarios import Usuario
from app.models.categoria import Categoria
from app.models.produto import Produto
from app.models.cliente import Cliente
from app.models.movimentacao import Movimentacao, TipoMovimentacao
from app.models.venda import Venda, ItemVenda


# ============================================================
# USUÁRIO
# ============================================================

def test_criar_usuario():
    usuario = Usuario(
        nome="João Teste",
        email="joao@teste.com",
        senha_hash="senha_hash_teste",
        role="admin",
        ativo=True
    )

    assert usuario.nome == "João Teste"
    assert usuario.email == "joao@teste.com"
    assert usuario.senha_hash == "senha_hash_teste"
    assert usuario.role == "admin"
    assert usuario.ativo is True


def test_usuario_inativo():
    usuario = Usuario(
        nome="Usuário Inativo",
        email="inativo@teste.com",
        senha_hash="senha_hash",
        role="operador",
        ativo=False
    )

    assert usuario.ativo is False


def test_usuario_operador():
    usuario = Usuario(
        nome="Operador",
        email="operador@teste.com",
        senha_hash="senha_hash",
        role="operador",
        ativo=True
    )

    assert usuario.role == "operador"


# ============================================================
# CATEGORIA
# ============================================================

def test_criar_categoria():
    categoria = Categoria(
        nome="Vinhos"
    )

    assert categoria.nome == "Vinhos"
    assert categoria.ativo is None or categoria.ativo is True


def test_categoria_nome():
    categoria = Categoria(
        nome="Cervejas"
    )

    assert categoria.nome == "Cervejas"


# ============================================================
# PRODUTO
# ============================================================

def test_criar_produto():
    produto = Produto(
        nome="Vinho Tinto",
        preco=50.00,
        estoque_atual=10
    )

    assert produto.nome == "Vinho Tinto"
    assert produto.preco == 50.00
    assert produto.estoque_atual == 10


def test_produto_com_estoque_zero():
    produto = Produto(
        nome="Produto Sem Estoque",
        preco=30.00,
        estoque_atual=0
    )

    assert produto.estoque_atual == 0


def test_produto_com_preco_decimal():
    produto = Produto(
        nome="Vinho Especial",
        preco=99.90,
        estoque_atual=5
    )

    assert produto.preco == 99.90


def test_produto_inativo():
    produto = Produto(
        nome="Produto Inativo",
        preco=20.00,
        estoque_atual=5,
        ativo=False
    )

    assert produto.ativo is False


# ============================================================
# PROPRIEDADES DO PRODUTO
# ============================================================

def test_produto_imagem_url_com_imagem():
    produto = Produto(
        nome="Vinho",
        preco=50.00,
        estoque_atual=5,
        imagem_path="uploads/vinho.jpg"
    )

    assert produto.imagem_url == "/static/uploads/vinho.jpg"


def test_produto_imagem_url_sem_imagem():
    produto = Produto(
        nome="Vinho",
        preco=50.00,
        estoque_atual=5
    )

    assert produto.imagem_url == "/static/img/produto-placeholder.png"


def test_produto_estoque_baixo():
    produto = Produto(
        nome="Vinho",
        preco=50.00,
        estoque_atual=10
    )

    assert produto.estoque_baixo is True


def test_produto_estoque_acima_do_limite():
    produto = Produto(
        nome="Vinho",
        preco=50.00,
        estoque_atual=11
    )

    assert produto.estoque_baixo is False


# ============================================================
# CLIENTE
# ============================================================

def test_criar_cliente():
    cliente = Cliente(
        nome="Maria Teste",
        telefone="11999999999"
    )

    assert cliente.nome == "Maria Teste"
    assert cliente.telefone == "11999999999"


def test_cliente_associado():
    cliente = Cliente(
        nome="Cliente Associado",
        telefone="11988888888",
        is_associado=True
    )

    assert cliente.is_associado is True


def test_cliente_nao_associado():
    cliente = Cliente(
        nome="Cliente Normal",
        telefone="11977777777",
        is_associado=False
    )

    assert cliente.is_associado is False


def test_cliente_inativo():
    cliente = Cliente(
        nome="Cliente Inativo",
        telefone="11966666666",
        ativo=False
    )

    assert cliente.ativo is False


# ============================================================
# MOVIMENTAÇÃO
# ============================================================

def test_criar_movimentacao_entrada():
    movimentacao = Movimentacao(
        tipo=TipoMovimentacao.ENTRADA,
        quantidade=10,
        preco_unitario=20.00,
        produto_id=1
    )

    assert movimentacao.tipo == TipoMovimentacao.ENTRADA
    assert movimentacao.quantidade == 10
    assert movimentacao.preco_unitario == 20.00


def test_criar_movimentacao_saida():
    movimentacao = Movimentacao(
        tipo=TipoMovimentacao.SAIDA,
        quantidade=3,
        preco_unitario=25.00,
        produto_id=1
    )

    assert movimentacao.tipo == TipoMovimentacao.SAIDA
    assert movimentacao.quantidade == 3


def test_valor_total_movimentacao():
    movimentacao = Movimentacao(
        tipo=TipoMovimentacao.ENTRADA,
        quantidade=5,
        preco_unitario=20.00,
        produto_id=1
    )

    assert movimentacao.valor_total == 100.00


# ============================================================
# VENDA
# ============================================================

def test_criar_venda():
    venda = Venda(
        total_bruto=100.00,
        total_liquido=100.00
    )

    assert venda.total_bruto == 100.00
    assert venda.total_liquido == 100.00


def test_venda_com_desconto():
    venda = Venda(
        total_bruto=100.00,
        total_liquido=90.00
    )

    assert venda.total_bruto == 100.00
    assert venda.total_liquido == 90.00


# ============================================================
# ITEM DA VENDA
# ============================================================

def test_criar_item_venda():
    item = ItemVenda(
        produto_nome="Vinho Tinto",
        quantidade=2,
        preco_unitario=50.00,
        venda_id=1
    )

    assert item.produto_nome == "Vinho Tinto"
    assert item.quantidade == 2
    assert item.preco_unitario == 50.00


def test_subtotal_item_venda():
    item = ItemVenda(
        produto_nome="Vinho Tinto",
        quantidade=3,
        preco_unitario=25.00,
        venda_id=1
    )

    assert item.subtotal == 75.00


def test_repr_cliente():
    cliente = Cliente(
        nome="Maria",
        is_associado=True
    )

    cliente.id = 1

    resultado = repr(cliente)

    assert "Cliente" in resultado
    assert "Maria" in resultado
    assert "associado=True" in resultado


def test_repr_venda():
    venda = Venda(
        total_liquido=150.00
    )

    venda.id = 1

    resultado = repr(venda)

    assert "Venda" in resultado
    assert "150.0" in resultado


def test_repr_item_venda():
    item = ItemVenda(
        produto_nome="Vinho",
        quantidade=2,
        preco_unitario=30.00,
        venda_id=1
    )

    item.id = 1

    resultado = repr(item)

    assert "ItemVenda" in resultado
    assert "Vinho" in resultado
    assert "quantidade=2" in resultado