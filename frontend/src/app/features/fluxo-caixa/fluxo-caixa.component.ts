import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { ContaBancariaService } from '../../core/services/conta-bancaria.service';
import { FluxoCaixaService } from '../../core/services/fluxo-caixa.service';
import { ContaBancaria, FluxoCaixaResponse } from '../../core/models';

const MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
               'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];

interface PeriodoEnriquecido {
  periodo: string;
  receitas_realizadas: number;
  despesas_realizadas: number;
  receitas_previstas: number;
  despesas_previstas: number;
  saldo_realizado: number;
  saldo_previsto: number;
  saldo_periodo: number;
  saldo_acumulado: number;
}

@Component({
  selector: 'app-fluxo-caixa',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule, CurrencyPipe, DatePipe,
    ButtonModule, TableModule, SelectModule, TagModule, ToastModule, TooltipModule,
  ],
  template: `
<p-toast />

<div class="page">
  <div class="page-header">
    <h1 class="page-title">Fluxo de Caixa</h1>
    <div class="header-controls">
      <div class="mes-nav">
        <p-button icon="pi pi-chevron-left" [text]="true" [rounded]="true" size="small"
          (onClick)="navegar(-1)" />
        <span class="mes-label">{{ labelMes() }}</span>
        <p-button icon="pi pi-chevron-right" [text]="true" [rounded]="true" size="small"
          (onClick)="navegar(1)" />
      </div>
      <p-select [options]="empresaStore.empresas()" optionLabel="nome" optionValue="id"
        [(ngModel)]="filtroEmpresaId" placeholder="Todas as empresas" class="filter-select"
        [showClear]="true" (onChange)="pesquisar()" />
      <p-select [options]="contas()" optionLabel="nome" optionValue="id"
        [(ngModel)]="filtroContaId" placeholder="Todas as contas" class="filter-select"
        [showClear]="true" (onChange)="pesquisar()" />
      <p-button icon="pi pi-refresh" [text]="true" [rounded]="true" [loading]="carregando()"
        pTooltip="Atualizar" (onClick)="pesquisar()" />
    </div>
  </div>

  @if (kpi()) {
    <div class="kpi-cards">
      <div class="kpi-card">
        <span class="kpi-label">Saldo Inicial</span>
        <span class="kpi-value">{{ kpi()!.saldoInicial | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
      </div>
      <div class="kpi-card receita">
        <span class="kpi-label">Receitas Realizadas</span>
        <span class="kpi-value">{{ kpi()!.receitasReal | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
        <span class="kpi-sub">+ {{ kpi()!.receitasPrev | currency:'BRL':'symbol':'1.2-2':'pt-BR' }} previsto</span>
      </div>
      <div class="kpi-card despesa">
        <span class="kpi-label">Despesas Realizadas</span>
        <span class="kpi-value">{{ kpi()!.despesasReal | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
        <span class="kpi-sub">+ {{ kpi()!.despesasPrev | currency:'BRL':'symbol':'1.2-2':'pt-BR' }} previsto</span>
      </div>
      <div class="kpi-card" [class.saldo-pos]="kpi()!.saldoFinal >= 0" [class.saldo-neg]="kpi()!.saldoFinal < 0">
        <span class="kpi-label">Saldo Final Projetado</span>
        <span class="kpi-value">{{ kpi()!.saldoFinal | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
      </div>
    </div>
  }

  @if (carregando() && !resposta()) {
    <div class="loading-msg"><i class="pi pi-spin pi-spinner"></i> Carregando...</div>
  }

  @if (resposta() && periodosEnriquecidos().length === 0) {
    <div class="empty-msg">Nenhum movimento no período selecionado.</div>
  }

  @if (periodosEnriquecidos().length > 0) {
    <p-table [value]="periodosEnriquecidos()" size="small"
      class="p-datatable-gridlines fluxo-table">
      <ng-template pTemplate="header">
        <tr>
          <th rowspan="2" style="width:100px;vertical-align:middle">Período</th>
          <th colspan="3" style="text-align:center;border-bottom:0">Realizado</th>
          <th colspan="3" style="text-align:center;border-bottom:0">Previsto</th>
          <th rowspan="2" style="text-align:right;vertical-align:middle">Saldo Período</th>
          <th rowspan="2" style="text-align:right;vertical-align:middle">Saldo Acumulado</th>
        </tr>
        <tr>
          <th style="text-align:right">Receitas</th>
          <th style="text-align:right">Despesas</th>
          <th style="text-align:right">Saldo</th>
          <th style="text-align:right">Receitas</th>
          <th style="text-align:right">Despesas</th>
          <th style="text-align:right">Saldo</th>
        </tr>
      </ng-template>
      <ng-template pTemplate="body" let-p>
        <tr>
          <td>{{ p.periodo | date:'dd/MM/yyyy' }}</td>
          <td style="text-align:right" class="receita-cell">
            {{ p.receitas_realizadas > 0 ? (p.receitas_realizadas | currency:'BRL':'symbol':'1.2-2':'pt-BR') : '—' }}
          </td>
          <td style="text-align:right" class="despesa-cell">
            {{ p.despesas_realizadas > 0 ? (p.despesas_realizadas | currency:'BRL':'symbol':'1.2-2':'pt-BR') : '—' }}
          </td>
          <td style="text-align:right" [class.saldo-pos]="p.saldo_realizado > 0" [class.saldo-neg]="p.saldo_realizado < 0">
            {{ p.saldo_realizado !== 0 ? (p.saldo_realizado | currency:'BRL':'symbol':'1.2-2':'pt-BR') : '—' }}
          </td>
          <td style="text-align:right" class="receita-cell prev">
            {{ p.receitas_previstas > 0 ? (p.receitas_previstas | currency:'BRL':'symbol':'1.2-2':'pt-BR') : '—' }}
          </td>
          <td style="text-align:right" class="despesa-cell prev">
            {{ p.despesas_previstas > 0 ? (p.despesas_previstas | currency:'BRL':'symbol':'1.2-2':'pt-BR') : '—' }}
          </td>
          <td style="text-align:right" [class.saldo-pos]="p.saldo_previsto > 0" [class.saldo-neg]="p.saldo_previsto < 0">
            {{ p.saldo_previsto !== 0 ? (p.saldo_previsto | currency:'BRL':'symbol':'1.2-2':'pt-BR') : '—' }}
          </td>
          <td style="text-align:right;font-weight:500"
              [class.saldo-pos]="p.saldo_periodo > 0" [class.saldo-neg]="p.saldo_periodo < 0">
            {{ p.saldo_periodo !== 0 ? (p.saldo_periodo | currency:'BRL':'symbol':'1.2-2':'pt-BR') : '—' }}
          </td>
          <td style="text-align:right;font-weight:600"
              [class.saldo-pos]="p.saldo_acumulado >= 0" [class.saldo-neg]="p.saldo_acumulado < 0">
            {{ p.saldo_acumulado | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
          </td>
        </tr>
      </ng-template>
      <ng-template pTemplate="footer">
        @if (kpi()) {
          <tr class="totais-row">
            <td><strong>Total</strong></td>
            <td style="text-align:right" class="receita-cell"><strong>{{ kpi()!.receitasReal | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong></td>
            <td style="text-align:right" class="despesa-cell"><strong>{{ kpi()!.despesasReal | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong></td>
            <td style="text-align:right"><strong>{{ (kpi()!.receitasReal - kpi()!.despesasReal) | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong></td>
            <td style="text-align:right" class="receita-cell prev"><strong>{{ kpi()!.receitasPrev | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong></td>
            <td style="text-align:right" class="despesa-cell prev"><strong>{{ kpi()!.despesasPrev | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong></td>
            <td style="text-align:right"><strong>{{ (kpi()!.receitasPrev - kpi()!.despesasPrev) | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong></td>
            <td style="text-align:right"><strong>{{ (kpi()!.receitasReal + kpi()!.receitasPrev - kpi()!.despesasReal - kpi()!.despesasPrev) | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong></td>
            <td style="text-align:right" [class.saldo-pos]="kpi()!.saldoFinal >= 0" [class.saldo-neg]="kpi()!.saldoFinal < 0">
              <strong>{{ kpi()!.saldoFinal | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</strong>
            </td>
          </tr>
        }
      </ng-template>
    </p-table>
  }
</div>
  `,
  styles: [`
    .page { padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
    .page-header { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
    .page-title { margin: 0; font-size: 1.4rem; font-weight: 700; flex: 1; }
    .header-controls { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .mes-nav { display: flex; align-items: center; gap: 0.25rem; }
    .mes-label { font-size: 0.95rem; font-weight: 600; min-width: 140px; text-align: center; }
    :host ::ng-deep .filter-select { min-width: 180px; }
    .kpi-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
    .kpi-card { background: var(--p-surface-0); border: 1px solid var(--p-surface-200);
      border-radius: 10px; padding: 1rem 1.25rem; display: flex; flex-direction: column; gap: 0.2rem; }
    .kpi-label { font-size: 0.75rem; color: var(--p-surface-500); font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
    .kpi-value { font-size: 1.2rem; font-weight: 700; color: var(--p-surface-800); }
    .kpi-sub { font-size: 0.75rem; color: var(--p-surface-400); }
    .kpi-card.receita { border-left: 3px solid var(--p-green-400); }
    .kpi-card.despesa { border-left: 3px solid var(--p-red-400); }
    .kpi-card.saldo-pos { border-left: 3px solid var(--p-green-500); }
    .kpi-card.saldo-neg { border-left: 3px solid var(--p-red-500); }
    .loading-msg, .empty-msg { text-align: center; padding: 2rem; color: var(--p-surface-400); }
    .receita-cell { color: var(--p-green-700); }
    .despesa-cell { color: var(--p-red-700); }
    .receita-cell.prev { color: var(--p-green-400); }
    .despesa-cell.prev { color: var(--p-red-400); }
    .saldo-pos { color: var(--p-green-700); }
    .saldo-neg { color: var(--p-red-700); }
    :host ::ng-deep .fluxo-table .p-datatable-footer .totais-row { background: var(--p-surface-100); font-weight: 600; }
    :host ::ng-deep .fluxo-table th { font-size: 0.8rem; }
    :host ::ng-deep .fluxo-table td { font-size: 0.875rem; }
  `],
})
export class FluxoCaixaComponent implements OnInit {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly contaSvc = inject(ContaBancariaService);
  private readonly fluxoSvc = inject(FluxoCaixaService);
  private readonly msgSvc = inject(MessageService);

  protected readonly contas = signal<ContaBancaria[]>([]);
  protected readonly resposta = signal<FluxoCaixaResponse | null>(null);
  protected readonly carregando = signal(false);

  protected readonly mes = signal(new Date().getMonth());
  protected readonly ano = signal(new Date().getFullYear());
  protected filtroEmpresaId: string | null = null;
  protected filtroContaId: string | null = null;

  protected readonly dataInicio = computed(() => {
    const d = new Date(this.ano(), this.mes(), 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
  });
  protected readonly dataFim = computed(() => {
    const d = new Date(this.ano(), this.mes() + 1, 0);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  });
  protected readonly labelMes = computed(() => `${MESES[this.mes()]} ${this.ano()}`);

  protected readonly periodosEnriquecidos = computed<PeriodoEnriquecido[]>(() => {
    const resp = this.resposta();
    if (!resp) return [];
    let acumulado = Number(resp.saldo_inicial);
    return resp.periodos.map(p => {
      const saldo_realizado = Number(p.receitas_realizadas) - Number(p.despesas_realizadas);
      const saldo_previsto = Number(p.receitas_previstas) - Number(p.despesas_previstas);
      const saldo_periodo = saldo_realizado + saldo_previsto;
      acumulado += saldo_periodo;
      return {
        periodo: p.periodo,
        receitas_realizadas: Number(p.receitas_realizadas),
        despesas_realizadas: Number(p.despesas_realizadas),
        receitas_previstas: Number(p.receitas_previstas),
        despesas_previstas: Number(p.despesas_previstas),
        saldo_realizado,
        saldo_previsto,
        saldo_periodo,
        saldo_acumulado: acumulado,
      };
    });
  });

  protected readonly kpi = computed(() => {
    const resp = this.resposta();
    if (!resp) return null;
    const saldoInicial = Number(resp.saldo_inicial);
    const receitasReal = resp.periodos.reduce((s, p) => s + Number(p.receitas_realizadas), 0);
    const despesasReal = resp.periodos.reduce((s, p) => s + Number(p.despesas_realizadas), 0);
    const receitasPrev = resp.periodos.reduce((s, p) => s + Number(p.receitas_previstas), 0);
    const despesasPrev = resp.periodos.reduce((s, p) => s + Number(p.despesas_previstas), 0);
    const periodos = this.periodosEnriquecidos();
    const saldoFinal = periodos.length > 0
      ? periodos[periodos.length - 1].saldo_acumulado
      : saldoInicial;
    return { saldoInicial, receitasReal, despesasReal, receitasPrev, despesasPrev, saldoFinal };
  });

  ngOnInit(): void {
    this.contaSvc.listar().subscribe(c => this.contas.set(c));
    this.pesquisar();
  }

  protected navegar(delta: number): void {
    let m = this.mes() + delta;
    let a = this.ano();
    if (m < 0) { m = 11; a--; }
    if (m > 11) { m = 0; a++; }
    this.mes.set(m);
    this.ano.set(a);
    this.pesquisar();
  }

  protected pesquisar(): void {
    this.carregando.set(true);
    this.fluxoSvc.obter({
      dataInicio: this.dataInicio(),
      dataFim: this.dataFim(),
      empresaId: this.filtroEmpresaId,
      contaBancariaId: this.filtroContaId,
    }).subscribe({
      next: r => { this.resposta.set(r); this.carregando.set(false); },
      error: err => {
        this.carregando.set(false);
        this.msgSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao carregar fluxo de caixa.' });
      },
    });
  }
}
