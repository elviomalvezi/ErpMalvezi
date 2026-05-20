import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { UsuarioMe } from '../models';

export interface UsuarioCreate {
  nome: string;
  email: string;
  senha: string;
}

@Injectable({ providedIn: 'root' })
export class UsuarioService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/usuarios`;

  listar(): Observable<UsuarioMe[]> {
    return this.http.get<UsuarioMe[]>(this.base);
  }

  criar(data: UsuarioCreate): Observable<UsuarioMe> {
    return this.http.post<UsuarioMe>(this.base, data);
  }

  inativar(id: string): Observable<UsuarioMe> {
    return this.http.patch<UsuarioMe>(`${this.base}/${id}/inativar`, {});
  }

  reativar(id: string): Observable<UsuarioMe> {
    return this.http.patch<UsuarioMe>(`${this.base}/${id}/reativar`, {});
  }
}
