"""Validadores de CNPJ e CPF com algoritmo de dígitos verificadores."""

import re


def _only_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def validar_cnpj(cnpj: str) -> bool:
    digits = _only_digits(cnpj)
    if len(digits) != 14:
        return False
    # Rejeita sequências trivialmente inválidas (ex: 00000000000000)
    if len(set(digits)) == 1:
        return False

    def calc_digito(digits: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(digits, weights, strict=True))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = calc_digito(digits[:12], w1)
    d2 = calc_digito(digits[:13], w2)
    return digits[12] == str(d1) and digits[13] == str(d2)


def validar_cpf(cpf: str) -> bool:
    digits = _only_digits(cpf)
    if len(digits) != 11:
        return False
    if len(set(digits)) == 1:
        return False

    def calc_digito(digits: str, factor: int) -> int:
        total = sum(int(d) * (factor - i) for i, d in enumerate(digits))
        remainder = (total * 10) % 11
        return 0 if remainder >= 10 else remainder

    d1 = calc_digito(digits[:9], 10)
    d2 = calc_digito(digits[:10], 11)
    return digits[9] == str(d1) and digits[10] == str(d2)


def formatar_documento(documento: str, tipo: str) -> str:
    """Retorna documento formatado com máscara (armazena sem máscara no banco)."""
    digits = _only_digits(documento)
    if tipo == "PJ" and len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    if tipo == "PF" and len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return documento


def normalizar_documento(documento: str) -> str:
    """Remove máscara, retorna apenas dígitos."""
    return _only_digits(documento)
