import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { SkeletonModule } from 'primeng/skeleton';
import { SelectModule } from 'primeng/select';
import { CardModule } from 'primeng/card';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { LancamentoService } from '../../core/services/lancamento.service';
import { ExportacaoService } from '../../core/services/exportacao.service';
import { Lancamento } from '../../core/models';

interface GrupoCliente {
  nome: string;
  lancamentos: Lancamento[];
  total: number;
  diasAtraso: number;
}

@Component({
  selector: 'app-inadimplencia',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule, CurrencyPipe, DatePipe,
    TableModule, ButtonModule, TagModule, ToastModule,
    TooltipModule, SkeletonModule, SelectModule, CardModule,
  ],
  template: `
    <p-toast />
    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title"><i class="pi pi-exclamation-circle icon-danger"></i> Inadimplência</h1>
          <p class="page-subtitle">Contas a receber vencidas agrupadas por cliente</p>
        </div>
        <div class="header-actions">
          <p-button icon="pi pi-file-excel" [text]="true" severity="success"
            pTooltip="Exportar Excel" (onClick)="exportarExcel()"
            [disabled]="todos().length === 0" />
          <p-button icon="pi pi-refresh" [text]="true" [loading]="carregando()"
            pTooltip="Atualizar" (onClick)="carregar()" />
        </div>
      </div>

      <!-- KPIs -->
      @if (!carregando() && grupos().length > 0) {
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Total em Atraso</div>
            <div class="kpi-valor danger">{{ totalGeral() | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Clientes Inadimplentes</div>
            <div class="kpi-valor">{{ grupos().length }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Lançamentos Vencidos</div>
            <div class="kpi-valor">{{ todos().length }}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Maior Atraso</div>
            <div class="kpi-valor danger">{{ maiorAtraso() }} dias</div>
          </div>
        </div>
      }

      @if (carregando()) {
        <p-skeleton height="200px" />
      } @else if (grupos().length === 0) {
        <div class="empty-state">
          <i class="pi pi-check-circle"></i>
          <p>Nenhuma conta em atraso. Ótimo!</p>
        </div>
      } @else {
        @for (grupo of grupos(); track grupo.nome) {
          <div class="grupo-card">
            <div class="grupo-header">
              <div class="grupo-info">
                <i class="pi pi-user"></i>
                <strong>{{ grupo.nome || 'Sem cliente' }}</strong>
                <span class="grupo-count">{{ grupo.lancamentos.length }} lançamento(s)</span>
              </div>
              <div class="grupo-total">
                <span class="atraso-badge">Maior atraso: {{ grupo.diasAtraso }} dias</span>
                <strong class="total-danger">{{ grupo.total | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong>
              </div>
            </div>

            <p-table [value]="grupo.lancamentos" class="p-datatable-sm grupo-table">
              <ng-template pTemplate="header">
                <tr>
                  <th>Descrição</th>
                  <th style="width:110px">Vencimento</th>
                  <th style="width:80px">Atraso</th>
                  <th style="width:110px" class="text-right">Valor</th>
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-lct>
                <tr>
                  <td>{{ lct.descricao }}</td>
                  <td>{{ lct.data_vencimento | date:'dd/MM/yyyy' }}</td>
                  <td>
                    <p-tag [value]="calcDias(lct.data_vencimento) + ' dias'"
                      [severity]="calcDias(lct.data_vencimento) > 30 ? 'danger' : 'warn'" />
                  </td>
                  <td class="text-right valor-danger">{{ lct.valor | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td>
                </tr>
              </ng-template>
            </p-table>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    .page { max-width: 1100px; }
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
    .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; }
    .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.875rem; }
    .header-actions { display: flex; gap: 0.5rem; }
    .icon-danger { color: var(--p-red-500); }

    .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    .kpi-card { background: var(--p-surface-0); border: 1px solid var(--p-surface-200); border-radius: 10px; padding: 1.2rem; }
    .kpi-label { font-size: 0.75rem; font-weight: 700; color: var(--p-surface-500); text-transform: uppercase; margin-bottom: 0.4rem; }
    .kpi-valor { font-size: 1.5rem; font-weight: 700; }
    .kpi-valor.danger { color: var(--p-red-600); }

    .grupo-card { background: var(--p-surface-0); border: 1px solid var(--p-surface-200); border-radius: 10px; margin-bottom: 1rem; overflow: hidden; }
    .grupo-header { display: flex; justify-content: space-between; align-items: center; padding: 0.9rem 1.2rem; background: var(--p-surface-50); border-bottom: 1px solid var(--p-surface-200); }
    .grupo-info { display: flex; align-items: center; gap: 0.6rem; }
    .grupo-count { font-size: 0.8rem; color: var(--p-surface-400); }
    .grupo-total { display: flex; align-items: center; gap: 1rem; }
    .atraso-badge { font-size: 0.8rem; color: var(--p-orange-600); background: var(--p-orange-50); padding: 0.2rem 0.6rem; border-radius: 4px; }
    .total-danger { color: var(--p-red-600); font-size: 1.1rem; }

    :host ::ng-deep .grupo-table .p-datatable-tbody > tr > td { padding: 0.4rem 0.75rem; }
    .text-right { text-align: right !important; }
    .valor-danger { color: var(--p-red-600); font-weight: 600; }

    .empty-state { text-align: center; padding: 4rem; color: var(--p-surface-400); }
    .empty-state i { font-size: 3rem; color: var(--p-green-400); display: block; margin-bottom: 1rem; }
  `],
})
export class InadimplenciaComponent implements OnInit {
  private readonly lancamentoSvc = inject(LancamentoService);
  private readonly exportSvc = inject(ExportacaoService);
  private readonly messageSvc = inject(MessageService);
  protected readonly empresaStore = inject(EmpresaStore);

  protected readonly todos = signal<Lancamento[]>([]);
  protected readonly carregando = signal(false);

  protected readonly grupos = computed<GrupoCliente[]>(() => {
    const hoje = new Date();
    const map = new Map<string, Lancamento[]>();
    this.todos().forEach(lct => {
      const chave = lct.contato_id ?? '__sem_cliente__';
      if (!map.has(chave)) map.set(chave, []);
      map.get(chave)!.push(lct);
    });

    return Array.from(map.entries())
      .map(([, lancamentos]) => {
        const total = lancamentos.reduce((s, l) => s + Number(l.valor), 0);
        const diasAtraso = Math.max(...lancamentos.map(l => this.calcDias(l.data_vencimento)));
        const nome = (lancamentos[0] as any).contato_nome ?? 'Sem cliente';
        return { nome, lancamentos, total, diasAtraso };
      })
      .sort((a, b) => b.total - a.total);
  });

  protected readonly totalGeral = computed(() =>
    this.grupos().reduce((s, g) => s + g.total, 0)
  );

  protected readonly maiorAtraso = computed(() =>
    this.grupos().length ? Math.max(...this.grupos().map(g => g.diasAtraso)) : 0
  );

  ngOnInit(): void { this.carregar(); }

  protected carregar(): void {
    const empresaId = this.empresaStore.empresaAtiva()?.id;
    this.carregando.set(true);
    const hoje = new Date().toISOString().split('T')[0];
    this.lancamentoSvc.listar({
      empresaId,
      tipo: 'RECEITA',
      status: 'PENDENTE',
      dataFim: hoje,
    }).subscribe({
      next: (data) => {
        this.todos.set(data.filter(l => l.data_vencimento < hoje));
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }

  protected calcDias(dataVencimento: string): number {
    const diff = new Date().getTime() - new Date(dataVencimento).getTime();
    return Math.max(0, Math.floor(diff / 86400000));
  }

  protected exportarExcel(): void {
    this.exportSvc.exportarExcel(this.todos(), 'inadimplencia');
  }
}
