// Interfaces que espelham os schemas do backend

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UsuarioMe {
  id: string;
  nome: string;
  email: string;
  ativo: boolean;
  admin: boolean;
  gestor: boolean;
  email_verificado: boolean;
  preferencia_multi_empresa: boolean;
  foto_url: string | null;
}

export interface EmpresaListItem {
  id: string;
  tipo: 'PJ' | 'PF';
  documento: string | null;
  nome_principal: string;
  nome_alternativo: string | null;
  cor_primaria: string | null;
  logo_url: string | null;
  ativa: boolean;
}

export interface Lancamento {
  id: string;
  empresa_id: string;
  usuario_id: string;
  tipo: 'RECEITA' | 'DESPESA';
  descricao: string;
  valor: number;
  valor_pago: number;
  data_competencia: string;
  data_vencimento: string;
  data_pagamento: string | null;
  status: 'pendente' | 'pago' | 'cancelado' | 'nao_realizado';
  categoria_id: string | null;
  contato_id: string | null;
  conta_bancaria_id: string | null;
  fatura_id: string | null;
  numero_parcela: number | null;
  total_parcelas: number | null;
  grupo_parcelas_id: string | null;
  recorrencia_id: string | null;
  observacoes: string | null;
  tags: string[];
  veiculo_id: string | null;
  imovel_id: string | null;
  ativo: boolean;
  tem_anexo: boolean;
}

export interface LancamentoCreate {
  empresa_id: string;
  tipo: 'RECEITA' | 'DESPESA';
  descricao: string;
  valor: number;
  data_competencia: string;
  data_vencimento: string;
  categoria_id?: string | null;
  contato_id?: string | null;
  conta_bancaria_id?: string | null;
  observacoes?: string | null;
  tags?: string[];
  veiculo_id?: string | null;
  imovel_id?: string | null;
}

export interface LancamentoParceladoCreate {
  empresa_id: string;
  tipo: 'RECEITA' | 'DESPESA';
  descricao: string;
  valor_total: number;
  parcelas: number;
  data_primeira_competencia: string;
  data_primeiro_vencimento: string;
  categoria_id?: string | null;
  contato_id?: string | null;
  conta_bancaria_id?: string | null;
  observacoes?: string | null;
  tags?: string[];
  veiculo_id?: string | null;
  imovel_id?: string | null;
}

export interface LancamentoRecorrenteCreate {
  empresa_id: string;
  tipo: 'RECEITA' | 'DESPESA';
  descricao: string;
  valor: number;
  data_primeira_competencia: string;
  data_primeiro_vencimento: string;
  frequencia: 'semanal' | 'quinzenal' | 'mensal' | 'anual';
  quantidade: number;
  categoria_id?: string | null;
  contato_id?: string | null;
  conta_bancaria_id?: string | null;
  observacoes?: string | null;
  tags?: string[];
  veiculo_id?: string | null;
  imovel_id?: string | null;
}

export interface LancamentoBaixaCreate {
  valor_pago: number;
  data_pagamento: string;
  conta_bancaria_id: string;
  categoria_id: string;
}

export interface LancamentoUpdate {
  descricao?: string | null;
  valor?: number | null;
  data_competencia?: string | null;
  data_vencimento?: string | null;
  categoria_id?: string | null;
  contato_id?: string | null;
  observacoes?: string | null;
  tags?: string[];
  veiculo_id?: string | null;
  imovel_id?: string | null;
}

export interface Transferencia {
  id: string;
  usuario_id: string;
  empresa_origem_id: string;
  empresa_destino_id: string;
  conta_origem_id: string;
  conta_destino_id: string;
  valor: number;
  data_transferencia: string;
  descricao: string | null;
  status: 'concluida' | 'cancelada';
  ativo: boolean;
}

export type TipoConta = 'corrente' | 'poupanca' | 'caixinha' | 'aplicacao' | 'cartao_credito';
export type BandeiraCartao = 'visa' | 'mastercard' | 'elo' | 'amex' | 'hipercard' | 'outro';

export interface ContaBancaria {
  id: string;
  empresa_id: string;
  usuario_id: string;
  nome: string;
  tipo: TipoConta;
  banco: string | null;
  agencia: string | null;
  numero_conta: string | null;
  digito: string | null;
  saldo_inicial: number;
  data_saldo_inicial: string | null;
  bandeira: BandeiraCartao | null;
  limite: number | null;
  dia_vencimento: number | null;
  dia_fechamento: number | null;
  ativa: boolean;
}

export interface ContaBancariaCreate {
  empresa_id: string;
  nome: string;
  tipo: TipoConta;
  banco?: string | null;
  agencia?: string | null;
  numero_conta?: string | null;
  digito?: string | null;
  saldo_inicial?: number;
  data_saldo_inicial?: string | null;
  bandeira?: BandeiraCartao | null;
  limite?: number | null;
  dia_vencimento?: number | null;
  dia_fechamento?: number | null;
}

export interface ContaBancariaUpdate {
  nome?: string | null;
  banco?: string | null;
  agencia?: string | null;
  numero_conta?: string | null;
  digito?: string | null;
  saldo_inicial?: number | null;
  data_saldo_inicial?: string | null;
  bandeira?: BandeiraCartao | null;
  limite?: number | null;
  dia_vencimento?: number | null;
  dia_fechamento?: number | null;
}

export interface Categoria {
  id: string;
  usuario_id: string;
  empresa_id: string | null;
  parent_id: string | null;
  nome: string;
  tipo: 'RECEITA' | 'DESPESA';
  escopo: 'global' | 'especifico';
  nivel: number;
  codigo: string | null;
  descricao: string | null;
  exigir_veiculo: boolean;
  exigir_imovel: boolean;
  ativa: boolean;
}

export interface CategoriaCreate {
  nome: string;
  tipo: 'RECEITA' | 'DESPESA';
  escopo: 'global' | 'especifico';
  parent_id?: string | null;
  empresa_id?: string | null;
  codigo?: string | null;
  descricao?: string | null;
  exigir_veiculo?: boolean;
  exigir_imovel?: boolean;
}

export interface CategoriaUpdate {
  nome?: string | null;
  parent_id?: string | null;
  codigo?: string | null;
  descricao?: string | null;
  exigir_veiculo?: boolean | null;
  exigir_imovel?: boolean | null;
}

export interface DashboardResponse {
  empresa_id: string | null;
  data_inicio: string;
  data_fim: string;
  saldo_contas: number;
  kpi: {
    receitas_realizadas: number;
    despesas_realizadas: number;
    receitas_previstas: number;
    despesas_previstas: number;
    saldo_realizado: number;
    saldo_previsto: number;
  };
  a_vencer_hoje: LancamentoPendente[];
  vencidos: LancamentoPendente[];
  proximos_vencimentos: LancamentoPendente[];
  alertas_count: number;
}

export interface GraficosResponse {
  despesas_por_categoria: { categoria: string; total: number }[];
  evolucao_mensal: { mes: string; receitas: number; despesas: number }[];
  alertas_count: number;
}

export interface LancamentoPendente {
  id: string;
  descricao: string;
  valor: number;
  data_vencimento: string;
  tipo: string;
}

export interface ApiError {
  detail: string | { msg: string }[];
}

export type TipoPessoa = 'PJ' | 'PF';
export type RegimeTributario = 'Simples' | 'Presumido' | 'Real' | 'MEI';

export interface EmpresaCreate {
  tipo: TipoPessoa;
  documento: string;
  nome_principal: string;
  nome_alternativo?: string | null;
  regime_tributario?: RegimeTributario | null;
  documento_complementar_1?: string | null;
  documento_complementar_2?: string | null;
  endereco_cep?: string | null;
  logradouro?: string | null;
  numero?: string | null;
  complemento?: string | null;
  bairro?: string | null;
  cidade?: string | null;
  uf?: string | null;
  pais?: string;
  telefone?: string | null;
  email?: string | null;
  cor_primaria?: string | null;
}

export interface EmpresaUpdate {
  tipo?: TipoPessoa | null;
  documento?: string | null;
  nome_principal?: string | null;
  nome_alternativo?: string | null;
  regime_tributario?: RegimeTributario | null;
  documento_complementar_1?: string | null;
  documento_complementar_2?: string | null;
  endereco_cep?: string | null;
  logradouro?: string | null;
  numero?: string | null;
  complemento?: string | null;
  bairro?: string | null;
  cidade?: string | null;
  uf?: string | null;
  pais?: string | null;
  telefone?: string | null;
  email?: string | null;
  cor_primaria?: string | null;
  separador_decimal?: string | null;
  separador_milhares?: string | null;
  casas_decimais_valor?: number | null;
  casas_decimais_percentual?: number | null;
  mes_inicio_exercicio?: number | null;
  trava_fechamento_ativa?: boolean | null;
  dia_fechamento_mensal?: number | null;
  prefixo_lancamento?: string | null;
  reset_anual_numeracao?: boolean | null;
  email_remetente_nome?: string | null;
  email_assinatura?: string | null;
}

export interface EmpresaResponse {
  id: string;
  tipo: TipoPessoa;
  documento: string | null;
  nome_principal: string;
  nome_alternativo: string | null;
  documento_complementar_1: string | null;
  documento_complementar_2: string | null;
  regime_tributario: RegimeTributario | null;
  moeda_padrao: string;
  simbolo_monetario: string;
  separador_decimal: string;
  separador_milhares: string;
  casas_decimais_valor: number;
  casas_decimais_percentual: number;
  mes_inicio_exercicio: number;
  trava_fechamento_ativa: boolean;
  dia_fechamento_mensal: number;
  prefixo_lancamento: string;
  reset_anual_numeracao: boolean;
  cor_primaria: string | null;
  logo_url: string | null;
  email_remetente_nome: string | null;
  email_assinatura: string | null;
  endereco_cep: string | null;
  logradouro: string | null;
  numero: string | null;
  complemento: string | null;
  bairro: string | null;
  cidade: string | null;
  uf: string | null;
  pais: string;
  telefone: string | null;
  email: string | null;
  ativa: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface Contato {
  id: string;
  usuario_id: string;
  empresa_id: string | null;
  tipo: 'PJ' | 'PF';
  documento: string | null;
  nome_principal: string;
  nome_alternativo: string | null;
  eh_cliente: boolean;
  eh_fornecedor: boolean;
  escopo: 'global' | 'especifico';
  email: string | null;
  telefone: string | null;
  celular: string | null;
  site: string | null;
  cep: string | null;
  logradouro: string | null;
  numero: string | null;
  complemento: string | null;
  bairro: string | null;
  cidade: string | null;
  uf: string | null;
  pais: string;
  observacoes: string | null;
  ativa: boolean;
}

export interface ContatoCreate {
  tipo: 'PJ' | 'PF';
  documento: string;
  nome_principal: string;
  nome_alternativo?: string | null;
  eh_cliente?: boolean;
  eh_fornecedor?: boolean;
  escopo?: 'global' | 'especifico';
  empresa_id?: string | null;
  email?: string | null;
  telefone?: string | null;
  celular?: string | null;
  site?: string | null;
  cep?: string | null;
  logradouro?: string | null;
  numero?: string | null;
  complemento?: string | null;
  bairro?: string | null;
  cidade?: string | null;
  uf?: string | null;
  pais?: string;
  observacoes?: string | null;
}

export interface ContatoUpdate {
  documento?: string | null;
  nome_principal?: string | null;
  nome_alternativo?: string | null;
  eh_cliente?: boolean | null;
  eh_fornecedor?: boolean | null;
  escopo?: 'global' | 'especifico' | null;
  empresa_id?: string | null;
  email?: string | null;
  telefone?: string | null;
  celular?: string | null;
  site?: string | null;
  cep?: string | null;
  logradouro?: string | null;
  numero?: string | null;
  complemento?: string | null;
  bairro?: string | null;
  cidade?: string | null;
  uf?: string | null;
  pais?: string | null;
  observacoes?: string | null;
}

// ─────────────────────────────────── Patrimônio Anexos ──────────────────────

export interface PatrimonioAnexo {
  id: string;
  registro_id: string;
  usuario_id: string;
  nome_original: string;
  tamanho: number;
  mime_type: string;
  criado_em: string;
}

// ─────────────────────────────────── Lançamento Anexos ──────────────────────

export interface LancamentoAnexo {
  id: string;
  lancamento_id: string;
  usuario_id: string;
  nome_original: string;
  tamanho: number;
  mime_type: string;
  criado_em: string;
}

export interface ImportacaoAnaliseResponse {
  colunas: string[];
  total_linhas: number;
  amostras: Record<string, string>[];
  campos_suportados: string[];
  campos_obrigatorios: string[];
}

export interface ExtratoItem {
  lancamento: Lancamento;
  saldo_apos: number;
}

export interface ExtratoResponse {
  conta_bancaria_id: string;
  data_inicio: string | null;
  data_fim: string | null;
  saldo_anterior: number;
  saldo_final: number;
  itens: ExtratoItem[];
}

export interface ImportacaoLinhaPreview {
  numero_linha: number;
  dados_originais: Record<string, string>;
  payload: Record<string, any>;
  erros: string[];
  valida: boolean;
}

export interface ImportacaoPreviewResponse {
  total_linhas: number;
  linhas_validas: number;
  linhas_invalidas: number;
  itens: ImportacaoLinhaPreview[];
}

export interface ImportacaoResultadoResponse {
  total_linhas: number;
  importadas: number;
  ignoradas: number;
  empresas_criadas_importacao: string[];
}

// ─────────────────────────────────── Patrimônio ──────────────────────────────

export type StatusVeiculo = 'ativo' | 'vendido' | 'sinistrado' | 'inativo';
export type CombustivelVeiculo = 'gasolina' | 'etanol' | 'flex' | 'diesel' | 'eletrico' | 'hibrido' | 'gnv';
export type TipoImovel = 'casa' | 'apartamento' | 'terreno' | 'sala_comercial' | 'galpao' | 'loja' | 'outro';
export type StatusImovel = 'ativo' | 'locado' | 'vendido' | 'em_reforma' | 'inativo';

export interface Veiculo {
  id: string;
  empresa_id: string;
  usuario_id: string;
  placa: string | null;
  renavam: string | null;
  chassi: string | null;
  numero_motor: string | null;
  marca: string;
  modelo: string;
  ano_fabricacao: number;
  ano_modelo: number | null;
  cor: string | null;
  combustivel: CombustivelVeiculo | null;
  valor_aquisicao: number;
  data_aquisicao: string | null;
  valor_mercado: number | null;
  quilometragem: number | null;
  status: StatusVeiculo;
  observacoes: string | null;
  ativo: boolean;
}

export interface VeiculoCreate {
  empresa_id: string;
  placa?: string | null;
  renavam?: string | null;
  chassi?: string | null;
  numero_motor?: string | null;
  marca: string;
  modelo: string;
  ano_fabricacao: number;
  ano_modelo?: number | null;
  cor?: string | null;
  combustivel?: CombustivelVeiculo | null;
  valor_aquisicao: number;
  data_aquisicao?: string | null;
  valor_mercado?: number | null;
  quilometragem?: number | null;
  observacoes?: string | null;
}

export interface VeiculoUpdate {
  placa?: string | null;
  renavam?: string | null;
  chassi?: string | null;
  numero_motor?: string | null;
  marca?: string | null;
  modelo?: string | null;
  ano_fabricacao?: number | null;
  ano_modelo?: number | null;
  cor?: string | null;
  combustivel?: CombustivelVeiculo | null;
  valor_aquisicao?: number | null;
  data_aquisicao?: string | null;
  valor_mercado?: number | null;
  quilometragem?: number | null;
  status?: StatusVeiculo | null;
  observacoes?: string | null;
}

export interface Imovel {
  id: string;
  empresa_id: string;
  usuario_id: string;
  tipo: TipoImovel;
  descricao: string;
  matricula: string | null;
  inscricao_municipal: string | null;
  cep: string | null;
  logradouro: string | null;
  numero: string | null;
  complemento: string | null;
  bairro: string | null;
  cidade: string | null;
  uf: string | null;
  area_total: number | null;
  area_construida: number | null;
  valor_aquisicao: number;
  data_aquisicao: string | null;
  valor_mercado: number | null;
  valor_venal: number | null;
  status: StatusImovel;
  observacoes: string | null;
  ativo: boolean;
}

export interface ImovelCreate {
  empresa_id: string;
  tipo: TipoImovel;
  descricao: string;
  matricula?: string | null;
  inscricao_municipal?: string | null;
  cep?: string | null;
  logradouro?: string | null;
  numero?: string | null;
  complemento?: string | null;
  bairro?: string | null;
  cidade?: string | null;
  uf?: string | null;
  area_total?: number | null;
  area_construida?: number | null;
  valor_aquisicao: number;
  data_aquisicao?: string | null;
  valor_mercado?: number | null;
  valor_venal?: number | null;
  observacoes?: string | null;
}

export interface ImovelUpdate {
  tipo?: TipoImovel | null;
  descricao?: string | null;
  matricula?: string | null;
  inscricao_municipal?: string | null;
  cep?: string | null;
  logradouro?: string | null;
  numero?: string | null;
  complemento?: string | null;
  bairro?: string | null;
  cidade?: string | null;
  uf?: string | null;
  area_total?: number | null;
  area_construida?: number | null;
  valor_aquisicao?: number | null;
  data_aquisicao?: string | null;
  valor_mercado?: number | null;
  valor_venal?: number | null;
  status?: StatusImovel | null;
  observacoes?: string | null;
}

// ─────────────────────────────────── Transferências ──────────────────────────

export interface TransferenciaCreate {
  empresa_origem_id: string;
  empresa_destino_id: string;
  conta_origem_id: string;
  conta_destino_id: string;
  valor: number;
  data_transferencia: string;
  descricao?: string | null;
}

// ─────────────────────────────────── Fluxo de Caixa ──────────────────────────

export interface PeriodoFluxo {
  periodo: string;
  receitas_realizadas: string | number;
  despesas_realizadas: string | number;
  receitas_previstas: string | number;
  despesas_previstas: string | number;
}

export interface FluxoCaixaResponse {
  empresa_ids: string[];
  data_inicio: string;
  data_fim: string;
  saldo_inicial: string | number;
  periodos: PeriodoFluxo[];
}

// ─────────────────────────────────── Conciliação Bancária ────────────────────

export interface ImportacaoBancariaResponse {
  id: string;
  conta_bancaria_id: string;
  empresa_id: string;
  nome_arquivo: string;
  status: 'processando' | 'concluida' | 'erro';
  total_transacoes: number;
  conciliadas: number;
  ignoradas: number;
}

export interface TransacaoBancariaResponse {
  id: string;
  importacao_id: string;
  conta_bancaria_id: string;
  empresa_id: string;
  id_externo: string | null;
  data: string;
  valor: number;
  tipo: 'credito' | 'debito';
  descricao_original: string;
  status: 'pendente' | 'conciliada' | 'ignorada';
  lancamento_id: string | null;
}

export interface SugestaoMatchResponse {
  id: string;
  descricao: string;
  valor: number;
  data_vencimento: string;
  tipo: 'RECEITA' | 'DESPESA';
}

export interface CriarLancamentoConciliacaoRequest {
  empresa_id: string;
  descricao: string;
  tipo: 'RECEITA' | 'DESPESA';
  data_competencia: string;
  data_vencimento: string;
  categoria_id?: string | null;
  observacoes?: string | null;
}
