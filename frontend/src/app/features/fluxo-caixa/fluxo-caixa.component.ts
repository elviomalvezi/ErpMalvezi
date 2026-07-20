import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { CurrencyPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, forkJoin } from 'rxjs';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { SelectModule } from 'primeng/select';
import { MultiSelectModule } from 'primeng/multiselect';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressBarModule } from 'primeng/progressbar';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { ContaBancariaService } from '../../core/services/conta-bancaria.service';
import { FluxoCaixaService } from '../../core/services/fluxo-caixa.service';
import { ContaBancaria, FluxoCaixaResponse } from '../../core/models';

interface PeriodoEnriquecido {
  periodo: string;
  mes: string;
  receitas_realizadas: number;
  despesas_realizadas: number;
  receitas_previstas: number;
  despesas_previstas: number;
  saldo_realizado: number;
  saldo_previsto: number;
  saldo_periodo: number;
  saldo_acumulado: number;
  temDados: boolean;
}

const MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];

@Component({
  selector: 'app-fluxo-caixa',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule, CurrencyPipe,
    ButtonModule, TableModule, SelectModule, MultiSelectModule,
    ToastModule, TooltipModule, ProgressBarModule,
  ],
  template: `
<p-toast />

<div class="page">
  <div class="page-header">
    <h1 class="page-title">Fluxo de Caixa</h1>
    <div class="header-controls">
      <div class="ano-nav">
        <p-button icon="pi pi-chevron-left" [text]="true" [rounded]="true" size="small"
          (onClick)="navegar(-1)" />
        <span class="ano-label">{{ ano() }}</span>
        <p-button icon="pi pi-chevron-right" [text]="true" [rounded]="true" size="small"
          (onClick)="navegar(1)" />
      </div>
      <p-select [options]="mesesOpts" optionLabel="label" optionValue="value"
        [(ngModel)]="filtroMes" placeholder="Todos os meses" class="filter-select mes-select"
        [showClear]="true" (onChange)="pesquisar()" />
      <p-multiselect
        [options]="empresaStore.empresas()" optionLabel="nome" optionValue="id"
        [(ngModel)]="filtroEmpresaIds" placeholder="Todas as empresas"
        selectedItemsLabel="{0} empresa(s)" [maxSelectedLabels]="1"
        class="filter-select" [filter]="false"
        (onChange)="onChangeEmpresas()" />
      <p-select [options]="contas()" optionLabel="nome" optionValue="id"
        [(ngModel)]="filtroContaId" placeholder="Selecione uma conta" class="filter-select"
        [showClear]="true" [disabled]="filtroEmpresaIds.length === 0 || contas().length === 0"
        (onChange)="pesquisar()" />
      <p-button icon="pi pi-refresh" [text]="true" [rounded]="true" [loading]="carregando()"
        pTooltip="Atualizar" (onClick)="pesquisar()" />
    </div>
  </div>

  @if (carregando()) {
    <p-progressbar mode="indeterminate" [style]="{'height':'3px'}" />
  }

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

  @if (resposta()) {
    <p-table [value]="periodosEnriquecidos()" size="small"
      class="p-datatable-gridlines fluxo-table" [class.loading-dim]="carregando()">
      <ng-template pTemplate="header">
        <tr>
          <th rowspan="2" style="width:80px;vertical-align:middle">Mês</th>
          <th colspan="3" style="text-align:center">Realizado</th>
          <th colspan="3" style="text-align:center">Previsto</th>
          <th rowspan="2" style="text-align:right;vertical-align:middle;min-width:110px">Saldo Período</th>
          <th rowspan="2" style="text-align:right;vertical-align:middle;min-width:110px">Saldo Acumulado</th>
        </tr>
        <tr>
          <th style="text-align:right;min-width:110px">Receitas</th>
          <th style="text-align:right;min-width:110px">Despesas</th>
          <th style="text-align:right;min-width:100px">Saldo</th>
          <th style="text-align:right;min-width:110px">Receitas</th>
          <th style="text-align:right;min-width:110px">Despesas</th>
          <th style="text-align:right;min-width:100px">Saldo</th>
        </tr>
      </ng-template>
      <ng-template pTemplate="body" let-p>
        <tr [class.row-sem-dados]="!p.temDados">
          <td class="mes-col">{{ p.mes }}</td>
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
            <td style="text-align:right">
              <strong [class.saldo-pos]="(kpi()!.receitasReal + kpi()!.receitasPrev - kpi()!.despesasReal - kpi()!.despesasPrev) >= 0"
                      [class.saldo-neg]="(kpi()!.receitasReal + kpi()!.receitasPrev - kpi()!.despesasReal - kpi()!.despesasPrev) < 0">
                {{ (kpi()!.receitasReal + kpi()!.receitasPrev - kpi()!.despesasReal - kpi()!.despesasPrev) | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
              </strong>
            </td>
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
    .ano-nav { display: flex; align-items: center; gap: 0.25rem; }
    .ano-label { font-size: 1.05rem; font-weight: 700; min-width: 60px; text-align: center; }
    :host ::ng-deep .filter-select { min-width: 160px; max-width: 280px; }
    :host ::ng-deep .mes-select { min-width: 130px; max-width: 160px; }
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
    .receita-cell { color: var(--p-green-700); }
    .despesa-cell { color: var(--p-red-700); }
    .receita-cell.prev { color: var(--p-green-400); }
    .despesa-cell.prev { color: var(--p-red-400); }
    .saldo-pos { color: var(--p-green-700); }
    .saldo-neg { color: var(--p-red-700); }
    .mes-col { font-weight: 600; }
    :host ::ng-deep .row-sem-dados td { opacity: 0.45; }
    :host ::ng-deep .fluxo-table.loading-dim { opacity: 0.5; pointer-events: none; transition: opacity 0.15s; }
    :host ::ng-deep .fluxo-table .p-datatable-footer .totais-row { background: var(--p-surface-100); font-weight: 600; }
    :host ::ng-deep .fluxo-table th { font-size: 0.8rem; }
    :host ::ng-deep .fluxo-table td { font-size: 0.875rem; }
  `],
})
export class FluxoCaixaComponent implements OnInit, OnDestroy {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly contaSvc = inject(ContaBancariaService);
  private readonly fluxoSvc = inject(FluxoCaixaService);
  private readonly msgSvc = inject(MessageService);

  private searchTimer?: ReturnType<typeof setTimeout>;
  private searchSub?: Subscription;

  protected readonly contas = signal<ContaBancaria[]>([]);
  protected readonly resposta = signal<FluxoCaixaResponse | null>(null);
  protected readonly carregando = signal(false);

  protected readonly ano = signal(new Date().getFullYear());
  protected filtroEmpresaIds: string[] = [];
  protected filtroContaId: string | null = null;
  protected filtroMes: number | null = null;

  protected readonly mesesOpts = MESES_ABREV.map((label, value) => ({ label, value }));

  protected readonly dataInicio = computed(() => {
    const a = this.ano();
    if (this.filtroMes !== null) {
      const m = String(this.filtroMes + 1).padStart(2, '0');
      return `${a}-${m}-01`;
    }
    return `${a}-01-01`;
  });

  protected readonly dataFim = computed(() => {
    const a = this.ano();
    if (this.filtroMes !== null) {
      const m = this.filtroMes + 1;
      const ultimo = new Date(a, m, 0).getDate();
      return `${a}-${String(m).padStart(2, '0')}-${String(ultimo).padStart(2, '0')}`;
    }
    return `${a}-12-31`;
  });

  protected readonly periodosEnriquecidos = computed<PeriodoEnriquecido[]>(() => {
    const resp = this.resposta();
    const anoAtual = this.ano();
    if (!resp) return [];

    const porMes = new Map<string, typeof resp.periodos[0]>();
    for (const p of resp.periodos) {
      porMes.set(String(p.periodo).substring(0, 7), p);
    }

    const meses = this.filtroMes !== null
      ? [this.filtroMes]
      : Array.from({ length: 12 }, (_, i) => i);

    let acumulado = Number(resp.saldo_inicial);
    return meses.map(m => {
      const chave = `${anoAtual}-${String(m + 1).padStart(2, '0')}`;
      const p = porMes.get(chave);
      const receitasReal = p ? Number(p.receitas_realizadas) : 0;
      const despesasReal = p ? Number(p.despesas_realizadas) : 0;
      const receitasPrev = p ? Number(p.receitas_previstas) : 0;
      const despesasPrev = p ? Number(p.despesas_previstas) : 0;
      const saldo_realizado = receitasReal - despesasReal;
      const saldo_previsto = receitasPrev - despesasPrev;
      const saldo_periodo = saldo_realizado + saldo_previsto;
      acumulado += saldo_periodo;
      return {
        periodo: `${chave}-01`,
        mes: `${MESES_ABREV[m]}/${anoAtual}`,
        receitas_realizadas: receitasReal,
        despesas_realizadas: despesasReal,
        receitas_previstas: receitasPrev,
        despesas_previstas: despesasPrev,
        saldo_realizado,
        saldo_previsto,
        saldo_periodo,
        saldo_acumulado: acumulado,
        temDados: !!(p && (receitasReal > 0 || despesasReal > 0 || receitasPrev > 0 || despesasPrev > 0)),
      };
    });
  });

  protected readonly kpi = computed(() => {
    const periodos = this.periodosEnriquecidos();
    const resp = this.resposta();
    if (!resp) return null;
    const saldoInicial = Number(resp.saldo_inicial);
    const receitasReal = periodos.reduce((s, p) => s + p.receitas_realizadas, 0);
    const despesasReal = periodos.reduce((s, p) => s + p.despesas_realizadas, 0);
    const receitasPrev = periodos.reduce((s, p) => s + p.receitas_previstas, 0);
    const despesasPrev = periodos.reduce((s, p) => s + p.despesas_previstas, 0);
    const saldoFinal = periodos.length > 0 ? periodos[periodos.length - 1].saldo_acumulado : saldoInicial;
    return { saldoInicial, receitasReal, despesasReal, receitasPrev, despesasPrev, saldoFinal };
  });

  ngOnInit(): void {
    const ativa = this.empresaStore.empresaAtiva();
    if (ativa) {
      this.filtroEmpresaIds = [ativa.id];
      this.carregarContas();
    }
    this.pesquisar();
  }

  ngOnDestroy(): void {
    clearTimeout(this.searchTimer);
    this.searchSub?.unsubscribe();
  }

  protected navegar(delta: number): void {
    this.ano.update(a => a + delta);
    this.pesquisar();
  }

  protected onChangeEmpresas(): void {
    this.filtroContaId = null;
    this.carregarContas();
    this.pesquisar();
  }

  private carregarContas(): void {
    if (this.filtroEmpresaIds.length === 0) {
      this.contas.set([]);
      return;
    }
    const obs = this.filtroEmpresaIds.map(id => this.contaSvc.listar({ empresaId: id }));
    forkJoin(obs).subscribe(resultados => {
      const todas = resultados.flat();
      const unicas = todas.filter((c, i) => todas.findIndex(x => x.id === c.id) === i);
      this.contas.set(unicas);
    });
  }

  protected pesquisar(): void {
    clearTimeout(this.searchTimer);
    this.carregando.set(true);
    this.searchTimer = setTimeout(() => {
      this.searchSub?.unsubscribe();
      this.searchSub = this.fluxoSvc.obter({
        dataInicio: this.dataInicio(),
        dataFim: this.dataFim(),
        empresaIds: this.filtroEmpresaIds,
        contaBancariaId: this.filtroContaId,
      }).subscribe({
        next: r => { this.resposta.set(r); this.carregando.set(false); },
        error: err => {
          this.carregando.set(false);
          this.msgSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao carregar fluxo de caixa.' });
        },
      });
    }, 250);
  }
}
