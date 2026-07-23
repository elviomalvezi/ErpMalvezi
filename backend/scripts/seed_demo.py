"""Popula o banco com dados de demonstração do ErpMalvezi.

Cria um cenário multi-empresa realista para apresentações:
- Usuário demo (admin) + vínculo de todos os admins existentes às empresas.
- 3 empresas: PJ comércio (001), PJ serviços/locação (002) e PF (003).
- Plano de contas padrão, contas bancárias, contatos.
- ~6 meses de lançamentos (pagos, pendentes e vencidos) por empresa.

Idempotente: se a empresa de código 001 já existir, nada é alterado.

Uso:
    uv run python scripts/seed_demo.py
"""

import asyncio
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importa modelos referenciados por FKs de Lancamento para registrar no metadata.
import app.modules.fatura.models  # noqa: E402, F401
import app.modules.patrimonio.models  # noqa: E402, F401
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.modules.categoria.models import Categoria
from app.modules.categoria.repository import CategoriaRepository
from app.modules.categoria.service import CategoriaService
from app.modules.conta_bancaria.models import BandeiraCartao, ContaBancaria, TipoConta
from app.modules.contato.models import Contato, TipoContato
from app.modules.empresa.models import Empresa, TipoPessoa, UsuarioEmpresa
from app.modules.empresa.repository import EmpresaRepository
from app.modules.empresa.schemas import EmpresaCreate
from app.modules.empresa.service import EmpresaService
from app.modules.lancamento.models import Lancamento, StatusLancamento, TipoLancamento
from app.modules.usuario.models import Usuario

DEMO_EMAIL = "demo@erpmalvezi.local"
DEMO_SENHA = "Demo@123"

# Documentos válidos (dígitos verificadores corretos), de uso ilustrativo.
CNPJ_COMERCIO = "11444777000161"
CNPJ_SERVICOS = "11222333000181"
CPF_PESSOA = "52998224725"

HOJE = date.today()


def _mes(offset: int, dia: int = 10) -> date:
    """Data no mês `offset` relativo ao atual (offset<0 = passado)."""
    ano = HOJE.year + (HOJE.month - 1 + offset) // 12
    mes = (HOJE.month - 1 + offset) % 12 + 1
    return date(ano, mes, min(dia, 28))


async def _get_or_create_demo_user(db: AsyncSession) -> Usuario:
    usuario = await db.scalar(select(Usuario).where(Usuario.email == DEMO_EMAIL))
    if usuario:
        return usuario
    usuario = Usuario(
        email=DEMO_EMAIL,
        nome="Usuário Demonstração",
        senha_hash=hash_password(DEMO_SENHA),
        ativo=True,
        admin=True,
        email_verificado=True,
    )
    db.add(usuario)
    await db.flush()
    print(f"[ok] Usuário demo criado: {DEMO_EMAIL} / {DEMO_SENHA}")
    return usuario


async def _criar_empresas(db: AsyncSession, demo: Usuario) -> list[Empresa]:
    svc = EmpresaService(db)
    empresas = []
    for payload in (
        EmpresaCreate(
            tipo=TipoPessoa.PJ,
            codigo="001",
            documento=CNPJ_COMERCIO,
            nome_principal="Aurora Comércio de Materiais Ltda",
            nome_alternativo="Aurora Materiais",
            regime_tributario="Simples",
            cidade="Campinas",
            uf="SP",
            cor_primaria="#14675A",
        ),
        EmpresaCreate(
            tipo=TipoPessoa.PJ,
            codigo="002",
            documento=CNPJ_SERVICOS,
            nome_principal="TecnoServ Locação e Manutenção Ltda",
            nome_alternativo="TecnoServ",
            regime_tributario="Simples",
            cidade="Jundiaí",
            uf="SP",
            cor_primaria="#33506B",
        ),
        EmpresaCreate(
            tipo=TipoPessoa.PF,
            codigo="003",
            documento=CPF_PESSOA,
            nome_principal="Patrimônio Pessoal — Pessoa Física",
            nome_alternativo="PF",
            cidade="Cabreúva",
            uf="SP",
            cor_primaria="#8A5A12",
        ),
    ):
        empresas.append(await svc.criar(payload, demo.id))
    print(f"[ok] {len(empresas)} empresas criadas (001, 002, 003)")
    return empresas


async def _vincular_admins(db: AsyncSession, empresas: list[Empresa], demo: Usuario) -> None:
    """Todos os admins existentes enxergam as empresas de demonstração."""
    admins = (
        (await db.execute(select(Usuario).where(Usuario.admin.is_(True)))).scalars().all()
    )
    for admin in admins:
        if admin.id == demo.id:
            continue
        for empresa in empresas:
            existe = await db.scalar(
                select(UsuarioEmpresa).where(
                    UsuarioEmpresa.usuario_id == admin.id,
                    UsuarioEmpresa.empresa_id == empresa.id,
                )
            )
            if not existe:
                db.add(UsuarioEmpresa(usuario_id=admin.id, empresa_id=empresa.id))
    await db.flush()


async def _categorias(db: AsyncSession, demo: Usuario) -> dict[str, Categoria]:
    svc = CategoriaService(CategoriaRepository(db))
    total = await svc.inicializar_plano_padrao(demo.id)
    print(f"[ok] Plano de contas padrão: {total} categorias")
    result = await db.execute(select(Categoria).where(Categoria.usuario_id == demo.id))
    return {c.nome: c for c in result.scalars().all()}


def _conta(
    empresa: Empresa, demo: Usuario, nome: str, tipo: TipoConta, saldo: str, **kw
) -> ContaBancaria:
    return ContaBancaria(
        empresa_id=empresa.id,
        usuario_id=demo.id,
        nome=nome,
        tipo=tipo,
        saldo_inicial=Decimal(saldo),
        data_saldo_inicial=_mes(-6, 1),
        **kw,
    )


async def _contas_bancarias(
    db: AsyncSession, empresas: list[Empresa], demo: Usuario
) -> dict[str, ContaBancaria]:
    e1, e2, e3 = empresas
    contas = {
        "001-corrente": _conta(
            e1, demo, "Banco Cora — Corrente", TipoConta.CORRENTE,
            "45000.00", banco="403 — Cora", agencia="0001", numero_conta="123456", digito="7",
        ),
        "001-caixinha": _conta(e1, demo, "Caixinha da Loja", TipoConta.CAIXINHA, "1200.00"),
        "001-cartao": ContaBancaria(
            empresa_id=e1.id, usuario_id=demo.id, nome="Cartão Corporativo",
            tipo=TipoConta.CARTAO_CREDITO, saldo_inicial=Decimal("0"),
            bandeira=BandeiraCartao.VISA, limite=Decimal("15000.00"), dia_fechamento=3, dia_vencimento=10,
        ),
        "002-corrente": _conta(
            e2, demo, "Banco Cora — Corrente", TipoConta.CORRENTE,
            "28000.00", banco="403 — Cora", agencia="0001", numero_conta="654321", digito="0",
        ),
        "003-corrente": _conta(
            e3, demo, "Conta Pessoal", TipoConta.CORRENTE,
            "12000.00", banco="001 — Banco do Brasil", agencia="1234", numero_conta="99887", digito="6",
        ),
    }
    db.add_all(contas.values())
    await db.flush()
    print(f"[ok] {len(contas)} contas bancárias")
    return contas


async def _contatos(
    db: AsyncSession, empresas: list[Empresa], demo: Usuario
) -> dict[str, Contato]:
    e1, e2, e3 = empresas
    def c(empresa, nome, doc, tipo=TipoContato.PJ, cliente=True, fornecedor=False):
        return Contato(
            usuario_id=demo.id, empresa_id=empresa.id, escopo="especifico",
            tipo=tipo, documento=doc, nome_principal=nome,
            eh_cliente=cliente, eh_fornecedor=fornecedor, cidade="São Paulo", uf="SP",
        )
    contatos = {
        "horizonte": c(e1, "Construtora Horizonte Ltda", "19131243000197"),
        "bompreco": c(e1, "Mercado Bom Preço", "45723174000110"),
        "alfa": c(e1, "Distribuidora Alfa", "10880770000101", cliente=False, fornecedor=True),
        "energia1": c(e1, "Companhia de Energia", "33050196000188", cliente=False, fornecedor=True),
        "geomap": c(e2, "GeoMap Topografia", "34028316000103"),
        "sitio": c(e2, "Sítio Boa Vista", "39346861000162"),
        "pecas": c(e2, "Casa das Peças", "60701190000104", cliente=False, fornecedor=True),
        "inquilino": c(e3, "Marcos Andrade (inquilino)", "16899535009", tipo=TipoContato.PF),
    }
    db.add_all(contatos.values())
    await db.flush()
    print(f"[ok] {len(contatos)} contatos")
    return contatos


def _lcto(
    empresa: Empresa,
    demo: Usuario,
    tipo: TipoLancamento,
    descricao: str,
    valor: str,
    vencimento: date,
    categoria: Categoria | None,
    contato: Contato | None = None,
    conta: ContaBancaria | None = None,
    pago: bool = False,
) -> Lancamento:
    v = Decimal(valor)
    return Lancamento(
        empresa_id=empresa.id,
        usuario_id=demo.id,
        tipo=tipo,
        descricao=descricao,
        valor=v,
        valor_pago=v if pago else Decimal("0"),
        data_competencia=vencimento.replace(day=1),
        data_vencimento=vencimento,
        data_pagamento=vencimento if pago else None,
        status=StatusLancamento.PAGO if pago else StatusLancamento.PENDENTE,
        categoria_id=categoria.id if categoria else None,
        contato_id=contato.id if contato else None,
        conta_bancaria_id=conta.id if conta else None,
    )


async def _lancamentos(
    db: AsyncSession,
    empresas: list[Empresa],
    demo: Usuario,
    cats: dict[str, Categoria],
    contas: dict[str, ContaBancaria],
    ctts: dict[str, Contato],
) -> int:
    e1, e2, e3 = empresas
    R, D = TipoLancamento.RECEITA, TipoLancamento.DESPESA
    lctos: list[Lancamento] = []

    # ── 001 Aurora Comércio: 6 meses de vendas e despesas fixas ─────────────
    for m in range(-6, 0):
        lctos += [
            _lcto(e1, demo, R, "Vendas balcão", f"{18000 + 1200 * (m % 3)}.00",
                  _mes(m, 5), cats.get("Produtos"), ctts["bompreco"], contas["001-corrente"], pago=True),
            _lcto(e1, demo, R, "Fornecimento obra Horizonte", "9500.00",
                  _mes(m, 15), cats.get("Produtos"), ctts["horizonte"], contas["001-corrente"], pago=True),
            _lcto(e1, demo, D, "Compra de mercadorias", "11200.00",
                  _mes(m, 8), cats.get("Despesas Diversas"), ctts["alfa"], contas["001-corrente"], pago=True),
            _lcto(e1, demo, D, "Aluguel da loja", "4200.00",
                  _mes(m, 5), cats.get("Aluguel"), None, contas["001-corrente"], pago=True),
            _lcto(e1, demo, D, "Energia elétrica", "870.00",
                  _mes(m, 12), cats.get("Água e Energia"), ctts["energia1"], contas["001-corrente"], pago=True),
            _lcto(e1, demo, D, "Folha de pagamento", "7600.00",
                  _mes(m, 5), cats.get("Salários e Pró-labore"), None, contas["001-corrente"], pago=True),
        ]
    # Pendentes e inadimplência
    lctos += [
        _lcto(e1, demo, R, "Fornecimento obra Horizonte", "9500.00",
              _mes(1, 15), cats.get("Produtos"), ctts["horizonte"]),
        _lcto(e1, demo, R, "Venda a prazo — Mercado Bom Preço", "4300.00",
              HOJE - timedelta(days=18), cats.get("Produtos"), ctts["bompreco"]),  # vencido
        _lcto(e1, demo, D, "Aluguel da loja", "4200.00", _mes(1, 5), cats.get("Aluguel")),
        _lcto(e1, demo, D, "Compra de mercadorias", "12800.00",
              _mes(0, 28), cats.get("Despesas Diversas"), ctts["alfa"]),
    ]

    # ── 002 TecnoServ: locação recorrente + OS ──────────────────────────────
    for m in range(-6, 0):
        lctos += [
            _lcto(e2, demo, R, "Locação mensal — Estação Total (GeoMap)", "3800.00",
                  _mes(m, 10), cats.get("Serviços"), ctts["geomap"], contas["002-corrente"], pago=True),
            _lcto(e2, demo, R, "Manutenção de equipamentos", f"{2200 + 300 * (m % 2)}.00",
                  _mes(m, 20), cats.get("Serviços"), ctts["sitio"], contas["002-corrente"], pago=True),
            _lcto(e2, demo, D, "Peças de reposição", "950.00",
                  _mes(m, 14), cats.get("Despesas Diversas"), ctts["pecas"], contas["002-corrente"], pago=True),
            _lcto(e2, demo, D, "Pró-labore", "5000.00",
                  _mes(m, 5), cats.get("Salários e Pró-labore"), None, contas["002-corrente"], pago=True),
        ]
    lctos += [
        _lcto(e2, demo, R, "Locação mensal — Estação Total (GeoMap)", "3800.00",
              _mes(1, 10), cats.get("Serviços"), ctts["geomap"]),
        _lcto(e2, demo, R, "OS 0042 — Reparo de nível a laser", "1450.00",
              HOJE - timedelta(days=9), cats.get("Serviços"), ctts["sitio"]),  # vencido
    ]

    # ── 003 PF: aluguel recebido + despesas pessoais ────────────────────────
    for m in range(-6, 0):
        lctos += [
            _lcto(e3, demo, R, "Aluguel do imóvel — Rua das Palmeiras", "2600.00",
                  _mes(m, 10), cats.get("Receitas Diversas"), ctts["inquilino"], contas["003-corrente"], pago=True),
            _lcto(e3, demo, D, "IPTU parcelado", "310.00",
                  _mes(m, 15), cats.get("Tributos Municipais"), None, contas["003-corrente"], pago=True),
        ]
    lctos.append(
        _lcto(e3, demo, R, "Aluguel do imóvel — Rua das Palmeiras", "2600.00",
              _mes(1, 10), cats.get("Receitas Diversas"), ctts["inquilino"])
    )

    db.add_all(lctos)
    await db.flush()
    print(f"[ok] {len(lctos)} lançamentos (~6 meses de movimento)")
    return len(lctos)


async def main() -> None:
    async with AsyncSessionLocal() as db:
        repo = EmpresaRepository(db)
        if await repo.get_by_codigo("001"):
            print("[aviso] Seed já aplicado (empresa 001 existe). Nada foi alterado.")
            return

        demo = await _get_or_create_demo_user(db)
        empresas = await _criar_empresas(db, demo)
        await _vincular_admins(db, empresas, demo)
        cats = await _categorias(db, demo)
        contas = await _contas_bancarias(db, empresas, demo)
        ctts = await _contatos(db, empresas, demo)
        await _lancamentos(db, empresas, demo, cats, contas, ctts)

        await db.commit()
        print("\n[concluído] Ambiente de demonstração pronto.")
        print(f"  Login demo: {DEMO_EMAIL} / {DEMO_SENHA}")
        print("  Empresas: 001 Aurora (comércio) · 002 TecnoServ (serviços) · 003 PF")


if __name__ == "__main__":
    asyncio.run(main())
