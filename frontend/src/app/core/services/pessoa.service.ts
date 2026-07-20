import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { StatusValidade, TipoCertificado } from './certificado.service';

export type TipoPessoa = 'interno' | 'externo';

export interface CertificadoResumoItem {
  id: string;
  nome: string;
  tipo: TipoCertificado;
  validade_fim: string | null;
  status_validade: StatusValidade;
  empresa_id: string | null;
  nome_empresa: string | null;
}

export interface Pessoa {
  id: string;
  nome: string;
  email: string | null;
  tipo: TipoPessoa;
  setor: string | null;
  empresa_externa: string | null;
  telefone: string | null;
  observacoes: string | null;
  ativo: boolean;
  total_certificados: number;
}

export interface PessoaDetalhe extends Pessoa {
  certificados: CertificadoResumoItem[];
}

export interface PessoaPayload {
  nome: string;
  email?: string | null;
  tipo: TipoPessoa;
  setor?: string | null;
  empresa_externa?: string | null;
  telefone?: string | null;
  observacoes?: string | null;
  certificado_ids?: string[];
}

@Injectable({ providedIn: 'root' })
export class PessoaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/pessoas`;
  private readonly certBase = `${environment.apiUrl}/certificados`;

  listar(apenasAtivos = true): Observable<Pessoa[]> {
    const params = new HttpParams().set('apenas_ativos', String(apenasAtivos));
    return this.http.get<Pessoa[]>(this.base, { params });
  }

  obter(id: string): Observable<PessoaDetalhe> {
    return this.http.get<PessoaDetalhe>(`${this.base}/${id}`);
  }

  criar(data: PessoaPayload): Observable<Pessoa> {
    return this.http.post<Pessoa>(this.base, data);
  }

  atualizar(id: string, data: Partial<PessoaPayload>): Observable<Pessoa> {
    return this.http.put<Pessoa>(`${this.base}/${id}`, data);
  }

  inativar(id: string): Observable<Pessoa> {
    return this.http.patch<Pessoa>(`${this.base}/${id}/inativar`, {});
  }

  definirCertificados(id: string, certificadoIds: string[]): Observable<PessoaDetalhe> {
    return this.http.put<PessoaDetalhe>(`${this.base}/${id}/certificados`, {
      certificado_ids: certificadoIds,
    });
  }

  // ── Lado do certificado ──────────────────────────────────────────────────
  pessoasDoCertificado(certId: string): Observable<Pessoa[]> {
    return this.http.get<Pessoa[]>(`${this.certBase}/${certId}/pessoas`);
  }

  associar(certId: string, pessoaId: string): Observable<void> {
    return this.http.post<void>(`${this.certBase}/${certId}/pessoas`, { pessoa_id: pessoaId });
  }

  desassociar(certId: string, pessoaId: string): Observable<void> {
    return this.http.delete<void>(`${this.certBase}/${certId}/pessoas/${pessoaId}`);
  }
}
