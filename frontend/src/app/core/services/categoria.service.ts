import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Categoria, CategoriaCreate, CategoriaUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class CategoriaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/categorias`;

  listar(empresaId?: string | null, apenasAtivas = true): Observable<Categoria[]> {
    let params = new HttpParams().set('apenas_ativas', String(apenasAtivas));
    if (empresaId) params = params.set('empresa_id', empresaId);
    return this.http.get<Categoria[]>(this.base, { params });
  }

  criar(data: CategoriaCreate): Observable<Categoria> {
    return this.http.post<Categoria>(this.base, data);
  }

  atualizar(id: string, data: CategoriaUpdate): Observable<Categoria> {
    return this.http.put<Categoria>(`${this.base}/${id}`, data);
  }

  inativar(id: string): Observable<Categoria> {
    return this.http.patch<Categoria>(`${this.base}/${id}/inativar`, {});
  }

  reativar(id: string): Observable<Categoria> {
    return this.http.patch<Categoria>(`${this.base}/${id}/reativar`, {});
  }

  inicializarPlanoPadrao(): Observable<{ criadas: number }> {
    return this.http.post<{ criadas: number }>(`${this.base}/plano-padrao`, {});
  }
}
