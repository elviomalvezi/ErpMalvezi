import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { EmpresaCreate, EmpresaListItem, EmpresaResponse, EmpresaUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class EmpresaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/empresas`;

  listar(): Observable<EmpresaListItem[]> {
    return this.http.get<EmpresaListItem[]>(this.base);
  }

  criar(data: EmpresaCreate): Observable<EmpresaResponse> {
    return this.http.post<EmpresaResponse>(this.base, data);
  }

  obter(id: string): Observable<EmpresaResponse> {
    return this.http.get<EmpresaResponse>(`${this.base}/${id}`);
  }

  atualizar(id: string, data: EmpresaUpdate): Observable<EmpresaResponse> {
    return this.http.put<EmpresaResponse>(`${this.base}/${id}`, data);
  }

  inativar(id: string): Observable<EmpresaResponse> {
    return this.http.patch<EmpresaResponse>(`${this.base}/${id}/inativar`, {});
  }

  reativar(id: string): Observable<EmpresaResponse> {
    return this.http.patch<EmpresaResponse>(`${this.base}/${id}/reativar`, {});
  }
}
