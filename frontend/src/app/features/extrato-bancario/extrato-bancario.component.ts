import { Component, computed, effect, inject, signal, untracked } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { DatePickerModule } from 'primeng/datepicker';
import { DialogModule } from 'primeng/dialog';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { CategoriaService } from '../../core/services/categoria.service';
import { ContaBancariaService } from '../../core/services/conta-bancaria.service';
import { LancamentoService } from '../../core/services/lancamento.service';
import type {
  Categoria,
  ContaBancaria,
  ExtratoItem,
  ExtratoResponse,
  LancamentoBaixaCreate,
  LancamentoCreate,
} from '../../core/models';

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function primeiroDia(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function ultimoDia(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}

@Component({
  selector: 'app-extrato-bancario',
  standalone: true,
  providers: [MessageService],
  imports: [
    ReactiveFormsModule, FormsModule,
    ButtonModule, CardModule, TableModule, DialogModule, TagModule,
    ToastModule, SelectModule, DatePickerModule, InputNumberModule,
    InputTextModule, TooltipModule,
    CurrencyPipe, DatePipe,
  ],
  template: `
<p-toast />

@if (!empresaAtiva()) {
  <div class="sem-conta">
    <i class="pi pi-building sem-conta-icon"></i>
    <p>Selecione uma empresa para visualizar o extrato.</p>
  </div>
} @else {

<div class="page">
  <div class="page-header">
    <div class="header-left">
      <h1 class="page-title">Extrato Bancário</h1>
      <div class="filtros-header">
        <p-select
          [options]="contas()"
          [(ngModel)]="contaSelecionada"
          optionLabel="nome"
          placeholder="Selecione a conta..."
          [filter]="true"
          filterPlaceholder="Buscar conta..."
          appendTo="body"
          [showClear]="false"
          styleClass="conta-select"
          (onChange)="onContaMudou()"
        />
        <div class="month-nav">
          <p-button icon="pi pi-chevron-left" [text]="true" [rounded]="true" (onClick)="mesAnterior()" />
          <span class="mes-label">{{ nomeMes() }} {{ mesAtual().getFullYear() }}</span>
          <p-button icon="pi pi-chevron-right" [text]="true" [rounded]="true" (onClick)="proximoMes()" />
        </div>
      </div>
    </div>
    <div class="header-actions">
      @if (contaSelecionada) {
        <p-button label="Novo Lançamento" icon="pi pi-plus" (onClick)="abrirNovoLancamento()" />
      }
    </div>
  </div>

  @if (!contaSelecionada) {
    <div class="sem-conta">
      <i class="pi pi-credit-card sem-conta-icon"></i>
      <p>Selecione uma conta bancária para visualizar o extrato.</p>
    </div>
  } @else if (loading()) {
    <div class="carregando">
      <i class="pi pi-spin pi-spinner"></i> Carregando extrato...
    </div>
  } @else {
    <!-- Cards de resumo -->
    <div class="resumo-cards">
      <div class="card-resumo card-neutro">
        <span class="card-label">Saldo Anterior</span>
        <span class="card-valor">{{ extrato()?.saldo_anterior | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
      </div>
      <div class="card-resumo card-receita">
        <span class="card-label">Entradas</span>
        <span class="card-valor">{{ totalEntradas() | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
      </div>
      <div class="card-resumo card-despesa">
        <span class="card-label">Saídas</span>
        <span class="card-valor">{{ totalSaidas() | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
      </div>
      <div class="card-resumo" [class.card-positivo]="(extrato()?.saldo_final ?? 0) >= 0" [class.card-negativo]="(extrato()?.saldo_final ?? 0) < 0">
        <span class="card-label">Saldo Atual</span>
        <span class="card-valor">{{ extrato()?.saldo_final | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
      </div>
    </div>

    <!-- Tabela de lançamentos -->
    <p-table
      [value]="itens()"
      [loading]="loading()"
      [paginator]="true"
      [rows]="25"
      [rowsPerPageOptions]="[10, 25, 50, 100]"
      [showCurrentPageReport]="true"
      currentPageReportTemplate="{first}–{last} de {totalRecords}"
      size="small"
      styleClass="extrato-table"
    >
      <ng-template pTemplate="header">
        <tr>
          <th style="width:105px">Data</th>
          <th>Descrição</th>
          <th style="width:170px">Categoria</th>
          <th style="width:60px;text-align:center">Tipo</th>
          <th style="width:130px;text-align:right">Valor</th>
          <th style="width:130px;text-align:right">Saldo</th>
          <th style="width:100px;text-align:center">Status</th>
          <th style="width:90px;text-align:center">Ações</th>
        </tr>
      </ng-template>
      <ng-template pTemplate="body" let-item>
        <tr [class.linha-pendente]="item.lancamento.status === 'pendente'"
            [class.linha-cancelado]="item.lancamento.status === 'cancelado'">
          <td>{{ dataExibicao(item.lancamento) | date:'dd/MM/yyyy' }}</td>
          <td class="descricao-col">
            <span class="descricao-text" [title]="item.lancamento.descricao">{{ item.lancamento.descricao }}</span>
            @if (item.lancamento.numero_parcela) {
              <span class="parcela-tag">{{ item.lancamento.numero_parcela }}/{{ item.lancamento.total_parcelas }}</span>
            }
          </td>
          <td class="categoria-nome">{{ categoriaNome(item.lancamento.categoria_id) }}</td>
          <td style="text-align:center">
            @if (item.lancamento.tipo === 'RECEITA') {
              <i class="pi pi-arrow-down tipo-receita" pTooltip="Receita" tooltipPosition="top"></i>
            } @else {
              <i class="pi pi-arrow-up tipo-despesa" pTooltip="Despesa" tooltipPosition="top"></i>
            }
          </td>
          <td style="text-align:right">
            <span [class.valor-receita]="item.lancamento.tipo === 'RECEITA'"
                  [class.valor-despesa]="item.lancamento.tipo === 'DESPESA'">
              {{ item.lancamento.valor | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
            </span>
          </td>
          <td style="text-align:right">
            @if (item.lancamento.status === 'pago') {
              <span [class.valor-positivo]="item.saldo_apos >= 0" [class.valor-negativo]="item.saldo_apos < 0">
                {{ item.saldo_apos | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
              </span>
            } @else {
              <span class="saldo-pendente">—</span>
            }
          </td>
          <td style="text-align:center">
            <p-tag [value]="labelStatus(item.lancamento.status)"
                   [severity]="severidadeStatus(item.lancamento.status)"
                   styleClass="status-tag" />
          </td>
          <td style="text-align:center">
            <div class="acoes">
              @if (item.lancamento.status === 'pendente') {
                <p-button
                  icon="pi pi-check"
                  [text]="true"
                  severity="success"
                  size="small"
                  pTooltip="Efetivar"
                  tooltipPosition="top"
                  (onClick)="abrirEfetivar(item)"
                />
              }
            </div>
          </td>
        </tr>
      </ng-template>
      <ng-template pTemplate="emptymessage">
        <tr>
          <td colspan="8" style="text-align:center;padding:2rem;color:var(--p-surface-400)">
            Nenhum lançamento encontrado para este período.
          </td>
        </tr>
      </ng-template>
    </p-table>
  }
</div>

<!-- Dialog: Efetivar lançamento -->
<p-dialog
  header="Efetivar Lançamento"
  [(visible)]="dialogEfetivar"
  [modal]="true"
  [style]="{ width: '460px' }"
  (onHide)="fecharEfetivar()"
>
  @if (itemEfetivar()) {
    <div class="efetivar-info">
      <strong>{{ itemEfetivar()!.lancamento.descricao }}</strong>
      <span class="efetivar-valor" [class.valor-receita]="itemEfetivar()!.lancamento.tipo === 'RECEITA'"
            [class.valor-despesa]="itemEfetivar()!.lancamento.tipo === 'DESPESA'">
        {{ itemEfetivar()!.lancamento.valor | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
      </span>
    </div>
  }
  <form [formGroup]="formBaixa" class="dialog-form">
    <div class="field">
      <label>Valor pago *</label>
      <p-inputnumber formControlName="valor_pago" mode="currency" currency="BRL" locale="pt-BR"
        [minFractionDigits]="2" [maxFractionDigits]="2" styleClass="w-full" />
    </div>
    <div class="field">
      <label>Data do pagamento *</label>
      <p-datepicker formControlName="data_pagamento" dateFormat="dd/mm/yy"
        [showIcon]="true" styleClass="w-full" />
    </div>
    <div class="field">
      <label>Categoria *</label>
      <p-select
        formControlName="categoria_id"
        [options]="categorias()"
        optionLabel="nome"
        optionValue="id"
        placeholder="Selecione a categoria"
        [filter]="true"
        filterPlaceholder="Buscar categoria..."
        appendTo="body"
        styleClass="w-full"
      />
    </div>
  </form>
  <ng-template pTemplate="footer">
    <p-button label="Cancelar" [text]="true" (onClick)="fecharEfetivar()" />
    <p-button label="Efetivar" icon="pi pi-check" severity="success"
      [disabled]="formBaixa.invalid || salvandoBaixa()"
      [loading]="salvandoBaixa()"
      (onClick)="confirmarEfetivar()" />
  </ng-template>
</p-dialog>

<!-- Dialog: Novo lançamento -->
<p-dialog
  header="Novo Lançamento"
  [(visible)]="dialogNovo"
  [modal]="true"
  [style]="{ width: '520px' }"
  (onHide)="fecharNovo()"
>
  <form [formGroup]="formNovo" class="dialog-form">
    <div class="field">
      <label>Tipo *</label>
      <p-select
        formControlName="tipo"
        [options]="tiposLancamento"
        optionLabel="label"
        optionValue="value"
        styleClass="w-full"
      />
    </div>
    <div class="field">
      <label>Descrição *</label>
      <input pInputText formControlName="descricao" class="w-full" />
    </div>
    <div class="field">
      <label>Valor *</label>
      <p-inputnumber formControlName="valor" mode="currency" currency="BRL" locale="pt-BR"
        [minFractionDigits]="2" styleClass="w-full" />
    </div>
    <div class="fields-row">
      <div class="field">
        <label>Competência *</label>
        <p-datepicker formControlName="data_competencia" dateFormat="dd/mm/yy"
          [showIcon]="true" styleClass="w-full" />
      </div>
      <div class="field">
        <label>Vencimento *</label>
        <p-datepicker formControlName="data_vencimento" dateFormat="dd/mm/yy"
          [showIcon]="true" styleClass="w-full" />
      </div>
    </div>
    <div class="field">
      <label>Categoria</label>
      <p-select
        formControlName="categoria_id"
        [options]="categorias()"
        optionLabel="nome"
        optionValue="id"
        placeholder="Selecione a categoria"
        [filter]="true"
        filterPlaceholder="Buscar categoria..."
        appendTo="body"
        [showClear]="true"
        styleClass="w-full"
      />
    </div>
  </form>
  <ng-template pTemplate="footer">
    <p-button label="Cancelar" [text]="true" (onClick)="fecharNovo()" />
    <p-button label="Salvar" icon="pi pi-check"
      [disabled]="formNovo.invalid || salvandoNovo()"
      [loading]="salvandoNovo()"
      (onClick)="confirmarNovo()" />
  </ng-template>
</p-dialog>

}
  `,
  styles: [`
    .page { display: flex; flex-direction: column; gap: 1.25rem; padding: 1.5rem; height: 100%; }

    .page-header {
      display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem;
    }
    .header-left { display: flex; flex-direction: column; gap: 0.75rem; }
    .page-title { font-size: 1.4rem; font-weight: 700; margin: 0; color: var(--p-surface-800); }

    .filtros-header { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
    .conta-select { min-width: 260px; }

    .month-nav { display: flex; align-items: center; gap: 0.25rem; }
    .mes-label { font-size: 0.9rem; font-weight: 600; min-width: 140px; text-align: center; color: var(--p-surface-700); }

    .sem-conta {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      gap: 1rem; padding: 4rem; color: var(--p-surface-400); text-align: center;
    }
    .sem-conta-icon { font-size: 3rem; }
    .carregando { display: flex; align-items: center; gap: 0.5rem; padding: 2rem; color: var(--p-surface-500); }

    .resumo-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
    .card-resumo {
      background: var(--p-surface-0); border: 1px solid var(--p-surface-200);
      border-radius: 10px; padding: 1rem 1.25rem;
      display: flex; flex-direction: column; gap: 0.25rem;
    }
    .card-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--p-surface-400); }
    .card-valor { font-size: 1.15rem; font-weight: 700; color: var(--p-surface-800); }
    .card-neutro { border-left: 4px solid var(--p-surface-300); }
    .card-receita { border-left: 4px solid #22c55e; }
    .card-despesa { border-left: 4px solid #ef4444; }
    .card-positivo { border-left: 4px solid #22c55e; }
    .card-negativo { border-left: 4px solid #ef4444; }

    .descricao-col { max-width: 280px; }
    .descricao-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; display: block; }
    .parcela-tag { font-size: 0.7rem; color: var(--p-surface-400); margin-left: 0.25rem; }
    .categoria-nome { color: var(--p-surface-500); font-size: 0.83rem; }

    .tipo-receita { color: #22c55e; font-size: 1rem; }
    .tipo-despesa { color: #ef4444; font-size: 1rem; }

    .valor-receita { color: #22c55e; font-weight: 600; }
    .valor-despesa { color: #ef4444; font-weight: 600; }
    .valor-positivo { color: #22c55e; font-weight: 600; }
    .valor-negativo { color: #ef4444; font-weight: 600; }
    .saldo-pendente { color: var(--p-surface-300); }

    .linha-pendente td { opacity: 0.75; }
    .linha-cancelado td { opacity: 0.45; text-decoration: line-through; }

    .status-tag { font-size: 0.7rem !important; }
    .acoes { display: flex; align-items: center; justify-content: center; gap: 0.1rem; }

    .efetivar-info {
      display: flex; justify-content: space-between; align-items: center;
      padding: 0.75rem 0; margin-bottom: 0.75rem;
      border-bottom: 1px solid var(--p-surface-200);
      font-size: 0.95rem;
    }
    .efetivar-valor { font-weight: 700; font-size: 1rem; }

    .dialog-form { display: flex; flex-direction: column; gap: 1rem; padding-top: 0.5rem; }
    .field { display: flex; flex-direction: column; gap: 0.35rem; }
    .field label { font-size: 0.82rem; font-weight: 600; color: var(--p-surface-600); }
    .fields-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
    .w-full { width: 100%; }

    :host-context(.dark) .page-title { color: var(--p-surface-100); }
    :host-context(.dark) .card-resumo { background: #1e1e30; border-color: #2a2a3d; }
    :host-context(.dark) .card-label { color: #5a5a7a; }
    :host-context(.dark) .card-valor { color: var(--p-surface-100); }
    :host-context(.dark) .mes-label { color: var(--p-surface-200); }
  `],
})
export class ExtratoBancarioComponent {
  private readonly fb = inject(FormBuilder);
  private readonly empresaStore = inject(EmpresaStore);
  private readonly contaService = inject(ContaBancariaService);
  private readonly categoriaService = inject(CategoriaService);
  private readonly lancamentoService = inject(LancamentoService);
  private readonly toast = inject(MessageService);

  readonly empresaAtiva = computed(() => this.empresaStore.empresaAtiva());

  readonly contas = signal<ContaBancaria[]>([]);
  readonly categorias = signal<Categoria[]>([]);
  readonly extrato = signal<ExtratoResponse | null>(null);
  readonly loading = signal(false);
  readonly mesAtual = signal(new Date());

  contaSelecionada: ContaBancaria | null = null;

  dialogEfetivar = false;
  dialogNovo = false;
  itemEfetivar = signal<ExtratoItem | null>(null);
  salvandoBaixa = signal(false);
  salvandoNovo = signal(false);

  private categoriasMap = computed<Map<string, string>>(() => {
    const m = new Map<string, string>();
    for (const c of this.categorias()) m.set(c.id, c.nome);
    return m;
  });

  readonly nomeMes = computed(() => MESES[this.mesAtual().getMonth()]);
  readonly itens = computed(() => this.extrato()?.itens ?? []);

  readonly totalEntradas = computed(() =>
    this.itens()
      .filter(i => i.lancamento.status === 'pago' && i.lancamento.tipo === 'RECEITA')
      .reduce((s, i) => s + i.lancamento.valor_pago, 0)
  );
  readonly totalSaidas = computed(() =>
    this.itens()
      .filter(i => i.lancamento.status === 'pago' && i.lancamento.tipo === 'DESPESA')
      .reduce((s, i) => s + i.lancamento.valor_pago, 0)
  );

  readonly tiposLancamento = [
    { label: 'Receita', value: 'RECEITA' },
    { label: 'Despesa', value: 'DESPESA' },
  ];

  readonly formBaixa = this.fb.group({
    valor_pago: [0, [Validators.required, Validators.min(0.01)]],
    data_pagamento: [new Date(), Validators.required],
    categoria_id: ['', Validators.required],
  });

  readonly formNovo = this.fb.group({
    tipo: ['DESPESA', Validators.required],
    descricao: ['', [Validators.required, Validators.minLength(2)]],
    valor: [0, [Validators.required, Validators.min(0.01)]],
    data_competencia: [primeiroDia(new Date()), Validators.required],
    data_vencimento: [new Date(), Validators.required],
    categoria_id: [null as string | null],
  });

  constructor() {
    // Recarrega contas quando empresa ativa muda — filtra somente as da empresa
    effect(() => {
      const empresa = this.empresaAtiva();
      untracked(() => {
        this.contaSelecionada = null;
        this.extrato.set(null);
        if (empresa) {
          this.contaService.listar({ empresaId: empresa.id, apenasAtivas: true }).subscribe({
            next: (lista) => this.contas.set(lista),
            error: () => this.toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível carregar as contas.' }),
          });
        } else {
          this.contas.set([]);
        }
      });
    });

    this.categoriaService.listar().subscribe({
      next: (lista) => this.categorias.set(lista),
      error: () => {},
    });

    effect(() => {
      this.mesAtual();
      untracked(() => {
        if (this.contaSelecionada) this.carregarExtrato();
      });
    });
  }

  onContaMudou(): void {
    this.extrato.set(null);
    if (this.contaSelecionada) this.carregarExtrato();
  }

  carregarExtrato(): void {
    if (!this.contaSelecionada) return;
    this.loading.set(true);
    const mes = this.mesAtual();
    const inicio = isoDate(primeiroDia(mes));
    const fim = isoDate(ultimoDia(mes));
    this.lancamentoService.extrato({
      contaBancariaId: this.contaSelecionada.id,
      dataInicio: inicio,
      dataFim: fim,
    }).subscribe({
      next: (resp) => { this.extrato.set(resp); this.loading.set(false); },
      error: () => {
        this.loading.set(false);
        this.toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível carregar o extrato.' });
      },
    });
  }

  mesAnterior(): void {
    const d = this.mesAtual();
    this.mesAtual.set(new Date(d.getFullYear(), d.getMonth() - 1, 1));
  }

  proximoMes(): void {
    const d = this.mesAtual();
    this.mesAtual.set(new Date(d.getFullYear(), d.getMonth() + 1, 1));
  }

  dataExibicao(lct: { status: string; data_pagamento: string | null; data_vencimento: string }): string {
    return lct.status === 'pago' && lct.data_pagamento ? lct.data_pagamento : lct.data_vencimento;
  }

  categoriaNome(id: string | null): string {
    if (!id) return '—';
    return this.categoriasMap().get(id) ?? '—';
  }

  labelStatus(status: string): string {
    return status === 'pago' ? 'Pago' : status === 'pendente' ? 'Pendente' : 'Cancelado';
  }

  severidadeStatus(status: string): 'success' | 'warn' | 'danger' | 'secondary' {
    if (status === 'pago') return 'success';
    if (status === 'pendente') return 'warn';
    if (status === 'cancelado') return 'danger';
    return 'secondary';
  }

  // ── Efetivar ──────────────────────────────────────────────────────────────

  abrirEfetivar(item: ExtratoItem): void {
    this.itemEfetivar.set(item);
    const restante = item.lancamento.valor - item.lancamento.valor_pago;
    this.formBaixa.reset({
      valor_pago: restante > 0 ? restante : item.lancamento.valor,
      data_pagamento: new Date(),
      categoria_id: item.lancamento.categoria_id ?? '',
    });
    this.dialogEfetivar = true;
  }

  fecharEfetivar(): void {
    this.dialogEfetivar = false;
    this.itemEfetivar.set(null);
  }

  confirmarEfetivar(): void {
    if (this.formBaixa.invalid || !this.itemEfetivar()) return;
    const v = this.formBaixa.value;
    const data: LancamentoBaixaCreate = {
      valor_pago: v.valor_pago!,
      data_pagamento: isoDate(v.data_pagamento as Date),
      conta_bancaria_id: this.contaSelecionada!.id,
      categoria_id: v.categoria_id!,
    };
    this.salvandoBaixa.set(true);
    this.lancamentoService.registrarBaixa(this.itemEfetivar()!.lancamento.id, data).subscribe({
      next: () => {
        this.salvandoBaixa.set(false);
        this.fecharEfetivar();
        this.toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento efetivado.' });
        this.carregarExtrato();
      },
      error: (err) => {
        this.salvandoBaixa.set(false);
        const msg = err?.error?.detail ?? 'Erro ao efetivar lançamento.';
        this.toast.add({ severity: 'error', summary: 'Erro', detail: msg });
      },
    });
  }

  // ── Novo lançamento ───────────────────────────────────────────────────────

  abrirNovoLancamento(): void {
    this.formNovo.reset({
      tipo: 'DESPESA',
      descricao: '',
      valor: 0,
      data_competencia: primeiroDia(this.mesAtual()),
      data_vencimento: new Date(),
      categoria_id: null,
    });
    this.dialogNovo = true;
  }

  fecharNovo(): void {
    this.dialogNovo = false;
  }

  confirmarNovo(): void {
    if (this.formNovo.invalid || !this.contaSelecionada) return;
    const v = this.formNovo.value;

    // Encontrar empresa_id da conta selecionada
    const conta = this.contaSelecionada;
    const data: LancamentoCreate = {
      empresa_id: conta.empresa_id,
      tipo: v.tipo as 'RECEITA' | 'DESPESA',
      descricao: v.descricao!,
      valor: v.valor!,
      data_competencia: isoDate(v.data_competencia as Date),
      data_vencimento: isoDate(v.data_vencimento as Date),
      conta_bancaria_id: conta.id,
      categoria_id: v.categoria_id ?? null,
    };
    this.salvandoNovo.set(true);
    this.lancamentoService.criar(data).subscribe({
      next: () => {
        this.salvandoNovo.set(false);
        this.fecharNovo();
        this.toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento criado.' });
        this.carregarExtrato();
      },
      error: (err) => {
        this.salvandoNovo.set(false);
        const msg = err?.error?.detail ?? 'Erro ao criar lançamento.';
        this.toast.add({ severity: 'error', summary: 'Erro', detail: msg });
      },
    });
  }
}
