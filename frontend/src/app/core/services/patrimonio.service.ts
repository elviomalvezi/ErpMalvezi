import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  Imovel,
  ImovelCreate,
  ImovelUpdate,
  PatrimonioAnexo,
  Veiculo,
  VeiculoCreate,
  VeiculoUpdate,
} from '../models';

@Injectable({ providedIn: 'root' })
export class PatrimonioService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/patrimonio`;

  // ── Veículos ──────────────────────────────────────────────────────────────

  listarVeiculos(opts: {
    empresaId?: string | null;
    status?: string | null;
    apenasAtivos?: boolean;
  } = {}): Observable<Veiculo[]> {
    let params = new HttpParams().set('apenas_ativos', String(opts.apenasAtivos ?? true));
    if (opts.empresaId) params = params.set('empresa_id', opts.empresaId);
    if (opts.status) params = params.set('status', opts.status);
    return this.http.get<Veiculo[]>(`${this.base}/veiculos`, { params });
  }

  criarVeiculo(data: VeiculoCreate): Observable<Veiculo> {
    return this.http.post<Veiculo>(`${this.base}/veiculos`, data);
  }

  atualizarVeiculo(id: string, data: VeiculoUpdate): Observable<Veiculo> {
    return this.http.put<Veiculo>(`${this.base}/veiculos/${id}`, data);
  }

  inativarVeiculo(id: string): Observable<Veiculo> {
    return this.http.patch<Veiculo>(`${this.base}/veiculos/${id}/inativar`, {});
  }

  reativarVeiculo(id: string): Observable<Veiculo> {
    return this.http.patch<Veiculo>(`${this.base}/veiculos/${id}/reativar`, {});
  }

  // ── Imóveis ───────────────────────────────────────────────────────────────

  listarImoveis(opts: {
    empresaId?: string | null;
    status?: string | null;
    apenasAtivos?: boolean;
  } = {}): Observable<Imovel[]> {
    let params = new HttpParams().set('apenas_ativos', String(opts.apenasAtivos ?? true));
    if (opts.empresaId) params = params.set('empresa_id', opts.empresaId);
    if (opts.status) params = params.set('status', opts.status);
    return this.http.get<Imovel[]>(`${this.base}/imoveis`, { params });
  }

  criarImovel(data: ImovelCreate): Observable<Imovel> {
    return this.http.post<Imovel>(`${this.base}/imoveis`, data);
  }

  atualizarImovel(id: string, data: ImovelUpdate): Observable<Imovel> {
    return this.http.put<Imovel>(`${this.base}/imoveis/${id}`, data);
  }

  inativarImovel(id: string): Observable<Imovel> {
    return this.http.patch<Imovel>(`${this.base}/imoveis/${id}/inativar`, {});
  }

  reativarImovel(id: string): Observable<Imovel> {
    return this.http.patch<Imovel>(`${this.base}/imoveis/${id}/reativar`, {});
  }

  // ── Anexos de Veículo ──────────────────────────────────────────────────────

  listarAnexosVeiculo(veiculoId: string): Observable<PatrimonioAnexo[]> {
    return this.http.get<PatrimonioAnexo[]>(`${this.base}/veiculos/${veiculoId}/anexos`);
  }

  uploadAnexoVeiculo(veiculoId: string, file: File): Observable<PatrimonioAnexo> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return this.http.post<PatrimonioAnexo>(`${this.base}/veiculos/${veiculoId}/anexos`, fd);
  }

  deletarAnexoVeiculo(veiculoId: string, anexoId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/veiculos/${veiculoId}/anexos/${anexoId}`);
  }

  downloadUrlVeiculo(veiculoId: string, anexoId: string): string {
    return `${this.base}/veiculos/${veiculoId}/anexos/${anexoId}/download`;
  }

  // ── Anexos de Imóvel ───────────────────────────────────────────────────────

  listarAnexosImovel(imovelId: string): Observable<PatrimonioAnexo[]> {
    return this.http.get<PatrimonioAnexo[]>(`${this.base}/imoveis/${imovelId}/anexos`);
  }

  uploadAnexoImovel(imovelId: string, file: File): Observable<PatrimonioAnexo> {
    const fd = new FormData();
    fd.append('file', file, file.name);
    return this.http.post<PatrimonioAnexo>(`${this.base}/imoveis/${imovelId}/anexos`, fd);
  }

  deletarAnexoImovel(imovelId: string, anexoId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/imoveis/${imovelId}/anexos/${anexoId}`);
  }

  downloadUrlImovel(imovelId: string, anexoId: string): string {
    return `${this.base}/imoveis/${imovelId}/anexos/${anexoId}/download`;
  }
}
