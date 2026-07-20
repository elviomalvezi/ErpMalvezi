import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface DreLinha {
  categoria_id: string;
  categoria_nome: string;
  nivel: number;
  parent_id: string | null;
  total_atual: number;
  total_anterior: number;
  variacao_pct: number | null;
}

export interface DreResponse {
  mes_referencia: string;
  mes_anterior: string;
  empresa_nome: string | null;
  receitas: DreLinha[];
  total_receitas_atual: number;
  total_receitas_anterior: number;
  despesas: DreLinha[];
  total_despesas_atual: number;
  total_despesas_anterior: number;
  resultado_atual: number;
  resultado_anterior: number;
}

export interface BuscaResult {
  lancamentos: any[];
  contatos: any[];
  categorias: { id: string; nome: string; tipo: string }[];
}

@Injectable({ providedIn: 'root' })
export class RelatorioService {
  private readonly http = inject(HttpClient);
  private readonly api = environment.apiUrl;

  dre(mesReferencia: string, empresaId?: string): Observable<DreResponse> {
    let params = new HttpParams().set('mes_referencia', mesReferencia);
    if (empresaId) params = params.set('empresa_id', empresaId);
    return this.http.get<DreResponse>(`${this.api}/relatorios/dre`, { params });
  }

  enviarNotificacoes(): Observable<{ enviados: number; mensagem: string }> {
    return this.http.post<{ enviados: number; mensagem: string }>(
      `${this.api}/notificacoes/enviar-vencimentos`,
      {},
    );
  }

  buscaGlobal(q: string): Observable<BuscaResult> {
    const params = new HttpParams().set('q', q);
    return this.http.get<BuscaResult>(`${this.api}/busca`, { params });
  }
}
