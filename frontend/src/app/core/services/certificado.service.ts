import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

export type TipoCertificado = 'e_cnpj' | 'e_cpf' | 'ssl' | 'outro';
export type StatusValidade = 'valido' | 'vencendo' | 'vencido' | 'sem_data';

export interface Certificado {
  id: string;
  empresa_id: string | null;
  nome_empresa: string | null;
  nome: string;
  tipo: TipoCertificado;
  titular: string | null;
  documento: string | null;
  emissor: string | null;
  numero_serie: string | null;
  validade_inicio: string | null;
  validade_fim: string | null;
  formato: string | null;
  arquivo_nome: string | null;
  tem_arquivo: boolean;
  tem_senha: boolean;
  observacoes: string | null;
  ativo: boolean;
  dias_para_vencer: number | null;
  status_validade: StatusValidade;
}

export interface CertificadoResumo {
  total: number;
  validos: number;
  vencendo: number;
  vencido: number;
}

export interface CertificadoManual {
  nome: string;
  tipo: TipoCertificado;
  empresa_id?: string | null;
  titular?: string | null;
  documento?: string | null;
  emissor?: string | null;
  numero_serie?: string | null;
  validade_inicio?: string | null;
  validade_fim?: string | null;
  observacoes?: string | null;
}

@Injectable({ providedIn: 'root' })
export class CertificadoService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/certificados`;

  listar(apenasAtivos = true): Observable<Certificado[]> {
    const params = new HttpParams().set('apenas_ativos', String(apenasAtivos));
    return this.http.get<Certificado[]>(this.base, { params });
  }

  resumo(): Observable<CertificadoResumo> {
    return this.http.get<CertificadoResumo>(`${this.base}/resumo`);
  }

  importar(form: FormData): Observable<Certificado> {
    return this.http.post<Certificado>(`${this.base}/importar`, form);
  }

  criarManual(data: CertificadoManual): Observable<Certificado> {
    return this.http.post<Certificado>(this.base, data);
  }

  atualizar(id: string, data: Partial<CertificadoManual>): Observable<Certificado> {
    return this.http.put<Certificado>(`${this.base}/${id}`, data);
  }

  inativar(id: string): Observable<Certificado> {
    return this.http.patch<Certificado>(`${this.base}/${id}/inativar`, {});
  }

  download(id: string): Observable<Blob> {
    return this.http.get(`${this.base}/${id}/download`, { responseType: 'blob' });
  }

  revelarSenha(id: string): Observable<{ senha: string }> {
    return this.http.get<{ senha: string }>(`${this.base}/${id}/senha`);
  }
}
