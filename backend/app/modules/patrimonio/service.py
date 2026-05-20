import uuid

import structlog

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.patrimonio.models import Imovel, StatusImovel, StatusVeiculo, Veiculo
from app.modules.patrimonio.repository import ImovelRepository, VeiculoRepository
from app.modules.patrimonio.schemas import ImovelCreate, ImovelUpdate, VeiculoCreate, VeiculoUpdate

logger = structlog.get_logger()


class VeiculoService:
    def __init__(self, repo: VeiculoRepository) -> None:
        self._repo = repo

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        status: StatusVeiculo | None = None,
        apenas_ativos: bool = True,
    ) -> list[Veiculo]:
        return await self._repo.listar(usuario_id, empresa_id, status, apenas_ativos)

    async def obter(self, veiculo_id: uuid.UUID, usuario_id: uuid.UUID) -> Veiculo:
        v = await self._repo.get_by_id(veiculo_id)
        if v is None:
            raise NotFoundError("Veículo não encontrado.")
        if v.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso a este veículo.")
        return v

    async def criar(self, data: VeiculoCreate, usuario_id: uuid.UUID) -> Veiculo:
        veiculo = Veiculo(
            empresa_id=data.empresa_id,
            usuario_id=usuario_id,
            placa=data.placa,
            renavam=data.renavam,
            chassi=data.chassi,
            numero_motor=data.numero_motor,
            marca=data.marca,
            modelo=data.modelo,
            ano_fabricacao=data.ano_fabricacao,
            ano_modelo=data.ano_modelo,
            cor=data.cor,
            combustivel=data.combustivel,
            valor_aquisicao=data.valor_aquisicao,
            data_aquisicao=data.data_aquisicao,
            valor_mercado=data.valor_mercado,
            quilometragem=data.quilometragem,
            observacoes=data.observacoes,
        )
        await self._repo.create(veiculo)
        await self._repo.commit()
        await self._repo.refresh(veiculo)
        logger.info("veiculo_criado", marca=data.marca, modelo=data.modelo, usuario_id=str(usuario_id))
        return veiculo

    async def atualizar(
        self, veiculo_id: uuid.UUID, data: VeiculoUpdate, usuario_id: uuid.UUID
    ) -> Veiculo:
        veiculo = await self.obter(veiculo_id, usuario_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(veiculo, field, value)
        await self._repo.commit()
        await self._repo.refresh(veiculo)
        return veiculo

    async def inativar(self, veiculo_id: uuid.UUID, usuario_id: uuid.UUID) -> Veiculo:
        veiculo = await self.obter(veiculo_id, usuario_id)
        if not veiculo.ativo:
            raise ConflictError("Veículo já está inativo.")
        veiculo.ativo = False
        await self._repo.commit()
        await self._repo.refresh(veiculo)
        return veiculo

    async def reativar(self, veiculo_id: uuid.UUID, usuario_id: uuid.UUID) -> Veiculo:
        veiculo = await self.obter(veiculo_id, usuario_id)
        if veiculo.ativo:
            raise ConflictError("Veículo já está ativo.")
        veiculo.ativo = True
        await self._repo.commit()
        await self._repo.refresh(veiculo)
        return veiculo


class ImovelService:
    def __init__(self, repo: ImovelRepository) -> None:
        self._repo = repo

    async def listar(
        self,
        usuario_id: uuid.UUID,
        empresa_id: uuid.UUID | None = None,
        status: StatusImovel | None = None,
        apenas_ativos: bool = True,
    ) -> list[Imovel]:
        return await self._repo.listar(usuario_id, empresa_id, status, apenas_ativos)

    async def obter(self, imovel_id: uuid.UUID, usuario_id: uuid.UUID) -> Imovel:
        i = await self._repo.get_by_id(imovel_id)
        if i is None:
            raise NotFoundError("Imóvel não encontrado.")
        if i.usuario_id != usuario_id:
            raise PermissionDeniedError("Sem acesso a este imóvel.")
        return i

    async def criar(self, data: ImovelCreate, usuario_id: uuid.UUID) -> Imovel:
        imovel = Imovel(
            empresa_id=data.empresa_id,
            usuario_id=usuario_id,
            tipo=data.tipo,
            descricao=data.descricao,
            matricula=data.matricula,
            inscricao_municipal=data.inscricao_municipal,
            cep=data.cep,
            logradouro=data.logradouro,
            numero=data.numero,
            complemento=data.complemento,
            bairro=data.bairro,
            cidade=data.cidade,
            uf=data.uf,
            area_total=data.area_total,
            area_construida=data.area_construida,
            valor_aquisicao=data.valor_aquisicao,
            data_aquisicao=data.data_aquisicao,
            valor_mercado=data.valor_mercado,
            valor_venal=data.valor_venal,
            observacoes=data.observacoes,
        )
        await self._repo.create(imovel)
        await self._repo.commit()
        await self._repo.refresh(imovel)
        logger.info("imovel_criado", tipo=data.tipo, usuario_id=str(usuario_id))
        return imovel

    async def atualizar(
        self, imovel_id: uuid.UUID, data: ImovelUpdate, usuario_id: uuid.UUID
    ) -> Imovel:
        imovel = await self.obter(imovel_id, usuario_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(imovel, field, value)
        await self._repo.commit()
        await self._repo.refresh(imovel)
        return imovel

    async def inativar(self, imovel_id: uuid.UUID, usuario_id: uuid.UUID) -> Imovel:
        imovel = await self.obter(imovel_id, usuario_id)
        if not imovel.ativo:
            raise ConflictError("Imóvel já está inativo.")
        imovel.ativo = False
        await self._repo.commit()
        await self._repo.refresh(imovel)
        return imovel

    async def reativar(self, imovel_id: uuid.UUID, usuario_id: uuid.UUID) -> Imovel:
        imovel = await self.obter(imovel_id, usuario_id)
        if imovel.ativo:
            raise ConflictError("Imóvel já está ativo.")
        imovel.ativo = True
        await self._repo.commit()
        await self._repo.refresh(imovel)
        return imovel
