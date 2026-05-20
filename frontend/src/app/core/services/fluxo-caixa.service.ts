import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { FluxoCaixaResponse } from '../models';

@Injectable({ providedIn: 'root' })
export class FluxoCaixaService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/fluxo-caixa`;

  obter(opts: {
    dataInicio: string;
    dataFim: string;
    empresaId?: string | null;
    contaBancariaId?: string | null;
  }): Observable<FluxoCaixaResponse> {
    let params = new HttpParams()
      .set('data_inicio', opts.dataInicio)
      .set('data_fim', opts.dataFim);
    if (opts.empresaId) params = params.set('empresa_id', opts.empresaId);
    if (opts.contaBancariaId) params = params.set('conta_bancaria_id', opts.contaBancariaId);
    return this.http.get<FluxoCaixaResponse>(this.base, { params });
  }
}
