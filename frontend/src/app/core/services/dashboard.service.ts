import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { DashboardResponse } from '../models';

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);

  obter(
    dataInicio: string,
    dataFim: string,
    dataReferencia: string,
    empresaId?: string,
  ): Observable<DashboardResponse> {
    let params = new HttpParams()
      .set('data_inicio', dataInicio)
      .set('data_fim', dataFim)
      .set('data_referencia', dataReferencia);
    if (empresaId) params = params.set('empresa_id', empresaId);
    return this.http.get<DashboardResponse>(`${environment.apiUrl}/dashboard`, { params });
  }
}
