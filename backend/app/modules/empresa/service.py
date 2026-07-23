import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.modules.empresa.models import (
    DominioSistema,
    Empresa,
    EmpresaDominio,
    TipoPessoa,
    UsuarioEmpresa,
)
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

        codigo = data.codigo or await self.repo.proximo_codigo()
        if await self.repo.get_by_codigo(codigo):
            raise ConflictError(f"Já existe uma empresa com o código {codigo}")

        empresa = Empresa(
            codigo=codigo,
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

        # Empresa nova nasce com os domínios do núcleo atual habilitados.
        for dominio in (DominioSistema.FINANCEIRO, DominioSistema.CADASTROS):
            self.db.add(EmpresaDominio(empresa_id=empresa.id, dominio=dominio))

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

        novo_codigo = update_data.get("codigo")
        if novo_codigo is not None and novo_codigo != empresa.codigo:
            existente_codigo = await self.repo.get_by_codigo(novo_codigo)
            if existente_codigo and existente_codigo.id != empresa_id:
                raise ConflictError(f"Já existe uma empresa com o código {novo_codigo}")

        novo_tipo = update_data.get("tipo", empresa.tipo)
        novo_doc = update_data.get("documento")

        if novo_doc is not None:
            novo_doc = _validar_documento(novo_doc, novo_tipo)
            if novo_doc != empresa.documento:
                existente = await self.repo.get_by_documento(novo_doc)
                if existente and existente.id != empresa_id:
                    raise ConflictError("Já existe uma empresa cadastrada com este documento")
            update_data["documento"] = novo_doc

        if update_data.get("tipo") == TipoPessoa.PF and "regime_tributario" not in update_data:
            update_data["regime_tributario"] = None

        for field, value in update_data.items():
            setattr(empresa, field, value)

        await self.db.commit()
        await self.db.refresh(empresa)
        return empresa

    async def excluir(self, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> None:
        empresa = await self.obter(empresa_id, usuario_id)
        if await self.repo.has_lancamentos(empresa_id):
            raise DomainError("Empresa possui lançamentos e não pode ser excluída permanentemente.")
        from sqlalchemy import delete as sql_delete
        await self.db.execute(
            sql_delete(UsuarioEmpresa).where(UsuarioEmpresa.empresa_id == empresa_id)
        )
        await self.db.delete(empresa)
        await self.db.commit()

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

    async def listar_dominios(
        self, empresa_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> list[EmpresaDominio]:
        await self.obter(empresa_id, usuario_id)  # valida vínculo
        return list(await self.repo.list_dominios(empresa_id))

    async def atualizar_dominios(
        self,
        empresa_id: uuid.UUID,
        dominios: list[DominioSistema],
        usuario_id: uuid.UUID,
    ) -> list[EmpresaDominio]:
        await self.obter(empresa_id, usuario_id)
        if DominioSistema.FINANCEIRO not in dominios:
            raise DomainError("O domínio Financeiro não pode ser desabilitado.")
        await self.repo.replace_dominios(empresa_id, dominios)
        await self.db.commit()
        return list(await self.repo.list_dominios(empresa_id))

    async def reativar(self, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> Empresa:
        empresa = await self.obter(empresa_id, usuario_id)
        if empresa.ativa:
            raise DomainError("Empresa já está ativa")
        empresa.ativa = True
        await self.db.commit()
        await self.db.refresh(empresa)
        return empresa
