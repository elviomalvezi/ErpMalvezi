import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.modules.empresa.models import Empresa, TipoPessoa, UsuarioEmpresa
from app.modules.empresa.repository import EmpresaRepository
from app.modules.empresa.schemas import EmpresaCreate, EmpresaUpdate
from app.modules.empresa.validators import (
    normalizar_documento,
    validar_cnpj,
    validar_cpf,
)


def _validar_documento(documento: str, tipo: TipoPessoa) -> str:
    normalizado = normalizar_documento(documento)
    if tipo == TipoPessoa.PJ:
        if not validar_cnpj(normalizado):
            raise DomainError("CNPJ inválido")
    else:
        if not validar_cpf(normalizado):
            raise DomainError("CPF inválido")
    return normalizado


class EmpresaService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = EmpresaRepository(db)
        self.db = db

    async def criar(self, data: EmpresaCreate, criado_por: uuid.UUID) -> Empresa:
        documento = _validar_documento(data.documento, data.tipo)

        if await self.repo.get_by_documento(documento):
            raise ConflictError(
                "Já existe uma empresa cadastrada com este documento"
            )

        empresa = Empresa(
            tipo=data.tipo,
            documento=documento,
            nome_principal=data.nome_principal,
            nome_alternativo=data.nome_alternativo,
            documento_complementar_1=data.documento_complementar_1,
            documento_complementar_2=data.documento_complementar_2,
            regime_tributario=data.regime_tributario,
            moeda_padrao=data.moeda_padrao,
            simbolo_monetario=data.simbolo_monetario,
            separador_decimal=data.separador_decimal,
            separador_milhares=data.separador_milhares,
            casas_decimais_valor=data.casas_decimais_valor,
            casas_decimais_percentual=data.casas_decimais_percentual,
            mes_inicio_exercicio=data.mes_inicio_exercicio,
            dia_fechamento_mensal=data.dia_fechamento_mensal,
            prefixo_lancamento=data.prefixo_lancamento,
            reset_anual_numeracao=data.reset_anual_numeracao,
            cor_primaria=data.cor_primaria,
            endereco_cep=data.endereco_cep,
            logradouro=data.logradouro,
            numero=data.numero,
            complemento=data.complemento,
            bairro=data.bairro,
            cidade=data.cidade,
            uf=data.uf,
            pais=data.pais,
            telefone=data.telefone,
            email=data.email,
            criado_por=criado_por,
        )
        empresa = await self.repo.create(empresa)

        vinculo = UsuarioEmpresa(usuario_id=criado_por, empresa_id=empresa.id)
        await self.repo.create_vinculo(vinculo)

        await self.db.commit()
        await self.db.refresh(empresa)
        return empresa

    async def listar_por_usuario(self, usuario_id: uuid.UUID) -> list[Empresa]:
        return list(await self.repo.list_by_usuario(usuario_id))

    async def obter(self, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> Empresa:
        empresa = await self.repo.get_by_id(empresa_id)
        if not empresa:
            raise NotFoundError("Empresa não encontrada")
        vinculo = await self.repo.get_vinculo(usuario_id, empresa_id)
        if not vinculo:
            raise NotFoundError("Empresa não encontrada")
        return empresa

    async def atualizar(
        self, empresa_id: uuid.UUID, data: EmpresaUpdate, usuario_id: uuid.UUID
    ) -> Empresa:
        empresa = await self.obter(empresa_id, usuario_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(empresa, field, value)

        await self.db.commit()
        await self.db.refresh(empresa)
        return empresa

    async def inativar(self, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> Empresa:
        empresa = await self.obter(empresa_id, usuario_id)
        if not empresa.ativa:
            raise DomainError("Empresa já está inativa")
        empresa.ativa = False
        await self.db.commit()
        await self.db.refresh(empresa)
        return empresa

    async def atualizar_logo(
        self,
        empresa_id: uuid.UUID,
        usuario_id: uuid.UUID,
        conteudo: bytes,
        extensao: str,
        content_type: str,
        storage,  # StorageProvider — injetado pelo router para evitar import circular
    ) -> Empresa:
        from app.core.storage import gerar_caminho_logo

        empresa = await self.obter(empresa_id, usuario_id)

        if empresa.logo_url:
            import contextlib

            from app.core.storage import gerar_caminho_logo as _gcl
            antigo_caminho = _gcl(empresa.id, empresa.logo_url.rsplit(".", 1)[-1])
            with contextlib.suppress(Exception):
                await storage.excluir(antigo_caminho)

        caminho = gerar_caminho_logo(empresa.id, extensao)
        url = await storage.salvar(conteudo, caminho, content_type)
        empresa.logo_url = url

        await self.db.commit()
        await self.db.refresh(empresa)
        return empresa

    async def reativar(self, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> Empresa:
        empresa = await self.obter(empresa_id, usuario_id)
        if empresa.ativa:
            raise DomainError("Empresa já está ativa")
        empresa.ativa = True
        await self.db.commit()
        await self.db.refresh(empresa)
        return empresa
