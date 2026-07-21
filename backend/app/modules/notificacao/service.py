import uuid
from datetime import date, timedelta
from decimal import Decimal

import structlog
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.email import smtp_sender
from app.modules.certificado.models import Certificado
from app.modules.empresa.models import Empresa, UsuarioEmpresa
from app.modules.lancamento.models import Lancamento, StatusLancamento
from app.modules.usuario.models import Usuario

logger = structlog.get_logger()


class NotificacaoService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def enviar_vencimentos(self) -> int:
        """Envia e-mails de alerta de vencimentos para todos os usuários ativos.
        Retorna o número de e-mails enviados."""
        hoje = date.today()
        prazo = hoje + timedelta(days=3)
        enviados = 0

        usuarios = await self._listar_usuarios_ativos()
        for usuario in usuarios:
            if not usuario.email:
                continue
            vencidos, proximos = await self._buscar_alertas(usuario.id, hoje, prazo)
            certs = await self._buscar_certificados_vencendo(usuario.id, hoje)
            if not vencidos and not proximos and not certs:
                continue
            html = _render_email(usuario.nome, hoje, vencidos, proximos, certs)
            try:
                smtp_sender.send(
                    to=usuario.email,
                    subject=f"ERP Malvezi — {len(vencidos)} vencido(s), {len(proximos)} a vencer",
                    html=html,
                )
                enviados += 1
                logger.info("notificacao_enviada", usuario_id=str(usuario.id), email=usuario.email)
            except Exception:
                logger.exception("notificacao_erro", usuario_id=str(usuario.id))

        logger.info("notificacoes_concluidas", enviados=enviados)
        return enviados

    async def _listar_usuarios_ativos(self) -> list[Usuario]:
        result = await self._db.execute(
            select(Usuario).where(Usuario.ativo.is_(True))
        )
        return list(result.scalars().all())

    async def _buscar_alertas(
        self,
        usuario_id: uuid.UUID,
        hoje: date,
        prazo: date,
    ) -> tuple[list[dict], list[dict]]:
        sq_emp = select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)

        base = (
            select(
                Lancamento.descricao,
                Lancamento.valor,
                Lancamento.data_vencimento,
                Lancamento.tipo,
                func.coalesce(Empresa.nome_alternativo, Empresa.nome_principal).label("empresa"),
            )
            .join(Empresa, Empresa.id == Lancamento.empresa_id)
            .where(
                Lancamento.empresa_id.in_(sq_emp),
                Lancamento.ativo.is_(True),
                Lancamento.status == StatusLancamento.PENDENTE,
            )
            .order_by(Lancamento.data_vencimento)
        )

        r_venc = await self._db.execute(
            base.where(Lancamento.data_vencimento < hoje).limit(20)
        )
        vencidos = [
            {
                "descricao": r.descricao,
                "valor": Decimal(str(r.valor)),
                "data": r.data_vencimento,
                "tipo": r.tipo,
                "empresa": r.empresa,
            }
            for r in r_venc.all()
        ]

        r_prox = await self._db.execute(
            base.where(
                Lancamento.data_vencimento >= hoje,
                Lancamento.data_vencimento <= prazo,
            ).limit(20)
        )
        proximos = [
            {
                "descricao": r.descricao,
                "valor": Decimal(str(r.valor)),
                "data": r.data_vencimento,
                "tipo": r.tipo,
                "empresa": r.empresa,
            }
            for r in r_prox.all()
        ]

        return vencidos, proximos

    async def _buscar_certificados_vencendo(
        self, usuario_id: uuid.UUID, hoje: date, dias: int = 30
    ) -> list[dict]:
        limite = hoje + timedelta(days=dias)
        sq_emp = select(UsuarioEmpresa.empresa_id).where(UsuarioEmpresa.usuario_id == usuario_id)
        stmt = (
            select(
                Certificado.nome,
                Certificado.validade_fim,
                func.coalesce(Empresa.nome_alternativo, Empresa.nome_principal).label("empresa"),
            )
            .outerjoin(Empresa, Empresa.id == Certificado.empresa_id)
            .where(
                or_(Certificado.empresa_id.in_(sq_emp), Certificado.empresa_id.is_(None)),
                Certificado.ativo.is_(True),
                Certificado.validade_fim.is_not(None),
                Certificado.validade_fim <= limite,
            )
            .order_by(Certificado.validade_fim)
            .limit(30)
        )
        result = await self._db.execute(stmt)
        return [
            {"nome": r.nome, "data": r.validade_fim, "empresa": r.empresa}
            for r in result.all()
        ]


def _render_email(
    nome_usuario: str,
    hoje: date,
    vencidos: list[dict],
    proximos: list[dict],
    certs: list[dict] | None = None,
) -> str:
    def _linha(item: dict) -> str:
        cor = "#dc2626" if item["tipo"] == "DESPESA" else "#16a34a"
        sinal = "-" if item["tipo"] == "DESPESA" else "+"
        atraso = (hoje - item["data"]).days if item["data"] < hoje else 0
        atraso_txt = f' <span style="color:#ef4444;font-size:11px">({atraso}d atraso)</span>' if atraso > 0 else ""
        return (
            f'<tr>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #f1f5f9">{item["empresa"]}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #f1f5f9">{item["descricao"]}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #f1f5f9;white-space:nowrap">'
            f'{item["data"].strftime("%d/%m/%Y")}{atraso_txt}</td>'
            f'<td style="padding:6px 8px;border-bottom:1px solid #f1f5f9;color:{cor};font-weight:600;'
            f'white-space:nowrap;text-align:right">{sinal} R$ {item["valor"]:,.2f}</td>'
            f'</tr>'
        )

    secao_vencidos = ""
    if vencidos:
        linhas = "\n".join(_linha(i) for i in vencidos)
        total = sum(i["valor"] for i in vencidos if i["tipo"] == "DESPESA")
        secao_vencidos = f"""
        <h3 style="color:#dc2626;margin:20px 0 8px">⚠️ Vencidos ({len(vencidos)})</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
          <thead>
            <tr style="background:#fee2e2;color:#7f1d1d">
              <th style="padding:6px 8px;text-align:left">Empresa</th>
              <th style="padding:6px 8px;text-align:left">Descrição</th>
              <th style="padding:6px 8px;text-align:left">Vencimento</th>
              <th style="padding:6px 8px;text-align:right">Valor</th>
            </tr>
          </thead>
          <tbody>{linhas}</tbody>
        </table>
        <p style="text-align:right;font-size:12px;color:#6b7280;margin:4px 0 0">
          Total despesas vencidas: <strong>R$ {total:,.2f}</strong>
        </p>
        """

    secao_proximos = ""
    if proximos:
        linhas = "\n".join(_linha(i) for i in proximos)
        total = sum(i["valor"] for i in proximos if i["tipo"] == "DESPESA")
        secao_proximos = f"""
        <h3 style="color:#d97706;margin:20px 0 8px">📅 Vencendo nos próximos 3 dias ({len(proximos)})</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
          <thead>
            <tr style="background:#fef3c7;color:#78350f">
              <th style="padding:6px 8px;text-align:left">Empresa</th>
              <th style="padding:6px 8px;text-align:left">Descrição</th>
              <th style="padding:6px 8px;text-align:left">Vencimento</th>
              <th style="padding:6px 8px;text-align:right">Valor</th>
            </tr>
          </thead>
          <tbody>{linhas}</tbody>
        </table>
        <p style="text-align:right;font-size:12px;color:#6b7280;margin:4px 0 0">
          Total a pagar: <strong>R$ {total:,.2f}</strong>
        </p>
        """

    secao_certs = ""
    if certs:
        def _linha_cert(c: dict) -> str:
            dias = (c["data"] - hoje).days
            vencido = dias < 0
            cor = "#dc2626" if vencido else "#d97706"
            quando = f"há {abs(dias)}d" if vencido else f"em {dias}d"
            emp = c["empresa"] or "—"
            return (
                f'<tr>'
                f'<td style="padding:6px 8px;border-bottom:1px solid #f1f5f9">{emp}</td>'
                f'<td style="padding:6px 8px;border-bottom:1px solid #f1f5f9">{c["nome"]}</td>'
                f'<td style="padding:6px 8px;border-bottom:1px solid #f1f5f9;color:{cor};'
                f'white-space:nowrap;font-weight:600">{c["data"].strftime("%d/%m/%Y")} ({quando})</td>'
                f'</tr>'
            )

        linhas = "\n".join(_linha_cert(c) for c in certs)
        secao_certs = f"""
        <h3 style="color:#b45309;margin:20px 0 8px">🔐 Certificados a vencer / vencidos ({len(certs)})</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
          <thead>
            <tr style="background:#fef3c7;color:#78350f">
              <th style="padding:6px 8px;text-align:left">Empresa</th>
              <th style="padding:6px 8px;text-align:left">Certificado</th>
              <th style="padding:6px 8px;text-align:left">Validade</th>
            </tr>
          </thead>
          <tbody>{linhas}</tbody>
        </table>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"/></head>
    <body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;padding:20px;color:#1e293b">
      <div style="border-left:4px solid #6366f1;padding-left:16px;margin-bottom:20px">
        <h2 style="margin:0;color:#6366f1">ERP Malvezi</h2>
        <p style="margin:4px 0 0;color:#64748b;font-size:13px">
          Resumo de vencimentos — {hoje.strftime("%d/%m/%Y")}
        </p>
      </div>
      <p>Olá, <strong>{nome_usuario}</strong>!</p>
      <p style="color:#475569">
        Segue o resumo de contas com vencimento pendente para sua atenção:
      </p>
      {secao_vencidos}
      {secao_proximos}
      {secao_certs}
      <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0"/>
      <p style="font-size:12px;color:#94a3b8">
        Este e-mail foi gerado automaticamente pelo ERP Malvezi.
        Acesse o sistema para gerenciar seus lançamentos.
      </p>
    </body>
    </html>
    """
