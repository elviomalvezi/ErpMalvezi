import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Contato, ContatoCreate, ContatoUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class ContatoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/contatos`;

  listar(opts: {
    empresaId?: string | null;
    ehCliente?: boolean | null;
    ehFornecedor?: boolean | null;
    apenasAtivas?: boolean;
  } = {}): Observable<Contato[]> {
    let params = new HttpParams().set('apenas_ativas', String(opts.apenasAtivas ?? true));
    if (opts.empresaId) params = params.set('empresa_id', opts.empresaId);
    if (opts.ehCliente != null) params = params.set('eh_cliente', String(opts.ehCliente));
    if (opts.ehFornecedor != null) params = params.set('eh_fornecedor', String(opts.ehFornecedor));
    return this.http.get<Contato[]>(this.base, { params });
  }

  criar(data: ContatoCreate): Observable<Contato> {
    return this.http.post<Contato>(this.base, data);
  }

  atualizar(id: string, data: ContatoUpdate): Observable<Contato> {
    return this.http.put<Contato>(`${this.base}/${id}`, data);
  }

  inativar(id: string): Observable<Contato> {
    return this.http.patch<Contato>(`${this.base}/${id}/inativar`, {});
  }

  reativar(id: string): Observable<Contato> {
    return this.http.patch<Contato>(`${this.base}/${id}/reativar`, {});
  }
}
