import { Component, inject, signal, effect } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { CardModule } from 'primeng/card';
import { SkeletonModule } from 'primeng/skeleton';
import { TagModule } from 'primeng/tag';
import { EmpresaStore } from '../../core/stores/empresa.store';
import { DashboardService } from '../../core/services/dashboard.service';
import { DashboardResponse } from '../../core/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [NgTemplateOutlet, CardModule, SkeletonModule, TagModule],
  template: `
    <div class="dashboard-page">
      <h1 class="page-title">Dashboard</h1>
      <p class="page-subtitle">
        {{ empresaStore.empresaAtiva()?.nome ?? 'Todas as empresas' }} —
        {{ mesAtual }}
      </p>

      @if (carregando()) {
        <div class="cards-grid">
          @for (_ of [1, 2, 3, 4]; track $index) {
            <p-card>
              <p-skeleton height="3rem" class="mb-2" />
              <p-skeleton width="60%" />
            </p-card>
          }
        </div>
      } @else if (dados()) {
        <div class="cards-grid">
          <p-card class="kpi-card kpi-saldo">
            <div class="kpi-label">Saldo em Conta</div>
            <div class="kpi-valor">{{ brl(dados()!.saldo_contas) }}</div>
          </p-card>
          <p-card class="kpi-card kpi-receita">
            <div class="kpi-label">Receitas Realizadas</div>
            <div class="kpi-valor">{{ brl(dados()!.kpi.receitas_realizadas) }}</div>
            <div class="kpi-sub">Previsto: {{ brl(dados()!.kpi.receitas_previstas) }}</div>
          </p-card>
          <p-card class="kpi-card kpi-despesa">
            <div class="kpi-label">Despesas Realizadas</div>
            <div class="kpi-valor">{{ brl(dados()!.kpi.despesas_realizadas) }}</div>
            <div class="kpi-sub">Previsto: {{ brl(dados()!.kpi.despesas_previstas) }}</div>
          </p-card>
          <p-card class="kpi-card" [class.kpi-positivo]="dados()!.kpi.saldo_realizado >= 0" [class.kpi-negativo]="dados()!.kpi.saldo_realizado < 0">
            <div class="kpi-label">Saldo do Mês</div>
            <div class="kpi-valor">{{ brl(dados()!.kpi.saldo_realizado) }}</div>
            <div class="kpi-sub">Previsto: {{ brl(dados()!.kpi.saldo_previsto) }}</div>
          </p-card>
        </div>

        <div class="listas-grid">
          <p-card header="Vence Hoje" class="lista-card">
            <ng-container *ngTemplateOutlet="listaLancamentos; context: { items: dados()!.a_vencer_hoje }" />
          </p-card>
          <p-card header="Vencidos" class="lista-card">
            <ng-container *ngTemplateOutlet="listaLancamentos; context: { items: dados()!.vencidos }" />
          </p-card>
          <p-card header="Próximos 7 Dias" class="lista-card">
            <ng-container *ngTemplateOutlet="listaLancamentos; context: { items: dados()!.proximos_vencimentos }" />
          </p-card>
        </div>
      } @else {
        <p class="empty-msg">Nenhuma informação disponível.</p>
      }
    </div>

    <ng-template #listaLancamentos let-items="items">
      @if (!items || items.length === 0) {
        <p class="empty-list">Nenhum lançamento.</p>
      } @else {
        <ul class="lancamentos-list">
          @for (item of items; track item.id) {
            <li class="lancamento-item">
              <div class="lancamento-desc">{{ item.descricao }}</div>
              <div class="lancamento-meta">
                <p-tag
                  [value]="item.tipo === 'RECEITA' ? 'Receita' : 'Despesa'"
                  [severity]="item.tipo === 'RECEITA' ? 'success' : 'danger'"
                />
                <span class="lancamento-valor" [class.receita]="item.tipo === 'RECEITA'" [class.despesa]="item.tipo !== 'RECEITA'">
                  {{ brl(item.valor) }}
                </span>
              </div>
            </li>
          }
        </ul>
      }
    </ng-template>
  `,
  styles: [
    `
      .dashboard-page {
        max-width: 1200px;
      }
      .page-title {
        margin: 0 0 0.25rem;
        font-size: 1.5rem;
        font-weight: 700;
      }
      .page-subtitle {
        margin: 0 0 1.5rem;
        color: var(--p-surface-500);
        font-size: 0.9rem;
      }
      .cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
      }
      .listas-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 1rem;
      }
      .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--p-surface-500);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.4rem;
      }
      .kpi-valor {
        font-size: 1.5rem;
        font-weight: 700;
      }
      .kpi-sub {
        font-size: 0.8rem;
        color: var(--p-surface-400);
        margin-top: 0.2rem;
      }
      :host ::ng-deep .kpi-saldo .kpi-valor {
        color: var(--p-primary-color);
      }
      :host ::ng-deep .kpi-receita .kpi-valor {
        color: var(--p-green-600);
      }
      :host ::ng-deep .kpi-despesa .kpi-valor {
        color: var(--p-red-600);
      }
      :host ::ng-deep .kpi-positivo .kpi-valor {
        color: var(--p-green-600);
      }
      :host ::ng-deep .kpi-negativo .kpi-valor {
        color: var(--p-red-600);
      }
      .lancamentos-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
      }
      .lancamento-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.4rem 0;
        border-bottom: 1px solid var(--p-surface-100);
        gap: 0.5rem;
      }
      .lancamento-item:last-child {
        border-bottom: none;
      }
      .lancamento-desc {
        font-size: 0.875rem;
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .lancamento-meta {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-shrink: 0;
      }
      .lancamento-valor {
        font-weight: 600;
        font-size: 0.875rem;
      }
      .lancamento-valor.receita {
        color: var(--p-green-600);
      }
      .lancamento-valor.despesa {
        color: var(--p-red-600);
      }
      .empty-list {
        color: var(--p-surface-400);
        font-size: 0.875rem;
        margin: 0;
      }
      .empty-msg {
        color: var(--p-surface-400);
      }
    `,
  ],
})
export class DashboardComponent {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly dashboardService = inject(DashboardService);

  protected readonly carregando = signal(true);
  protected readonly dados = signal<DashboardResponse | null>(null);

  protected readonly mesAtual = new Date().toLocaleDateString('pt-BR', {
    month: 'long',
    year: 'numeric',
  });

  constructor() {
    effect(() => {
      const empresa = this.empresaStore.empresaAtiva();
      this.carregar(empresa?.id);
    });
  }

  protected brl(valor: number): string {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  }

  private carregar(empresaId?: string): void {
    this.carregando.set(true);
    const hoje = new Date();
    const inicio = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}-01`;
    const ultimoDia = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0).getDate();
    const fim = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}-${String(ultimoDia).padStart(2, '0')}`;
    const referencia = hoje.toISOString().split('T')[0];

    this.dashboardService.obter(inicio, fim, referencia, empresaId).subscribe({
      next: (d) => {
        this.dados.set(d);
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }
}
