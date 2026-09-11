from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ============================================================
# VENDA
# ============================================================

class Venda(Base):

    __tablename__ = "vendas"

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # CLIENTE
    # --------------------------------------------------------
    # Pode ficar NULL quando a venda não tiver cliente.

    cliente_id = Column(
        Integer,
        ForeignKey(
            "clientes.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # --------------------------------------------------------
    # USUÁRIO
    # --------------------------------------------------------

    usuario_id = Column(
        Integer,
        ForeignKey(
            "usuarios.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # --------------------------------------------------------
    # TOTAL DA VENDA
    # --------------------------------------------------------

    total_bruto = Column(
        Float,
        nullable=False,
        default=0.0
    )

    total_liquido = Column(
        Float,
        nullable=False,
        default=0.0
    )

    # --------------------------------------------------------
    # OBSERVAÇÃO
    # --------------------------------------------------------

    observacao = Column(
        String(255),
        nullable=True
    )

    # --------------------------------------------------------
    # DATA DA VENDA
    # --------------------------------------------------------

    criado_em = Column(
        DateTime,
        server_default=func.now()
    )

    # ========================================================
    # RELACIONAMENTOS
    # ========================================================

    cliente = relationship(
        "Cliente",
        back_populates="vendas"
    )

    usuario = relationship(
        "Usuario",
        backref="vendas"
    )

    itens = relationship(
        "ItemVenda",
        back_populates="venda",
        cascade="all, delete-orphan"
    )

    # ========================================================
    # REPRESENTAÇÃO
    # ========================================================

    def __repr__(self):

        return (
            f"<Venda "
            f"id={self.id} "
            f"total={self.total_liquido}>"
        )


# ============================================================
# ITEM DA VENDA
# ============================================================

class ItemVenda(Base):

    __tablename__ = "itens_venda"

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # VENDA
    # --------------------------------------------------------

    venda_id = Column(
        Integer,
        ForeignKey(
            "vendas.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # --------------------------------------------------------
    # PRODUTO
    # --------------------------------------------------------

    produto_id = Column(
        Integer,
        ForeignKey(
            "produtos.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # --------------------------------------------------------
    # NOME DO PRODUTO
    # --------------------------------------------------------
    # Guardamos o nome para preservar o histórico da venda.

    produto_nome = Column(
        String(150),
        nullable=False
    )

    # --------------------------------------------------------
    # QUANTIDADE
    # --------------------------------------------------------

    quantidade = Column(
        Integer,
        nullable=False
    )

    # --------------------------------------------------------
    # PREÇO UNITÁRIO
    # --------------------------------------------------------

    preco_unitario = Column(
        Float,
        nullable=False
    )

    # ========================================================
    # RELACIONAMENTOS
    # ========================================================

    venda = relationship(
        "Venda",
        back_populates="itens"
    )

    produto = relationship(
        "Produto",
        backref="itens_venda"
    )

    # ========================================================
    # SUBTOTAL
    # ========================================================

    @property
    def subtotal(self):

        return (
            self.quantidade *
            self.preco_unitario
        )

    # ========================================================
    # REPRESENTAÇÃO
    # ========================================================

    def __repr__(self):

        return (
            f"<ItemVenda "
            f"id={self.id} "
            f"produto={self.produto_nome} "
            f"quantidade={self.quantidade}>"
        )