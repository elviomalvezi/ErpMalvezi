import { Component, inject, signal, computed, effect } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { SkeletonModule } from 'primeng/skeleton';
import { TagModule } from 'primeng/tag';
import { ChartModule } from 'primeng/chart';
import { ButtonModule } from 'primeng/button';
import { DatePickerModule } from 'primeng/datepicker';
import { forkJoin } from 'rxjs';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { DashboardService } from '../../core/services/dashboard.service';
import { DashboardResponse, GraficosResponse } from '../../core/models';

const MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [NgTemplateOutlet, RouterLink, FormsModule, CardModule, SkeletonModule, TagModule, ChartModule, ButtonModule, DatePickerModule],
  template: `
    <div class="dashboard-page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Dashboard</h1>
          <p class="page-subtitle">{{ empresaStore.empresaAtiva()?.nome ?? 'Todas as empresas' }}</p>
        </div>
        <div class="mes-nav">
          <p-button icon="pi pi-chevron-left" [text]="true" [rounded]="true" (onClick)="mesAnterior()" />
          <p-datepicker
            [(ngModel)]="mesAtual"
            view="month"
            dateFormat="MM/yy"
            [readonlyInput]="true"
            [showIcon]="true"
            icon="pi pi-calendar"
            placeholder="Selecione o mês"
          />
          <p-button icon="pi pi-chevron-right" [text]="true" [rounded]="true" (onClick)="proximoMes()" />
        </div>
        @if (dados()?.alertas_count) {
          <div class="alerta-banner">
            <i class="pi pi-exclamation-triangle"></i>
            <span>{{ dados()!.alertas_count }} conta(s) vencida(s) ou vencendo hoje</span>
            <a routerLink="/contas-pagar" class="alerta-link">Ver contas</a>
          </div>
        }
      </div>

      @if (carregando()) {
        <div class="cards-grid">
          @for (_ of [1,2,3,4]; track $index) {
            <p-card><p-skeleton height="3rem" class="mb-2" /><p-skeleton width="60%" /></p-card>
          }
        </div>
      } @else if (dados()) {
        <!-- KPIs -->
        <div class="cards-grid">
          <p-card class="kpi-card kpi-saldo">
            <div class="kpi-icon"><i class="pi pi-building-columns"></i></div>
            <div class="kpi-label">Saldo em Conta</div>
            <div class="kpi-valor">{{ brl(dados()!.saldo_contas) }}</div>
          </p-card>
          <p-card class="kpi-card kpi-receita">
            <div class="kpi-icon"><i class="pi pi-arrow-circle-down"></i></div>
            <div class="kpi-label">Receitas Realizadas</div>
            <div class="kpi-valor">{{ brl(dados()!.kpi.receitas_realizadas) }}</div>
            <div class="kpi-sub">Previsto: {{ brl(dados()!.kpi.receitas_previstas) }}</div>
          </p-card>
          <p-card class="kpi-card kpi-despesa">
            <div class="kpi-icon"><i class="pi pi-arrow-circle-up"></i></div>
            <div class="kpi-label">Despesas Realizadas</div>
            <div class="kpi-valor">{{ brl(dados()!.kpi.despesas_realizadas) }}</div>
            <div class="kpi-sub">Previsto: {{ brl(dados()!.kpi.despesas_previstas) }}</div>
          </p-card>
          <p-card class="kpi-card"
            [class.kpi-positivo]="dados()!.kpi.saldo_realizado >= 0"
            [class.kpi-negativo]="dados()!.kpi.saldo_realizado < 0">
            <div class="kpi-icon"><i class="pi pi-chart-bar"></i></div>
            <div class="kpi-label">Saldo do Mês</div>
            <div class="kpi-valor">{{ brl(dados()!.kpi.saldo_realizado) }}</div>
            <div class="kpi-sub">Previsto: {{ brl(dados()!.kpi.saldo_previsto) }}</div>
          </p-card>
        </div>

        <!-- Gráficos -->
        @if (graficos()) {
          <div class="graficos-grid">
            <p-card header="Receitas × Despesas (6 meses)" class="grafico-card">
              <p-chart type="bar" [data]="chartEvolucao()" [options]="optionsBar" height="220px" />
            </p-card>
            <p-card header="Despesas por Categoria" class="grafico-card">
              @if (graficos()!.despesas_por_categoria.length > 0) {
                <p-chart type="bar" [data]="chartBarCategoria()" [options]="optionsBarCategoria" height="220px" />
              } @else {
                <p class="sem-dados">Sem despesas realizadas no período.</p>
              }
            </p-card>
          </div>
        }

        <!-- Alertas -->
        <div class="listas-grid">
          <p-card header="Vence Hoje" class="lista-card">
            <ng-container *ngTemplateOutlet="listaLancamentos; context: { items: dados()!.a_vencer_hoje }" />
          </p-card>
          <p-card header="Vencidos" class="lista-card lista-card-danger">
            <ng-container *ngTemplateOutlet="listaLancamentos; context: { items: dados()!.vencidos }" />
          </p-card>
          <p-card header="Próximos 7 Dias" class="lista-card">
            <ng-container *ngTemplateOutlet="listaLancamentos; context: { items: dados()!.proximos_vencimentos }" />
          </p-card>
        </div>
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
                <p-tag [value]="item.tipo === 'RECEITA' ? 'Receita' : 'Despesa'"
                       [severity]="item.tipo === 'RECEITA' ? 'success' : 'danger'" />
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
  styles: [`
    .dashboard-page { max-width: 1200px; }
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem; }
    .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; }
    .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.9rem; }

    .alerta-banner {
      display: flex; align-items: center; gap: 0.6rem;
      background: var(--p-red-50); border: 1px solid var(--p-red-200);
      color: var(--p-red-700); padding: 0.6rem 1rem; border-radius: 8px;
      font-size: 0.875rem;
    }
    .alerta-banner i { color: var(--p-red-500); }
    .alerta-link { font-weight: 600; color: var(--p-red-700); text-decoration: underline; }

    .mes-nav { display: flex; align-items: center; gap: 0.25rem; }
    .cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
    .graficos-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
    .listas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }

    :host ::ng-deep .kpi-card .p-card-body { position: relative; }
    .kpi-icon { position: absolute; top: 1rem; right: 1rem; font-size: 1.4rem; opacity: 0.15; }
    .kpi-label { font-size: 0.75rem; font-weight: 700; color: var(--p-surface-500); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem; }
    .kpi-valor { font-size: 1.5rem; font-weight: 700; }
    .kpi-sub { font-size: 0.8rem; color: var(--p-surface-400); margin-top: 0.2rem; }
    :host ::ng-deep .kpi-saldo .kpi-valor { color: var(--p-primary-color); }
    :host ::ng-deep .kpi-receita .kpi-valor { color: var(--p-green-600); }
    :host ::ng-deep .kpi-despesa .kpi-valor { color: var(--p-red-600); }
    :host ::ng-deep .kpi-positivo .kpi-valor { color: var(--p-green-600); }
    :host ::ng-deep .kpi-negativo .kpi-valor { color: var(--p-red-600); }

    :host ::ng-deep .lista-card-danger .p-card-header { color: var(--p-red-600); }

    .lancamentos-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.5rem; }
    .lancamento-item { display: flex; justify-content: space-between; align-items: center; padding: 0.4rem 0; border-bottom: 1px solid var(--p-surface-100); gap: 0.5rem; }
    .lancamento-item:last-child { border-bottom: none; }
    .lancamento-desc { font-size: 0.875rem; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .lancamento-meta { display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0; }
    .lancamento-valor { font-weight: 600; font-size: 0.875rem; }
    .lancamento-valor.receita { color: var(--p-green-600); }
    .lancamento-valor.despesa { color: var(--p-red-600); }
    .empty-list { color: var(--p-surface-400); font-size: 0.875rem; margin: 0; }
    .sem-dados { color: var(--p-surface-400); font-size: 0.875rem; text-align: center; padding: 2rem; }

    @media (max-width: 768px) { .graficos-grid { grid-template-columns: 1fr; } }
  `],
})
export class DashboardComponent {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly dashboardService = inject(DashboardService);

  protected readonly carregando = signal(true);
  protected readonly dados = signal<DashboardResponse | null>(null);
  protected readonly graficos = signal<GraficosResponse | null>(null);
  protected mesAtual = signal(new Date());

  protected readonly mesTitulo = computed(() => {
    const d = this.mesAtual();
    return `${MESES[d.getMonth()]} / ${d.getFullYear()}`;
  });

  protected readonly optionsBar = {
    responsive: true,
    plugins: { legend: { position: 'bottom' } },
    scales: { y: { ticks: { callback: (v: number) => 'R$ ' + v.toLocaleString('pt-BR') } } },
  };

  protected readonly optionsBarCategoria = {
    indexAxis: 'y' as const,
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { callback: (v: number) => 'R$ ' + v.toLocaleString('pt-BR') } },
      y: { ticks: { font: { size: 11 } } },
    },
  };

  protected readonly chartEvolucao = computed(() => {
    const g = this.graficos();
    if (!g) return {};
    return {
      labels: g.evolucao_mensal.map(e => e.mes),
      datasets: [
        { label: 'Receitas', data: g.evolucao_mensal.map(e => e.receitas), backgroundColor: '#10b981' },
        { label: 'Despesas', data: g.evolucao_mensal.map(e => e.despesas), backgroundColor: '#ef4444' },
      ],
    };
  });

  protected readonly chartBarCategoria = computed(() => {
    const g = this.graficos();
    if (!g) return {};
    return {
      labels: g.despesas_por_categoria.map(c => c.categoria),
      datasets: [{
        label: 'Despesas',
        data: g.despesas_por_categoria.map(c => c.total),
        backgroundColor: '#ef4444',
      }],
    };
  });

  constructor() {
    effect(() => {
      const empresa = this.empresaStore.empresaAtiva();
      const mes = this.mesAtual();
      this.carregar(empresa?.id, mes);
    });
  }

  protected brl(valor: number): string {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  }

  protected mesAnterior(): void {
    const d = this.mesAtual();
    this.mesAtual.set(new Date(d.getFullYear(), d.getMonth() - 1, 1));
  }

  protected proximoMes(): void {
    const d = this.mesAtual();
    this.mesAtual.set(new Date(d.getFullYear(), d.getMonth() + 1, 1));
  }

  private toISODate(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  private carregar(empresaId?: string, mes: Date = new Date()): void {
    this.carregando.set(true);
    const inicio = this.toISODate(new Date(mes.getFullYear(), mes.getMonth(), 1));
    const fim = this.toISODate(new Date(mes.getFullYear(), mes.getMonth() + 1, 0));
    const hoje = new Date();
    const referencia = this.toISODate(
      mes.getFullYear() === hoje.getFullYear() && mes.getMonth() === hoje.getMonth()
        ? hoje
        : new Date(mes.getFullYear(), mes.getMonth() + 1, 0)
    );

    forkJoin({
      dashboard: this.dashboardService.obter(inicio, fim, referencia, empresaId),
      graficos: this.dashboardService.graficos(inicio, fim, referencia, empresaId),
    }).subscribe({
      next: ({ dashboard, graficos }) => {
        this.dados.set(dashboard);
        this.graficos.set(graficos);
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }
}
