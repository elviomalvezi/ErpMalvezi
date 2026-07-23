"""Extração de metadados de certificados X.509 (PFX/P12, PEM, DER/CER).

Reaproveita a biblioteca `cryptography`. Não persiste a chave privada — só lê os
dados públicos (titular, emissor, validade, série) para controle de vencimento.
"""


from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from app.core.exceptions import DomainError


def _cn(name: x509.Name) -> str | None:
    try:
        return name.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    except (IndexError, x509.AttributeNotFound):
        return None


def _extrair_documento(cn: str | None) -> str | None:
    """ICP-Brasil costuma trazer 'NOME:CNPJ' ou 'NOME:CPF' no CN. Extrai os dígitos."""
    if not cn or ":" not in cn:
        return None
    cauda = cn.split(":")[-1].strip()
    digitos = "".join(c for c in cauda if c.isdigit())
    if len(digitos) in (11, 14):
        return digitos
    return None


def _carregar(conteudo: bytes, senha: str | None, extensao: str) -> tuple[x509.Certificate, str]:
    if extensao in ("pfx", "p12"):
        pwd = senha.encode() if senha else None
        try:
            _, cert, _ = pkcs12.load_key_and_certificates(conteudo, pwd)
        except Exception as exc:  # senha errada / arquivo inválido
            raise DomainError(
                "Não foi possível abrir o certificado. Verifique a senha e o arquivo."
            ) from exc
        if cert is None:
            raise DomainError("O arquivo não contém um certificado válido.")
        return cert, "pfx"

    # PEM ou DER (.cer/.crt/.pem)
    try:
        return x509.load_pem_x509_certificate(conteudo), "pem"
    except ValueError:
        pass
    try:
        return x509.load_der_x509_certificate(conteudo), "der"
    except ValueError as exc:
        raise DomainError("Formato de certificado não reconhecido (use PFX, PEM ou CER).") from exc


def _tem_dns(cert: x509.Certificate) -> bool:
    try:
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        return bool(san.get_values_for_type(x509.DNSName))
    except x509.ExtensionNotFound:
        return False


def _tipo_sugerido(documento: str | None, cert: x509.Certificate) -> str:
    if documento and len(documento) == 14:
        return "e_cnpj"
    if documento and len(documento) == 11:
        return "e_cpf"
    if _tem_dns(cert):
        return "ssl"
    return "outro"


def parse_certificado(conteudo: bytes, senha: str | None, nome_arquivo: str) -> dict:
    extensao = nome_arquivo.lower().rsplit(".", 1)[-1] if "." in nome_arquivo else ""
    cert, formato = _carregar(conteudo, senha, extensao)

    titular = _cn(cert.subject)
    emissor = _cn(cert.issuer)
    documento = _extrair_documento(titular)
    inicio = cert.not_valid_before_utc.date()
    fim = cert.not_valid_after_utc.date()

    return {
        "titular": titular,
        "documento": documento,
        "emissor": emissor,
        "numero_serie": format(cert.serial_number, "X"),
        "validade_inicio": inicio,
        "validade_fim": fim,
        "formato": formato,
        "tipo_sugerido": _tipo_sugerido(documento, cert),
    }
