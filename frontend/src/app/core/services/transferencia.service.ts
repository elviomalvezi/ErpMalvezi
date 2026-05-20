import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Transferencia, TransferenciaCreate } from '../models';

@Injectable({ providedIn: 'root' })
export class TransferenciaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/transferencias`;

  listar(opts: {
    empresaId?: string | null;
    contaId?: string | null;
    status?: string | null;
    dataInicio?: string | null;
    dataFim?: string | null;
    apenasAtivas?: boolean;
  } = {}): Observable<Transferencia[]> {
    let params = new HttpParams().set('apenas_ativas', String(opts.apenasAtivas ?? false));
    if (opts.empresaId) params = params.set('empresa_id', opts.empresaId);
    if (opts.contaId) params = params.set('conta_id', opts.contaId);
    if (opts.status) params = params.set('status', opts.status);
    if (opts.dataInicio) params = params.set('data_inicio', opts.dataInicio);
    if (opts.dataFim) params = params.set('data_fim', opts.dataFim);
    return this.http.get<Transferencia[]>(this.base, { params });
  }

  criar(data: TransferenciaCreate): Observable<Transferencia> {
    return this.http.post<Transferencia>(this.base, data);
  }

  cancelar(id: string): Observable<Transferencia> {
    return this.http.patch<Transferencia>(`${this.base}/${id}/cancelar`, {});
  }
}
