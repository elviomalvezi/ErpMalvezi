import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Contato, ContatoCreate, ContatoUpdate } from '../models';

export interface ConsultaCnpj {
  documento: string;
  nome_principal: string | null;
  nome_alternativo: string | null;
  email: string | null;
  telefone: string | null;
  cep: string | null;
  logradouro: string | null;
  numero: string | null;
  complemento: string | null;
  bairro: string | null;
  cidade: string | null;
  uf: string | null;
  situacao: string | null;
}

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

  merge(origemId: string, destinoId: string): Observable<Contato> {
    return this.http.post<Contato>(`${this.base}/${origemId}/merge/${destinoId}`, {});
  }

  consultarCnpj(cnpj: string): Observable<ConsultaCnpj> {
    const params = new HttpParams().set('cnpj', cnpj);
    return this.http.get<ConsultaCnpj>(`${this.base}/consultar-cnpj`, { params });
  }

  verificarDuplicata(
    documento: string,
    excluirId?: string,
  ): Observable<{ existe: boolean; contato: Contato | null }> {
    let params = new HttpParams().set('documento', documento);
    if (excluirId) params = params.set('excluir_id', excluirId);
    return this.http.get<{ existe: boolean; contato: Contato | null }>(
      `${this.base}/verificar-duplicata`,
      { params },
    );
  }
}
