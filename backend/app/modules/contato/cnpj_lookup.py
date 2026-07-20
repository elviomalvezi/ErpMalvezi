"""Consulta de CNPJ via BrasilAPI (gratuita, sem token).

Endpoint: https://brasilapi.com.br/api/cnpj/v1/{cnpj}
Mapeia o retorno da Receita para os campos do cadastro de contato, permitindo
autopreencher fornecedores a partir do CNPJ.
"""

import httpx

from app.core.exceptions import DomainError, NotFoundError

_BRASILAPI_URL = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
_TIMEOUT = 10.0


def _formatar_cep(cep: str | None) -> str | None:
    if not cep:
        return None
    digitos = "".join(c for c in cep if c.isdigit())
    if len(digitos) != 8:
        return cep.strip() or None
    return f"{digitos[:5]}-{digitos[5:]}"


def _formatar_telefone(tel: str | None) -> str | None:
    if not tel:
        return None
    d = "".join(c for c in tel if c.isdigit())
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    return tel.strip() or None


def _limpo(valor: object) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


async def consultar_cnpj(cnpj: str) -> dict[str, str | None]:
    """Consulta o CNPJ na BrasilAPI e devolve os campos prontos para o contato.

    Levanta DomainError (CNPJ inválido / serviço indisponível) ou NotFoundError
    (CNPJ inexistente na base).
    """
    cnpj_limpo = "".join(c for c in cnpj if c.isdigit())
    if len(cnpj_limpo) != 14:
        raise DomainError("CNPJ deve conter 14 dígitos.")

    url = _BRASILAPI_URL.format(cnpj=cnpj_limpo)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers={"Accept": "application/json"})
    except httpx.HTTPError as exc:
        raise DomainError("Falha ao consultar a BrasilAPI. Tente novamente.") from exc

    if resp.status_code == 404:
        raise NotFoundError("CNPJ não encontrado na base da Receita.")
    if resp.status_code != 200:
        raise DomainError("Serviço de consulta de CNPJ indisponível no momento.")

    data = resp.json()
    email = _limpo(data.get("email"))
    return {
        "documento": cnpj_limpo,
        "nome_principal": _limpo(data.get("razao_social")),
        "nome_alternativo": _limpo(data.get("nome_fantasia")),
        "email": email.lower() if email else None,
        "telefone": _formatar_telefone(_limpo(data.get("ddd_telefone_1"))),
        "cep": _formatar_cep(_limpo(data.get("cep"))),
        "logradouro": _limpo(data.get("logradouro")),
        "numero": _limpo(data.get("numero")),
        "complemento": _limpo(data.get("complemento")),
        "bairro": _limpo(data.get("bairro")),
        "cidade": _limpo(data.get("municipio")),
        "uf": _limpo(data.get("uf")),
        "situacao": _limpo(data.get("descricao_situacao_cadastral")),
    }
