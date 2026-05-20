import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ContaBancaria, ContaBancariaCreate, ContaBancariaUpdate, TipoConta } from '../models';

@Injectable({ providedIn: 'root' })
export class ContaBancariaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/contas-bancarias`;

  listar(opts: {
    empresaId?: string | null;
    tipo?: TipoConta | null;
    apenasAtivas?: boolean;
  } = {}): Observable<ContaBancaria[]> {
    let params = new HttpParams().set('apenas_ativas', String(opts.apenasAtivas ?? true));
    if (opts.empresaId) params = params.set('empresa_id', opts.empresaId);
    if (opts.tipo) params = params.set('tipo', opts.tipo);
    return this.http.get<ContaBancaria[]>(this.base, { params });
  }

  criar(data: ContaBancariaCreate): Observable<ContaBancaria> {
    return this.http.post<ContaBancaria>(this.base, data);
  }

  atualizar(id: string, data: ContaBancariaUpdate): Observable<ContaBancaria> {
    return this.http.put<ContaBancaria>(`${this.base}/${id}`, data);
  }

  inativar(id: string): Observable<ContaBancaria> {
    return this.http.patch<ContaBancaria>(`${this.base}/${id}/inativar`, {});
  }

  reativar(id: string): Observable<ContaBancaria> {
    return this.http.patch<ContaBancaria>(`${this.base}/${id}/reativar`, {});
  }
}
