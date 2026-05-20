import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  CriarLancamentoConciliacaoRequest,
  ImportacaoBancariaResponse,
  SugestaoMatchResponse,
  TransacaoBancariaResponse,
} from '../models';

@Injectable({ providedIn: 'root' })
export class ConciliacaoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/conciliacao`;

  importarOfx(
    file: File,
    contaBancariaId: string,
    empresaId: string,
  ): Observable<ImportacaoBancariaResponse> {
    const fd = new FormData();
    fd.append('arquivo', file, file.name);
    const params = new HttpParams()
      .set('conta_bancaria_id', contaBancariaId)
      .set('empresa_id', empresaId);
    return this.http.post<ImportacaoBancariaResponse>(`${this.base}/importar/ofx`, fd, { params });
  }

  importarCsv(
    file: File,
    contaBancariaId: string,
    empresaId: string,
  ): Observable<ImportacaoBancariaResponse> {
    const fd = new FormData();
    fd.append('arquivo', file, file.name);
    const params = new HttpParams()
      .set('conta_bancaria_id', contaBancariaId)
      .set('empresa_id', empresaId);
    return this.http.post<ImportacaoBancariaResponse>(`${this.base}/importar/csv`, fd, { params });
  }

  listarImportacoes(contaBancariaId?: string | null): Observable<ImportacaoBancariaResponse[]> {
    let params = new HttpParams();
    if (contaBancariaId) params = params.set('conta_bancaria_id', contaBancariaId);
    return this.http.get<ImportacaoBancariaResponse[]>(`${this.base}/importacoes`, { params });
  }

  listarTransacoes(
    importacaoId: string,
    status?: string | null,
  ): Observable<TransacaoBancariaResponse[]> {
    let params = new HttpParams();
    if (status) params = params.set('status', status);
    return this.http.get<TransacaoBancariaResponse[]>(
      `${this.base}/importacoes/${importacaoId}/transacoes`,
      { params },
    );
  }

  sugerirMatch(transacaoId: string): Observable<SugestaoMatchResponse[]> {
    return this.http.get<SugestaoMatchResponse[]>(
      `${this.base}/transacoes/${transacaoId}/sugerir-match`,
    );
  }

  conciliar(transacaoId: string, lancamentoId: string): Observable<TransacaoBancariaResponse> {
    return this.http.post<TransacaoBancariaResponse>(
      `${this.base}/transacoes/${transacaoId}/conciliar`,
      { lancamento_id: lancamentoId },
    );
  }

  criarLancamento(
    transacaoId: string,
    data: CriarLancamentoConciliacaoRequest,
  ): Observable<TransacaoBancariaResponse> {
    return this.http.post<TransacaoBancariaResponse>(
      `${this.base}/transacoes/${transacaoId}/criar-lancamento`,
      data,
    );
  }

  ignorar(transacaoId: string): Observable<TransacaoBancariaResponse> {
    return this.http.patch<TransacaoBancariaResponse>(
      `${this.base}/transacoes/${transacaoId}/ignorar`,
      {},
    );
  }
}
