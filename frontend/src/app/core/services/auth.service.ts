import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, switchMap, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { TokenResponse, UsuarioMe } from '../models';
import { AuthStore } from '../stores/auth.store';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly authStore = inject(AuthStore);

  login(email: string, senha: string): Observable<UsuarioMe> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, { email, senha })
      .pipe(
        tap((res) => this.authStore.setToken(res.access_token)),
        switchMap(() => this.me()),
        tap((usuario) => this.authStore.setUsuario(usuario.id, usuario.nome)),
      );
  }

  me(): Observable<UsuarioMe> {
    return this.http.get<UsuarioMe>(`${environment.apiUrl}/usuarios/me`);
  }

  logout(): Observable<void> {
    return this.http
      .post<void>(`${environment.apiUrl}/auth/logout`, {})
      .pipe(tap(() => this.authStore.clearAuth()));
  }
}
