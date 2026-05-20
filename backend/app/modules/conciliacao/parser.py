"""Parsers para arquivos OFX (SGML) e CSV bancários."""

import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

_TAG_RE = re.compile(r"<([^/>\s][^>]*)>([^<\n\r]*)")
_DATE_RE = re.compile(r"(\d{4})(\d{2})(\d{2})")


def _parse_date_ofx(value: str) -> date:
    m = _DATE_RE.match(value.strip())
    if not m:
        raise ValueError(f"Data OFX inválida: {value!r}")
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _parse_decimal(value: str) -> Decimal:
    value = value.strip().replace(",", ".")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Valor numérico inválido: {value!r}") from exc


_DEBIT_TYPES = {"DEBIT", "CHECK", "PAYMENT", "ATM", "FEE", "SRVCHG", "DIRECTDEBIT", "REPEATPMT"}


def parse_ofx(content: bytes) -> list[dict]:
    """Extrai transações de arquivo OFX no formato SGML (padrão bancos brasileiros).

    Retorna lista de dicts com chaves:
        id_externo, data, valor (Decimal, sempre positivo), tipo ('credito'|'debito'),
        descricao
    """
    text = content.decode("latin-1", errors="replace")

    transactions: list[dict] = []
    current: dict = {}
    in_stmttrn = False

    for line in text.splitlines():
        line = line.strip()
        upper = line.upper()

        if upper == "<STMTTRN>":
            in_stmttrn = True
            current = {}
            continue
        if upper == "</STMTTRN>":
            if in_stmttrn and current:
                transactions.append(_normalize_ofx_entry(current))
            in_stmttrn = False
            current = {}
            continue

        if in_stmttrn:
            m = _TAG_RE.match(line)
            if m:
                tag = m.group(1).strip().upper()
                val = m.group(2).strip()
                current[tag] = val

    return transactions


def _normalize_ofx_entry(entry: dict) -> dict:
    raw_amount = _parse_decimal(entry.get("TRNAMT", "0"))
    trntype = entry.get("TRNTYPE", "").upper()

    if raw_amount < 0:
        tipo = "debito"
    elif raw_amount > 0:
        tipo = "credito"
    else:
        tipo = "debito" if trntype in _DEBIT_TYPES else "credito"

    descricao = (entry.get("MEMO") or entry.get("NAME") or "").strip() or "Sem descrição"

    return {
        "id_externo": entry.get("FITID"),
        "data": _parse_date_ofx(entry.get("DTPOSTED", "")),
        "valor": abs(raw_amount),
        "tipo": tipo,
        "descricao": descricao[:500],
    }


def parse_csv(
    content: bytes,
    delimiter: str = ";",
    col_data: int = 0,
    col_descricao: int = 1,
    col_valor: int = 2,
    decimal_sep: str = ",",
    formato_data: str = "%d/%m/%Y",
    col_tipo: int | None = None,
    encoding: str = "latin-1",
    skip_header: bool = True,
) -> list[dict]:
    """Extrai transações de CSV bancário configurável.

    Valores negativos são tratados como débito; positivos como crédito.
    Se col_tipo for fornecida, espera 'D'/'DEBITO' ou 'C'/'CREDITO' nessa coluna.
    """
    from datetime import datetime

    text = content.decode(encoding, errors="replace")
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    rows = list(reader)
    if skip_header and rows:
        rows = rows[1:]

    transactions: list[dict] = []
    for row in rows:
        if not any(cell.strip() for cell in row):
            continue
        try:
            raw_date = row[col_data].strip()
            data = datetime.strptime(raw_date, formato_data).date()

            raw_valor = row[col_valor].strip()
            if decimal_sep == ",":
                raw_valor = raw_valor.replace(".", "").replace(",", ".")
            valor_num = _parse_decimal(raw_valor)

            if col_tipo is not None:
                t = row[col_tipo].strip().upper()
                tipo = "debito" if t.startswith("D") else "credito"
            else:
                tipo = "debito" if valor_num < 0 else "credito"

            descricao = row[col_descricao].strip() if col_descricao < len(row) else "Sem descrição"
            if not descricao:
                descricao = "Sem descrição"

            transactions.append(
                {
                    "id_externo": None,
                    "data": data,
                    "valor": abs(valor_num),
                    "tipo": tipo,
                    "descricao": descricao[:500],
                }
            )
        except (IndexError, ValueError):
            continue

    return transactions
