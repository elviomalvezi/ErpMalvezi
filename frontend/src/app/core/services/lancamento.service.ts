import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  ExtratoResponse,
  ImportacaoAnaliseResponse,
  ImportacaoPreviewResponse,
  ImportacaoResultadoResponse,
  Lancamento,
  LancamentoAnexo,
  LancamentoBaixaCreate,
  LancamentoCreate,
  LancamentoParceladoCreate,
  LancamentoRecorrenteCreate,
  LancamentoUpdate,
} from '../models';

@Injectable({ providedIn: 'root' })
export class LancamentoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/lancamentos`;

  listar(opts: {
    empresaId?: string | null;
    tipo?: string | null;
    status?: string | null;
    dataInicio?: string | null;
    dataFim?: string | null;
    apenasAtivos?: boolean;
    descricao?: string | null;
    limit?: number | null;
  } = {}): Observable<Lancamento[]> {
    let params = new HttpParams().set('apenas_ativos', String(opts.apenasAtivos ?? true));
    if (opts.empresaId) params = params.set('empresa_id', opts.empresaId);
    if (opts.tipo) params = params.set('tipo', opts.tipo);
    if (opts.status) params = params.set('status', opts.status);
    if (opts.dataInicio) params = params.set('data_inicio', opts.dataInicio);
    if (opts.dataFim) params = params.set('data_fim', opts.dataFim);
    if (opts.descricao) params = params.set('descricao', opts.descricao);
    if (opts.limit != null) params = params.set('limit', String(opts.limit));
    return this.http.get<Lancamento[]>(this.base, { params });
  }

  criar(data: LancamentoCreate): Observable<Lancamento> {
    return this.http.post<Lancamento>(this.base, data);
  }

  criarParcelado(data: LancamentoParceladoCreate): Observable<Lancamento[]> {
    return this.http.post<Lancamento[]>(`${this.base}/parcelado`, data);
  }

  criarRecorrente(data: LancamentoRecorrenteCreate): Observable<Lancamento[]> {
    return this.http.post<Lancamento[]>(`${this.base}/recorrente`, data);
  }

  atualizar(id: string, data: LancamentoUpdate): Observable<Lancamento> {
    return this.http.put<Lancamento>(`${this.base}/${id}`, data);
  }

  registrarBaixa(id: string, data: LancamentoBaixaCreate): Observable<Lancamento> {
    return this.http.post<Lancamento>(`${this.base}/${id}/baixa`, data);
  }

  cancelar(id: string): Observable<Lancamento> {
    return this.http.patch<Lancamento>(`${this.base}/${id}/cancelar`, {});
  }

  marcarNaoRealizado(id: string): Observable<Lancamento> {
    return this.http.patch<Lancamento>(`${this.base}/${id}/nao-realizado`, {});
  }

  reverterPrevisto(id: string): Observable<Lancamento> {
    return this.http.patch<Lancamento>(`${this.base}/${id}/reverter-previsto`, {});
  }

  listarAnexos(lancamentoId: string): Observable<LancamentoAnexo[]> {
    return this.http.get<LancamentoAnexo[]>(`${this.base}/${lancamentoId}/anexos`);
  }

  uploadAnexo(lancamentoId: string, file: File): Observable<LancamentoAnexo> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return this.http.post<LancamentoAnexo>(`${this.base}/${lancamentoId}/anexos`, fd);
  }

  deletarAnexo(lancamentoId: string, anexoId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/${lancamentoId}/anexos/${anexoId}`);
  }

  downloadAnexoBlob(lancamentoId: string, anexoId: string): Observable<Blob> {
    return this.http.get(`${this.base}/${lancamentoId}/anexos/${anexoId}/download`, { responseType: 'blob' });
  }

  viewAnexoBlob(lancamentoId: string, anexoId: string): Observable<Blob> {
    return this.http.get(`${this.base}/${lancamentoId}/anexos/${anexoId}/view`, { responseType: 'blob' });
  }

  extrato(opts: {
    contaBancariaId: string;
    dataInicio?: string | null;
    dataFim?: string | null;
  }): Observable<ExtratoResponse> {
    let params = new HttpParams().set('conta_bancaria_id', opts.contaBancariaId);
    if (opts.dataInicio) params = params.set('data_inicio', opts.dataInicio);
    if (opts.dataFim) params = params.set('data_fim', opts.dataFim);
    return this.http.get<ExtratoResponse>(`${this.base}/extrato`, { params });
  }

  duplicar(id: string, empresaId: string): Observable<Lancamento> {
    return this.http.post<Lancamento>(`${this.base}/${id}/duplicar`, { empresa_id: empresaId });
  }

  analisarImportacao(file: File): Observable<ImportacaoAnaliseResponse> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return this.http.post<ImportacaoAnaliseResponse>(`${this.base}/importacao/analisar`, fd);
  }

  preVisualizarImportacao(data: {
    file: File;
    empresaId: string;
    tipo: 'RECEITA' | 'DESPESA';
    mapeamento: Record<string, string | null>;
  }): Observable<ImportacaoPreviewResponse> {
    const fd = new FormData();
    fd.append('file', data.file, data.file.name);
    fd.append('empresa_id', data.empresaId);
    fd.append('tipo', data.tipo);
    fd.append('mapeamento_json', JSON.stringify(data.mapeamento));
    return this.http.post<ImportacaoPreviewResponse>(`${this.base}/importacao/pre-visualizar`, fd);
  }

  confirmarImportacao(data: {
    file: File;
    empresaId: string;
    tipo: 'RECEITA' | 'DESPESA';
    mapeamento: Record<string, string | null>;
  }): Observable<ImportacaoResultadoResponse> {
    const fd = new FormData();
    fd.append('file', data.file, data.file.name);
    fd.append('empresa_id', data.empresaId);
    fd.append('tipo', data.tipo);
    fd.append('mapeamento_json', JSON.stringify(data.mapeamento));
    return this.http.post<ImportacaoResultadoResponse>(`${this.base}/importacao/confirmar`, fd);
  }
}
