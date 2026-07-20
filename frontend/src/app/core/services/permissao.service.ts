import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface MenuPermissao { id: string; chave: string; nome: string; ordem: number; }
export interface AcaoPermissao { id: string; chave: string; nome: string; }
export interface PermissaoItem { menu_chave: string; acao_chave: string; }
export interface PermissaoMatrizItem { menu_chave: string; menu_nome: string; acao_chave: string; acao_nome: string; permissao_id: string; }
export interface UsuarioPermissoesResponse { usuario_id: string; admin: boolean; permissoes: PermissaoMatrizItem[]; }

@Injectable({ providedIn: 'root' })
export class PermissaoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/permissoes`;

  listarMenus(): Observable<MenuPermissao[]> {
    return this.http.get<MenuPermissao[]>(`${this.base}/menus`);
  }

  listarAcoes(): Observable<AcaoPermissao[]> {
    return this.http.get<AcaoPermissao[]>(`${this.base}/acoes`);
  }

  listarPermissoesUsuario(usuarioId: string): Observable<UsuarioPermissoesResponse> {
    return this.http.get<UsuarioPermissoesResponse>(`${this.base}/usuarios/${usuarioId}`);
  }

  substituirPermissoes(usuarioId: string, permissoes: PermissaoItem[]): Observable<PermissaoMatrizItem[]> {
    return this.http.put<PermissaoMatrizItem[]>(`${this.base}/usuarios/${usuarioId}`, { permissoes });
  }
}
