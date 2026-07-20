import csv
import io
import re
import uuid
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree

from app.core.exceptions import DomainError

_MAX_LINHAS_IMPORTACAO = 100000
# Anti zip-bomb: teto de tamanho descomprimido de cada membro do XLSX.
_MAX_MEMBRO_DESCOMPRIMIDO = 80 * 1024 * 1024  # 80 MB por arquivo interno
_PLANILHA_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_CAMPOS_SUPORTADOS = {
    "descricao",
    "valor",
    "data_competencia",
    "data_vencimento",
    "observacoes",
    "categoria_id",
    "contato_id",
    "conta_bancaria_id",
    "categoria_nome",
    "contato_nome",
    "col_tipo",
    "col_empresa",
    "conta_banco",
    "conta_agencia",
    "conta_numero",
}
_CAMPOS_OBRIGATORIOS = {"descricao", "valor", "data_vencimento"}
# data_competencia é opcional — se não mapeada, usa o valor de data_vencimento


@dataclass(slots=True)
class ImportacaoArquivo:
    colunas: list[str]
    linhas: list[dict[str, str]]


def campos_suportados() -> set[str]:
    return set(_CAMPOS_SUPORTADOS)


def campos_obrigatorios() -> set[str]:
    return set(_CAMPOS_OBRIGATORIOS)


def ler_planilha(nome_arquivo: str, conteudo: bytes) -> ImportacaoArquivo:
    extensao = nome_arquivo.lower().rsplit(".", 1)[-1] if "." in nome_arquivo else ""
    if extensao == "csv":
        return _ler_csv(conteudo)
    if extensao == "xlsx":
        return _ler_xlsx(conteudo)
    raise DomainError("Formato de planilha não suportado. Use CSV ou XLSX.")


def validar_mapeamento(mapeamento: dict[str, str | None]) -> dict[str, str]:
    if not mapeamento:
        raise DomainError("Informe ao menos um mapeamento para importar a planilha.")

    normalizado: dict[str, str] = {}
    colunas_usadas: set[str] = set()

    for campo, coluna in mapeamento.items():
        if campo not in _CAMPOS_SUPORTADOS:
            raise DomainError(f"Campo de importação inválido: {campo}.")
        if coluna is None:
            continue
        coluna_limpa = coluna.strip()
        if not coluna_limpa:
            continue
        # Permite a mesma coluna ser usada em múltiplos campos (ex: DATA → vencimento e competência)
        normalizado[campo] = coluna_limpa
        colunas_usadas.add(coluna_limpa)

    faltantes = sorted(_CAMPOS_OBRIGATORIOS - set(normalizado))
    if faltantes:
        raise DomainError(
            "Mapeamento incompleto. Campos obrigatórios: " + ", ".join(faltantes) + "."
        )
    return normalizado


def normalizar_linhas(
    arquivo: ImportacaoArquivo,
    mapeamento: dict[str, str],
) -> list[dict[str, object]]:
    colunas = set(arquivo.colunas)
    for coluna in mapeamento.values():
        if coluna not in colunas:
            raise DomainError(f"A coluna '{coluna}' não existe na planilha enviada.")

    linhas_normalizadas: list[dict[str, object]] = []
    for indice, linha in enumerate(arquivo.linhas, start=2):
        erros: list[str] = []
        payload: dict[str, object] = {}

        descricao = _valor_texto(linha.get(mapeamento["descricao"]))
        if not descricao:
            erros.append("Descrição obrigatória.")
        else:
            payload["descricao"] = descricao

        valor = _parse_decimal(linha.get(mapeamento["valor"]))
        if valor is None or valor == 0:
            # Pula silenciosamente — valor zero, vazio ou "-" não é lançamento
            continue
        payload["valor"] = abs(valor)

        data_vencimento = _parse_data(linha.get(mapeamento["data_vencimento"]))
        if data_vencimento is None:
            erros.append("Data de vencimento inválida.")
        else:
            payload["data_vencimento"] = data_vencimento

        # data_competencia: usa mapeamento próprio ou fallback para data_vencimento
        col_competencia = mapeamento.get("data_competencia")
        if col_competencia:
            data_competencia = _parse_data(linha.get(col_competencia))
        else:
            data_competencia = data_vencimento  # fallback
        if data_competencia is None:
            erros.append("Data de competência inválida.")
        else:
            payload["data_competencia"] = data_competencia

        for campo in ("observacoes", "categoria_nome", "contato_nome", "col_empresa", "conta_banco", "conta_agencia", "conta_numero"):
            coluna = mapeamento.get(campo)
            if coluna is None:
                continue
            payload[campo] = _valor_texto(linha.get(coluna)) or None

        for campo in ("categoria_id", "contato_id", "conta_bancaria_id"):
            coluna = mapeamento.get(campo)
            if coluna is None:
                continue
            valor_bruto = _valor_texto(linha.get(coluna))
            if valor_bruto is not None and not _uuid_valido(valor_bruto):
                erros.append(f"{campo} deve ser informado como UUID válido.")
            payload[campo] = valor_bruto or None

        coluna_tipo = mapeamento.get("col_tipo")
        if coluna_tipo is not None:
            val_tipo = (_valor_texto(linha.get(coluna_tipo)) or "").strip().upper()
            # Normaliza variantes para CAP/CAR
            _MAP_TIPO = {
                "CAP": "CAP", "CAR": "CAR",
                "DESPESA": "CAP", "DESPESAS": "CAP", "D": "CAP",
                "RECEITA": "CAR", "RECEITAS": "CAR", "R": "CAR",
                "SAÍDA": "CAP", "SAIDA": "CAP",
                "ENTRADA": "CAR",
                "DÉBITO": "CAP", "DEBITO": "CAP",
                "CRÉDITO": "CAR", "CREDITO": "CAR",
            }
            val_normalizado = _MAP_TIPO.get(val_tipo)
            if val_normalizado is None:
                erros.append(
                    f"col_tipo '{val_tipo}' não reconhecido. "
                    "Use: CAP/Despesa/Despesas (para despesa) ou CAR/Receita/Receitas (para receita)."
                )
            else:
                payload["col_tipo"] = val_normalizado

        linhas_normalizadas.append(
            {
                "numero_linha": indice,
                "dados_originais": {coluna: linha.get(coluna, "") for coluna in arquivo.colunas},
                "payload": payload,
                "erros": erros,
                "valida": len(erros) == 0,
            }
        )

    return linhas_normalizadas


def _ler_csv(conteudo: bytes) -> ImportacaoArquivo:
    texto = conteudo.decode("utf-8-sig")
    leitor = csv.DictReader(io.StringIO(texto))
    if leitor.fieldnames is None:
        raise DomainError("Não foi possível identificar o cabeçalho da planilha.")
    colunas = [coluna.strip() for coluna in leitor.fieldnames if coluna and coluna.strip()]
    linhas = [_normalizar_linha_csv(linha, colunas) for linha in leitor]
    return _montar_arquivo(colunas, linhas)


def _normalizar_linha_csv(linha: dict[str, str | None], colunas: list[str]) -> dict[str, str]:
    return {coluna: (linha.get(coluna) or "").strip() for coluna in colunas}


def _ler_membro_seguro(pacote: zipfile.ZipFile, nome: str) -> bytes:
    """Lê um membro do XLSX limitando o tamanho descomprimido (anti zip-bomb).

    Lê via stream até o teto + 1 byte; se ultrapassar, aborta sem materializar
    o conteúdo inteiro em memória.
    """
    with pacote.open(nome) as fh:
        dados = fh.read(_MAX_MEMBRO_DESCOMPRIMIDO + 1)
    if len(dados) > _MAX_MEMBRO_DESCOMPRIMIDO:
        raise DomainError("Arquivo XLSX excede o limite de descompressão permitido.")
    return dados


def _ler_xlsx(conteudo: bytes) -> ImportacaoArquivo:
    try:
        with zipfile.ZipFile(io.BytesIO(conteudo)) as pacote:
            shared_strings = _shared_strings_xlsx(pacote)
            sheet_path = _primeira_planilha_path(pacote)
            xml_planilha = ElementTree.fromstring(_ler_membro_seguro(pacote, sheet_path))
    except (KeyError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise DomainError("Arquivo XLSX inválido ou corrompido.") from exc

    linhas_xlsx = [_linha_xlsx(row, shared_strings) for row in xml_planilha.findall(".//a:sheetData/a:row", _PLANILHA_NS)]
    if not linhas_xlsx:
        raise DomainError("A planilha está vazia.")

    cabecalho = [
        _valor_texto(valor) or f"coluna_{indice + 1}"
        for indice, valor in enumerate(linhas_xlsx[0])
    ]
    linhas = []
    for valores in linhas_xlsx[1:]:
        # Linhas podem ter menos células que o cabeçalho (Excel omite células vazias no final)
        linha = {
            cabecalho[indice]: (_valor_texto(valores[indice]) if indice < len(valores) else "") or ""
            for indice in range(len(cabecalho))
        }
        linhas.append(linha)
    return _montar_arquivo(cabecalho, linhas)


def _shared_strings_xlsx(pacote: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in pacote.namelist():
        return []
    raiz = ElementTree.fromstring(_ler_membro_seguro(pacote, "xl/sharedStrings.xml"))
    valores: list[str] = []
    for item in raiz.findall("a:si", _PLANILHA_NS):
        textos = [texto.text or "" for texto in item.findall(".//a:t", _PLANILHA_NS)]
        valores.append("".join(textos))
    return valores


def _primeira_planilha_path(pacote: zipfile.ZipFile) -> str:
    workbook = ElementTree.fromstring(_ler_membro_seguro(pacote, "xl/workbook.xml"))
    rels = ElementTree.fromstring(_ler_membro_seguro(pacote, "xl/_rels/workbook.xml.rels"))
    relacionamentos = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
    }
    primeira_sheet = workbook.find("a:sheets/a:sheet", _PLANILHA_NS)
    if primeira_sheet is None:
        raise DomainError("Nenhuma planilha encontrada no arquivo XLSX.")
    rel_id = primeira_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    if rel_id is None or rel_id not in relacionamentos:
        raise DomainError("Não foi possível localizar a primeira aba da planilha.")
    return "xl/" + relacionamentos[rel_id].lstrip("/")


def _linha_xlsx(row: ElementTree.Element, shared_strings: list[str]) -> list[str]:
    valores: dict[int, str] = {}
    max_coluna = -1
    for cell in row.findall("a:c", _PLANILHA_NS):
        referencia = cell.attrib.get("r", "")
        indice_coluna = _indice_coluna(referencia)
        max_coluna = max(max_coluna, indice_coluna)
        valor = _valor_celula_xlsx(cell, shared_strings)
        valores[indice_coluna] = valor
    return [valores.get(indice, "") for indice in range(max_coluna + 1)]


def _valor_celula_xlsx(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    tipo = cell.attrib.get("t")
    valor = cell.findtext("a:v", default="", namespaces=_PLANILHA_NS)
    if tipo == "s":
        try:
            return shared_strings[int(valor)]
        except (IndexError, ValueError):
            return ""
    if tipo == "inlineStr":
        return "".join(texto.text or "" for texto in cell.findall(".//a:t", _PLANILHA_NS))
    return valor or ""


def _indice_coluna(referencia: str) -> int:
    letras = "".join(ch for ch in referencia if ch.isalpha()).upper()
    indice = 0
    for letra in letras:
        indice = indice * 26 + (ord(letra) - 64)
    return max(indice - 1, 0)


def _montar_arquivo(colunas: list[str], linhas: list[dict[str, str]]) -> ImportacaoArquivo:
    colunas_limpas = [coluna.strip() for coluna in colunas if coluna.strip()]
    if not colunas_limpas:
        raise DomainError("A planilha não possui colunas válidas no cabeçalho.")

    linhas_validas: list[dict[str, str]] = []
    for linha in linhas:
        linha_limpa = {coluna: (linha.get(coluna) or "").strip() for coluna in colunas_limpas}
        if any(valor for valor in linha_limpa.values()):
            linhas_validas.append(linha_limpa)

    if not linhas_validas:
        raise DomainError("A planilha não possui linhas de dados para importar.")
    if len(linhas_validas) > _MAX_LINHAS_IMPORTACAO:
        raise DomainError(f"A planilha excede o limite de {_MAX_LINHAS_IMPORTACAO} linhas.")

    return ImportacaoArquivo(colunas=colunas_limpas, linhas=linhas_validas)


def _valor_texto(valor: str | None) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _parse_decimal(valor: str | None) -> Decimal | None:
    texto = _valor_texto(valor)
    if texto is None:
        return None
    normalizado = texto.replace("R$", "").replace(" ", "")
    if "," in normalizado and "." in normalizado:
        if normalizado.rfind(",") > normalizado.rfind("."):
            normalizado = normalizado.replace(".", "").replace(",", ".")
        else:
            normalizado = normalizado.replace(",", "")
    elif "," in normalizado:
        normalizado = normalizado.replace(".", "").replace(",", ".")
    try:
        return Decimal(normalizado)
    except InvalidOperation:
        return None


def _parse_data(valor: str | None) -> date | None:
    texto = _valor_texto(valor)
    if texto is None:
        return None

    if re.fullmatch(r"\d+(\.\d+)?", texto):
        numero = float(texto)
        if numero > 0:
            return date(1899, 12, 30) + timedelta(days=int(numero))

    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _uuid_valido(valor: str) -> bool:
    try:
        uuid.UUID(valor)
        return True
    except ValueError:
        return False
