from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)

    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True
    )

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True
    )

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

    # ============================================================
    # DESCONTO
    # ============================================================

    desconto = Column(
        Float,
        nullable=False,
        default=0.0
    )

    tipo_desconto = Column(
        String(20),
        nullable=True
    )

    # ============================================================
    # PRIMEIRO PAGAMENTO
    # ============================================================

    forma_pagamento_1 = Column(
        String(50),
        nullable=True
    )

    valor_pagamento_1 = Column(
        Float,
        nullable=False,
        default=0.0
    )

    # ============================================================
    # SEGUNDO PAGAMENTO
    # ============================================================

    forma_pagamento_2 = Column(
        String(50),
        nullable=True
    )

    valor_pagamento_2 = Column(
        Float,
        nullable=False,
        default=0.0
    )

    # ============================================================
    # OBSERVAÇÃO E DATA
    # ============================================================

    observacao = Column(
        String(255),
        nullable=True
    )

    criado_em = Column(
        DateTime,
        server_default=func.now()
    )

    # ============================================================
    # RELACIONAMENTOS
    # ============================================================

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

    def __repr__(self):
        return f"<Venda id={self.id} total={self.total_liquido}>"


class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    venda_id = Column(
        Integer,
        ForeignKey("vendas.id", ondelete="CASCADE"),
        nullable=False
    )

    produto_id = Column(
        Integer,
        ForeignKey("produtos.id", ondelete="SET NULL"),
        nullable=True
    )

    produto_nome = Column(
        String(150),
        nullable=False
    )

    quantidade = Column(
        Integer,
        nullable=False
    )

    preco_unitario = Column(
        Float,
        nullable=False
    )

    venda = relationship(
        "Venda",
        back_populates="itens"
    )

    produto = relationship(
        "Produto",
        backref="itens_venda"
    )

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario

    def __repr__(self):
        return (
            f"<ItemVenda id={self.id} "
            f"produto={self.produto_nome} "
            f"quantidade={self.quantidade}>"
        )