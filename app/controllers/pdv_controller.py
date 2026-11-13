
# ============================================================
# controllers/pdv_controller.py
# PONTO DE VENDA - NOVA ADEGA
# ============================================================

import json
from math import ceil

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.venda import Venda, ItemVenda
from app.models.produto import Produto
from app.models.cliente import Cliente
from app.auth import get_usuario_logado


router = APIRouter(prefix="/pdv", tags=["PDV"])
templates = Jinja2Templates(directory="app/templates")

DESCONTO_ASSOCIADO = 10.0
PRODUTOS_POR_PAGINA = 8


# ============================================================
# TELA DO PDV
# ============================================================

@router.get("/")
def tela_pdv(
    request: Request,
    pagina: int = 1,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    consulta_produtos = (
        db.query(Produto)
        .filter(
            Produto.ativo == True,
            Produto.estoque_atual > 0
        )
    )

    total_produtos = consulta_produtos.count()

    total_paginas = max(
        1,
        ceil(total_produtos / PRODUTOS_POR_PAGINA)
    )

    pagina = max(1, min(pagina, total_paginas))

    produtos = (
        consulta_produtos
        .order_by(Produto.nome)
        .offset((pagina - 1) * PRODUTOS_POR_PAGINA)
        .limit(PRODUTOS_POR_PAGINA)
        .all()
    )

    clientes = (
        db.query(Cliente)
        .filter(Cliente.ativo == True)
        .order_by(Cliente.nome)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "pdv/index.html",
        {
            "request": request,
            "usuario": usuario,
            "produtos": produtos,
            "clientes": clientes,
            "desconto_associado": DESCONTO_ASSOCIADO,
            "pagina": pagina,
            "total_paginas": total_paginas,
            "total_produtos": total_produtos,
            "produtos_por_pagina": PRODUTOS_POR_PAGINA,
        }
    )


# ============================================================
# FINALIZAR VENDA
# ============================================================

@router.post("/finalizar")
def finalizar_venda(
    request: Request,
    carrinho_json: str = Form(...),
    cliente_id: int = Form(0),
    observacao: str = Form(""),
    desconto_manual: float = Form(0.0),
    tipo_desconto: str = Form(""),
    forma_pagamento_1: str = Form(""),
    valor_pagamento_1: float = Form(0.0),
    forma_pagamento_2: str = Form(""),
    valor_pagamento_2: float = Form(0.0),
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    # Ler carrinho
    try:
        itens = json.loads(carrinho_json)

        if not isinstance(itens, list):
            raise ValueError("O carrinho precisa ser uma lista.")

    except (json.JSONDecodeError, ValueError, TypeError):
        return RedirectResponse(
            url="/pdv/?erro=json",
            status_code=303
        )

    if not itens:
        return RedirectResponse(
            url="/pdv/?erro=vazio",
            status_code=303
        )

    # Buscar cliente
    cliente = None

    if cliente_id:
        cliente = (
            db.query(Cliente)
            .filter(
                Cliente.id == cliente_id,
                Cliente.ativo == True
            )
            .first()
        )

        if not cliente:
            cliente_id = 0

    # Validar produtos e calcular subtotal
    total_bruto = 0.0
    itens_validados = []

    try:
        for item in itens:
            if not isinstance(item, dict):
                return RedirectResponse(
                    url="/pdv/?erro=json",
                    status_code=303
                )

            produto_id = int(item.get("produto_id"))
            quantidade = int(item.get("quantidade"))

            if quantidade <= 0:
                return RedirectResponse(
                    url="/pdv/?erro=quantidade",
                    status_code=303
                )

            produto = (
                db.query(Produto)
                .filter(
                    Produto.id == produto_id,
                    Produto.ativo == True
                )
                .first()
            )

            if not produto:
                return RedirectResponse(
                    url="/pdv/?erro=produto_inexistente",
                    status_code=303
                )

            if produto.estoque_atual < quantidade:
                return RedirectResponse(
                    url="/pdv/?erro=estoque",
                    status_code=303
                )

            preco = round(float(produto.preco), 2)
            subtotal_item = round(preco * quantidade, 2)
            total_bruto += subtotal_item

            itens_validados.append({
                "produto": produto,
                "quantidade": quantidade,
                "preco": preco,
                "produto_nome": produto.nome,
            })

    except (ValueError, TypeError, AttributeError):
        return RedirectResponse(
            url="/pdv/?erro=quantidade",
            status_code=303
        )

    total_bruto = round(total_bruto, 2)

    # Desconto de associado
    desconto_associado = 0.0

    if cliente and cliente.is_associado:
        desconto_associado = round(
            total_bruto * DESCONTO_ASSOCIADO / 100,
            2
        )

    # Validar desconto manual
    try:
        desconto_manual = round(
            float(desconto_manual or 0),
            2
        )
    except (ValueError, TypeError):
        return RedirectResponse(
            url="/pdv/?erro=desconto",
            status_code=303
        )

    if desconto_manual < 0:
        return RedirectResponse(
            url="/pdv/?erro=desconto",
            status_code=303
        )

    limite_desconto_manual = round(
        max(0.0, total_bruto - desconto_associado),
        2
    )

    if desconto_manual > limite_desconto_manual:
        return RedirectResponse(
            url="/pdv/?erro=desconto_maior",
            status_code=303
        )

    # Calcular total líquido
    desconto_total = round(
        desconto_associado + desconto_manual,
        2
    )

    total_liquido = round(
        max(0.0, total_bruto - desconto_total),
        2
    )

    # ========================================================
    # VALIDAR PAGAMENTOS
    # ========================================================

    try:
        valor_pagamento_1 = round(
            float(valor_pagamento_1 or 0), 2
        )
        valor_pagamento_2 = round(
            float(valor_pagamento_2 or 0), 2
        )
    except (ValueError, TypeError):
        return RedirectResponse(
            url="/pdv/?erro=pagamento",
            status_code=303
        )

    forma_pagamento_1 = (
        forma_pagamento_1 or ""
    ).strip().lower()

    forma_pagamento_2 = (
        forma_pagamento_2 or ""
    ).strip().lower()

    formas_permitidas = {
        "dinheiro",
        "pix",
        "cartao_credito",
        "cartao_debito",
    }

    if (
        valor_pagamento_1 < 0
        or valor_pagamento_2 < 0
    ):
        return RedirectResponse(
            url="/pdv/?erro=pagamento",
            status_code=303
        )

    if (
        valor_pagamento_1 <= 0
        or forma_pagamento_1 not in formas_permitidas
    ):
        return RedirectResponse(
            url="/pdv/?erro=pagamento_1",
            status_code=303
        )

    if valor_pagamento_2 > 0:
        if forma_pagamento_2 not in formas_permitidas:
            return RedirectResponse(
                url="/pdv/?erro=pagamento_2",
                status_code=303
            )

        if forma_pagamento_1 == forma_pagamento_2:
            return RedirectResponse(
                url="/pdv/?erro=pagamento_2",
                status_code=303
            )
    else:
        forma_pagamento_2 = None
        valor_pagamento_2 = 0.0

    total_pago = round(
        valor_pagamento_1 + valor_pagamento_2,
        2
    )

    # Diagnóstico no terminal do VS Code
    print("===== DIAGNÓSTICO DE PAGAMENTO =====")
    print(f"Total bruto:       R$ {total_bruto:.2f}")
    print(f"Desconto:          R$ {desconto_total:.2f}")
    print(f"Total líquido:     R$ {total_liquido:.2f}")
    print(f"Forma 1:           {forma_pagamento_1}")
    print(f"Valor 1:           R$ {valor_pagamento_1:.2f}")
    print(f"Forma 2:           {forma_pagamento_2}")
    print(f"Valor 2:           R$ {valor_pagamento_2:.2f}")
    print(f"Total recebido:    R$ {total_pago:.2f}")
    print("====================================")

    # Para pagamento dividido, os valores devem fechar o total.
    if abs(total_pago - total_liquido) > 0.001:
        return RedirectResponse(
            url="/pdv/?erro=valor_pagamento",
            status_code=303
        )

    # Identificar usuário logado
    if isinstance(usuario, dict):
        usuario_id = usuario.get("id")
    else:
        usuario_id = usuario.id

    # Criar venda
    venda = Venda(
        cliente_id=cliente_id or None,
        usuario_id=usuario_id,
        total_bruto=total_bruto,
        total_liquido=total_liquido,
        desconto=desconto_total,
        tipo_desconto=tipo_desconto or None,
        forma_pagamento_1=forma_pagamento_1,
        valor_pagamento_1=valor_pagamento_1,
        forma_pagamento_2=forma_pagamento_2,
        valor_pagamento_2=valor_pagamento_2,
        observacao=observacao.strip() or None
    )

    try:
        db.add(venda)
        db.flush()

        # Criar itens e baixar estoque
        for item in itens_validados:
            item_venda = ItemVenda(
                venda_id=venda.id,
                produto_id=item["produto"].id,
                produto_nome=item["produto_nome"],
                quantidade=item["quantidade"],
                preco_unitario=item["preco"]
            )

            db.add(item_venda)

            item["produto"].estoque_atual -= item["quantidade"]

        db.commit()
        db.refresh(venda)

    except Exception as erro:
        db.rollback()
        print("ERRO AO FINALIZAR VENDA:")
        print(erro)

        return RedirectResponse(
            url="/pdv/?erro=salvar",
            status_code=303
        )

    # Abrir comprovante
    return RedirectResponse(
        url=f"/pdv/venda/{venda.id}?sucesso=ok",
        status_code=303
    )


# ============================================================
# DETALHE DA VENDA / COMPROVANTE
# ============================================================

@router.get("/venda/{venda_id}")
def detalhe_venda(
    venda_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    venda = (
        db.query(Venda)
        .filter(Venda.id == venda_id)
        .first()
    )

    if not venda:
        return RedirectResponse(
            url="/pdv/",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "pdv/comprovante.html",
        {
            "request": request,
            "usuario": usuario,
            "venda": venda
        }
    )


# ============================================================
# HISTÓRICO DE VENDAS
# ============================================================

@router.get("/historico")
def historico_vendas(
    request: Request,
    pagina: int = 1,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    por_pagina = 10
    pagina = max(1, pagina)

    total_vendas = db.query(Venda).count()

    total_paginas = max(
        1,
        ceil(total_vendas / por_pagina)
    )

    pagina = min(pagina, total_paginas)

    vendas = (
        db.query(Venda)
        .order_by(Venda.criado_em.desc())
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "pdv/historico.html",
        {
            "request": request,
            "usuario": usuario,
            "vendas": vendas,
            "pagina": pagina,
            "total_paginas": total_paginas,
            "total_vendas": total_vendas
        }
    )
