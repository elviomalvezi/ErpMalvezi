import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { TooltipModule } from 'primeng/tooltip';
import { TextareaModule } from 'primeng/textarea';
import { ProgressBarModule } from 'primeng/progressbar';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { ContaBancariaService } from '../../core/services/conta-bancaria.service';
import { ConciliacaoService } from '../../core/services/conciliacao.service';
import { CategoriaService } from '../../core/services/categoria.service';
import {
  Categoria,
  ContaBancaria,
  CriarLancamentoConciliacaoRequest,
  ImportacaoBancariaResponse,
  SugestaoMatchResponse,
  TransacaoBancariaResponse,
} from '../../core/models';

@Component({
  selector: 'app-conciliacao',
  standalone: true,
  providers: [ConfirmationService, MessageService],
  imports: [
    FormsModule, CurrencyPipe, DatePipe,
    ButtonModule, TableModule, DialogModule, SelectModule,
    InputTextModule, TagModule, ToastModule, ConfirmPopupModule,
    TooltipModule, TextareaModule, ProgressBarModule,
  ],
  template: `
<p-toast />
<input #ofxInput type="file" hidden accept=".ofx" (change)="onArquivoChange($event, 'ofx')" />
<input #csvInput type="file" hidden accept=".csv,.txt" (change)="onArquivoChange($event, 'csv')" />

<div class="page">
  <div class="page-header">
    <h1 class="page-title">Conciliação Bancária</h1>
    <div class="header-controls">
      <p-select [options]="contasSemCartao()" optionLabel="nome" optionValue="id"
        [(ngModel)]="filtroContaId" placeholder="Selecione a conta"
        (onChange)="onContaChange()" [showClear]="true" />
      <p-button label="Importar OFX" icon="pi pi-file-import" [outlined]="true"
        [disabled]="!filtroContaId" (onClick)="ofxInput.click()" />
      <p-button label="Importar CSV" icon="pi pi-file" [outlined]="true"
        [disabled]="!filtroContaId" (onClick)="csvInput.click()" />
    </div>
  </div>

  @if (importando()) {
    <p-progressbar mode="indeterminate" [style]="{'height':'4px'}" />
  }

  <div class="conciliacao-layout">
    <!-- Painel de importações -->
    <div class="importacoes-panel">
      <div class="panel-header">
        <span class="panel-title">Importações</span>
        @if (carregandoImportacoes()) {
          <i class="pi pi-spin pi-spinner" style="font-size:0.85rem;color:var(--p-surface-400)"></i>
        }
      </div>

      @if (importacoes().length === 0 && !carregandoImportacoes()) {
        <div class="empty-panel">
          @if (filtroContaId) {
            <span>Nenhuma importação para esta conta.</span>
          } @else {
            <span>Selecione uma conta para ver as importações.</span>
          }
        </div>
      }

      <div class="importacoes-list">
        @for (imp of importacoes(); track imp.id) {
          <div class="importacao-card" [class.selected]="importacaoSelecionada()?.id === imp.id"
            (click)="selecionarImportacao(imp)">
            <div class="imp-top">
              <span class="imp-nome" [title]="imp.nome_arquivo">{{ imp.nome_arquivo }}</span>
              <p-tag [value]="labelStatusImp(imp.status)" [severity]="severityStatusImp(imp.status)"
                [style]="{'font-size':'0.7rem'}" />
            </div>
            <div class="imp-counts">
              <span title="Total">{{ imp.total_transacoes }} transações</span>
              <span class="count-ok" title="Conciliadas">{{ imp.conciliadas }} ✓</span>
              <span class="count-ig" title="Ignoradas">{{ imp.ignoradas }} —</span>
              <span class="count-pend" title="Pendentes">{{ imp.total_transacoes - imp.conciliadas - imp.ignoradas }} !</span>
            </div>
          </div>
        }
      </div>
    </div>

    <!-- Painel de transações -->
    <div class="transacoes-panel">
      @if (!importacaoSelecionada()) {
        <div class="empty-transacoes">
          <i class="pi pi-arrow-left" style="font-size:1.5rem;color:var(--p-surface-300)"></i>
          <span>Selecione uma importação para ver as transações</span>
        </div>
      } @else {
        <div class="transacoes-header">
          <span class="panel-title">Transações — {{ importacaoSelecionada()!.nome_arquivo }}</span>
          <div class="status-chips">
            @for (opt of statusTransOpts; track opt.value) {
              <button class="status-chip" [class.active]="filtroStatusTrans() === opt.value"
                (click)="filtroStatusTrans.set(opt.value)">
                {{ opt.label }}
              </button>
            }
          </div>
        </div>

        <p-table [value]="transacoesFiltradas()" [loading]="carregandoTransacoes()" size="small"
          class="p-datatable-gridlines">
          <ng-template pTemplate="header">
            <tr>
              <th style="width:100px">Data</th>
              <th style="width:70px">Tipo</th>
              <th>Descrição</th>
              <th style="width:130px;text-align:right">Valor</th>
              <th style="width:110px">Status</th>
              <th style="width:180px">Ações</th>
            </tr>
          </ng-template>
          <ng-template pTemplate="body" let-t>
            <tr>
              <td>{{ t.data | date:'dd/MM/yyyy' }}</td>
              <td>
                <p-tag [value]="t.tipo === 'credito' ? 'Crédito' : 'Débito'"
                  [severity]="t.tipo === 'credito' ? 'success' : 'danger'" />
              </td>
              <td class="descricao-cell" [title]="t.descricao_original">{{ t.descricao_original }}</td>
              <td style="text-align:right;font-weight:500"
                  [style.color]="t.tipo === 'credito' ? 'var(--p-green-700)' : 'var(--p-red-700)'">
                {{ t.valor | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
              </td>
              <td>
                <p-tag [value]="labelStatusTrans(t.status)" [severity]="severityStatusTrans(t.status)" />
              </td>
              <td>
                @if (t.status === 'pendente') {
                  <div class="acoes-cell">
                    <p-button label="Conciliar" size="small" [text]="true"
                      (onClick)="abrirConciliar(t)" />
                    <p-button label="Lançamento" size="small" [text]="true" severity="secondary"
                      (onClick)="abrirCriarLancamento(t)" />
                    <p-button icon="pi pi-minus-circle" size="small" [text]="true" severity="danger"
                      pTooltip="Ignorar" tooltipPosition="left"
                      (onClick)="ignorarTransacao(t)" />
                  </div>
                }
              </td>
            </tr>
          </ng-template>
          <ng-template pTemplate="emptymessage">
            <tr><td colspan="6" style="text-align:center;padding:2rem;color:var(--p-surface-400)">
              Nenhuma transação encontrada.
            </td></tr>
          </ng-template>
        </p-table>
      }
    </div>
  </div>
</div>

<!-- Dialog: Conciliar com lançamento existente -->
<p-dialog [(visible)]="dialogConciliar" header="Conciliar com Lançamento Existente"
  [modal]="true" [style]="{width:'560px'}" [draggable]="false">
  @if (transacaoAtiva()) {
    <div class="transacao-resumo">
      <span class="tr-label">Transação:</span>
      <span class="tr-value">{{ transacaoAtiva()!.descricao_original }}</span>
      <span class="tr-label">Valor:</span>
      <span class="tr-value" [style.color]="transacaoAtiva()!.tipo === 'credito' ? 'var(--p-green-700)' : 'var(--p-red-700)'">
        {{ transacaoAtiva()!.valor | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
        ({{ transacaoAtiva()!.tipo === 'credito' ? 'Crédito' : 'Débito' }})
      </span>
      <span class="tr-label">Data:</span>
      <span class="tr-value">{{ transacaoAtiva()!.data | date:'dd/MM/yyyy' }}</span>
    </div>

    <div class="sugestoes-section">
      <div class="sugestoes-title">
        Sugestões de lançamentos
        @if (carregandoSugestoes()) {
          <i class="pi pi-spin pi-spinner" style="font-size:0.85rem"></i>
        }
      </div>

      @if (!carregandoSugestoes() && sugestoes().length === 0) {
        <div class="empty-sugestoes">Nenhuma sugestão encontrada. Tente criar um novo lançamento.</div>
      }

      @for (s of sugestoes(); track s.id) {
        <div class="sugestao-card" (click)="conciliarComLancamento(s.id)">
          <div class="sug-tipo">
            <p-tag [value]="s.tipo === 'RECEITA' ? 'Receita' : 'Despesa'"
              [severity]="s.tipo === 'RECEITA' ? 'success' : 'danger'" />
          </div>
          <div class="sug-info">
            <span class="sug-desc">{{ s.descricao }}</span>
            <span class="sug-data">Venc. {{ s.data_vencimento | date:'dd/MM/yyyy' }}</span>
          </div>
          <span class="sug-valor" [style.color]="s.tipo === 'RECEITA' ? 'var(--p-green-700)' : 'var(--p-red-700)'">
            {{ s.valor | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
          </span>
          <i class="pi pi-check-circle sug-check"></i>
        </div>
      }
    </div>
  }

  <ng-template pTemplate="footer">
    <p-button label="Cancelar" [text]="true" severity="secondary" (onClick)="dialogConciliar = false" />
  </ng-template>
</p-dialog>

<!-- Dialog: Criar Lançamento -->
<p-dialog [(visible)]="dialogCriarLanc" header="Criar Lançamento a partir da Transação"
  [modal]="true" [style]="{width:'500px'}" [draggable]="false">
  <div class="form-grid">
    <div class="form-row-2col">
      <div class="form-row">
        <label>Tipo <span class="req">*</span></label>
        <p-select [options]="tipoLancOpts" [(ngModel)]="criarForm.tipo"
          optionLabel="label" optionValue="value" />
      </div>
      <div class="form-row">
        <label>Empresa <span class="req">*</span></label>
        <p-select [options]="empresaStore.empresas()" optionLabel="nome" optionValue="id"
          [(ngModel)]="criarForm.empresaId" />
      </div>
    </div>
    <div class="form-row">
      <label>Descrição <span class="req">*</span></label>
      <input type="text" pInputText [(ngModel)]="criarForm.descricao" maxlength="300" class="full-width" />
    </div>
    <div class="form-row-2col">
      <div class="form-row">
        <label>Data Competência <span class="req">*</span></label>
        <input type="date" pInputText [(ngModel)]="criarForm.dataCompetencia" class="full-width" />
      </div>
      <div class="form-row">
        <label>Data Vencimento <span class="req">*</span></label>
        <input type="date" pInputText [(ngModel)]="criarForm.dataVencimento" class="full-width" />
      </div>
    </div>
    <div class="form-row">
      <label>Categoria</label>
      <p-select [options]="categoriasFiltradas()" optionLabel="nome" optionValue="id"
        [(ngModel)]="criarForm.categoriaId" placeholder="Sem categoria" [showClear]="true" />
    </div>
    <div class="form-row">
      <label>Observações</label>
      <textarea pTextarea [(ngModel)]="criarForm.observacoes" [rows]="2" class="full-width"
        maxlength="1000"></textarea>
    </div>
  </div>

  <ng-template pTemplate="footer">
    <p-button label="Cancelar" [text]="true" severity="secondary" (onClick)="dialogCriarLanc = false" />
    <p-button label="Criar e Conciliar" icon="pi pi-check" [loading]="salvandoLanc()"
      (onClick)="confirmarCriarLancamento()" />
  </ng-template>
</p-dialog>
  `,
  styles: [`
    .page { padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; height: calc(100vh - 120px); }
    .page-header { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; flex-shrink: 0; }
    .page-title { margin: 0; font-size: 1.4rem; font-weight: 700; flex: 1; }
    .header-controls { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .conciliacao-layout { display: grid; grid-template-columns: 300px 1fr; gap: 1rem; flex: 1; min-height: 0; overflow: hidden; }
    .importacoes-panel { display: flex; flex-direction: column; gap: 0.5rem; border: 1px solid var(--p-surface-200); border-radius: 8px; padding: 0.75rem; overflow-y: auto; }
    .transacoes-panel { display: flex; flex-direction: column; gap: 0.75rem; min-height: 0; overflow: hidden; }
    .panel-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem; }
    .panel-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--p-surface-500); }
    .empty-panel, .empty-transacoes { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem; padding: 2rem 1rem; text-align: center; color: var(--p-surface-400); font-size: 0.875rem; height: 100%; }
    .importacoes-list { display: flex; flex-direction: column; gap: 0.4rem; }
    .importacao-card { padding: 0.6rem 0.75rem; border: 1px solid var(--p-surface-200); border-radius: 6px; cursor: pointer; transition: border-color 0.15s, background 0.15s; }
    .importacao-card:hover { border-color: var(--p-primary-300); background: var(--p-primary-50); }
    .importacao-card.selected { border-color: var(--p-primary-color); background: var(--p-primary-50); }
    .imp-top { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; margin-bottom: 0.3rem; }
    .imp-nome { font-size: 0.8rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
    .imp-counts { display: flex; gap: 0.5rem; font-size: 0.75rem; color: var(--p-surface-500); }
    .count-ok { color: var(--p-green-600); }
    .count-ig { color: var(--p-surface-400); }
    .count-pend { color: var(--p-orange-600); }
    .transacoes-header { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; flex-shrink: 0; }
    .status-chips { display: flex; gap: 0.4rem; flex-wrap: wrap; }
    .status-chip { padding: 0.25rem 0.75rem; border-radius: 20px; border: 1px solid var(--p-surface-300); background: transparent; cursor: pointer; font-size: 0.8rem; color: var(--p-surface-600); transition: all 0.15s; }
    .status-chip:hover { border-color: var(--p-primary-300); }
    .status-chip.active { background: var(--p-primary-color); border-color: var(--p-primary-color); color: #fff; }
    .descricao-cell { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.875rem; }
    .acoes-cell { display: flex; align-items: center; gap: 0; }
    .transacao-resumo { display: grid; grid-template-columns: auto 1fr; gap: 0.4rem 1rem; margin-bottom: 1rem; padding: 0.75rem; background: var(--p-surface-50); border-radius: 6px; align-items: center; }
    .tr-label { font-size: 0.8rem; font-weight: 600; color: var(--p-surface-500); }
    .tr-value { font-size: 0.875rem; }
    .sugestoes-section { display: flex; flex-direction: column; gap: 0.5rem; }
    .sugestoes-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--p-surface-400); display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem; }
    .empty-sugestoes { font-size: 0.875rem; color: var(--p-surface-400); padding: 0.5rem 0; }
    .sugestao-card { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0.75rem; border: 1px solid var(--p-surface-200); border-radius: 6px; cursor: pointer; transition: border-color 0.15s, background 0.15s; }
    .sugestao-card:hover { border-color: var(--p-primary-color); background: var(--p-primary-50); }
    .sug-tipo { flex-shrink: 0; }
    .sug-info { flex: 1; display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
    .sug-desc { font-size: 0.875rem; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .sug-data { font-size: 0.75rem; color: var(--p-surface-400); }
    .sug-valor { font-size: 0.9rem; font-weight: 600; white-space: nowrap; }
    .sug-check { color: var(--p-primary-color); opacity: 0; transition: opacity 0.15s; }
    .sugestao-card:hover .sug-check { opacity: 1; }
    .form-grid { display: flex; flex-direction: column; gap: 0.75rem; padding: 0.25rem 0; }
    .form-row { display: flex; flex-direction: column; gap: 0.25rem; }
    .form-row-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    label { font-size: 0.85rem; font-weight: 500; color: var(--p-surface-600); }
    .req { color: var(--p-red-500); }
    :host ::ng-deep .full-width, input.full-width, textarea.full-width { width: 100%; }
    input[type="date"] { height: 2.25rem; padding: 0 0.75rem; border: 1px solid var(--p-surface-300);
      border-radius: 6px; font-size: 0.875rem; color: var(--p-surface-700); background: var(--p-surface-0); }
  `],
})
export class ConciliacaoComponent implements OnInit {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly contaSvc = inject(ContaBancariaService);
  private readonly concilSvc = inject(ConciliacaoService);
  private readonly catSvc = inject(CategoriaService);
  private readonly msgSvc = inject(MessageService);

  protected readonly contas = signal<ContaBancaria[]>([]);
  protected readonly categorias = signal<Categoria[]>([]);
  protected readonly importacoes = signal<ImportacaoBancariaResponse[]>([]);
  protected readonly transacoes = signal<TransacaoBancariaResponse[]>([]);
  protected readonly sugestoes = signal<SugestaoMatchResponse[]>([]);
  protected readonly importacaoSelecionada = signal<ImportacaoBancariaResponse | null>(null);
  protected readonly transacaoAtiva = signal<TransacaoBancariaResponse | null>(null);

  protected readonly carregandoImportacoes = signal(false);
  protected readonly carregandoTransacoes = signal(false);
  protected readonly carregandoSugestoes = signal(false);
  protected readonly importando = signal(false);
  protected readonly salvandoLanc = signal(false);

  protected filtroContaId: string | null = null;
  protected readonly filtroStatusTrans = signal('');
  protected dialogConciliar = false;
  protected dialogCriarLanc = false;

  protected criarForm = {
    empresaId: '',
    descricao: '',
    tipo: '' as 'RECEITA' | 'DESPESA',
    dataCompetencia: '',
    dataVencimento: '',
    categoriaId: '' as string | null,
    observacoes: '',
  };

  protected readonly contasSemCartao = computed(() =>
    this.contas().filter(c => c.tipo !== 'cartao_credito')
  );

  protected readonly transacoesFiltradas = computed(() => {
    const list = this.transacoes();
    const filtro = this.filtroStatusTrans();
    if (!filtro) return list;
    return list.filter(t => t.status === filtro);
  });

  protected readonly categoriasFiltradas = computed(() =>
    this.categorias().filter(c => c.tipo === this.criarForm.tipo || !this.criarForm.tipo)
  );

  protected readonly statusTransOpts = [
    { label: 'Todas', value: '' },
    { label: 'Pendentes', value: 'pendente' },
    { label: 'Conciliadas', value: 'conciliada' },
    { label: 'Ignoradas', value: 'ignorada' },
  ];

  protected readonly tipoLancOpts = [
    { label: 'Receita', value: 'RECEITA' },
    { label: 'Despesa', value: 'DESPESA' },
  ];

  ngOnInit(): void {
    this.contaSvc.listar().subscribe(c => this.contas.set(c));
    this.catSvc.listar().subscribe(c => this.categorias.set(c));
  }

  protected onContaChange(): void {
    this.importacaoSelecionada.set(null);
    this.transacoes.set([]);
    if (this.filtroContaId) {
      this.carregarImportacoes();
    } else {
      this.importacoes.set([]);
    }
  }

  private carregarImportacoes(): void {
    this.carregandoImportacoes.set(true);
    this.concilSvc.listarImportacoes(this.filtroContaId).subscribe({
      next: i => { this.importacoes.set(i); this.carregandoImportacoes.set(false); },
      error: () => this.carregandoImportacoes.set(false),
    });
  }

  protected selecionarImportacao(imp: ImportacaoBancariaResponse): void {
    this.importacaoSelecionada.set(imp);
    this.filtroStatusTrans.set('');
    this.carregarTransacoes(imp.id);
  }

  private carregarTransacoes(importacaoId: string): void {
    this.carregandoTransacoes.set(true);
    this.transacoes.set([]);
    this.concilSvc.listarTransacoes(importacaoId).subscribe({
      next: t => { this.transacoes.set(t); this.carregandoTransacoes.set(false); },
      error: () => this.carregandoTransacoes.set(false),
    });
  }

  protected onArquivoChange(event: Event, tipo: 'ofx' | 'csv'): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !this.filtroContaId) return;

    const conta = this.contas().find(c => c.id === this.filtroContaId);
    const empresaId = conta?.empresa_id;
    if (!empresaId) return;

    this.importando.set(true);
    const obs = tipo === 'ofx'
      ? this.concilSvc.importarOfx(file, this.filtroContaId, empresaId)
      : this.concilSvc.importarCsv(file, this.filtroContaId, empresaId);

    obs.subscribe({
      next: imp => {
        this.importacoes.update(list => [imp, ...list]);
        this.importando.set(false);
        this.msgSvc.add({ severity: 'success', summary: 'Sucesso',
          detail: `Importação concluída: ${imp.total_transacoes} transação(ões).` });
        this.selecionarImportacao(imp);
      },
      error: err => {
        this.importando.set(false);
        this.msgSvc.add({ severity: 'error', summary: 'Erro',
          detail: err?.error?.detail ?? 'Erro ao importar arquivo.' });
      },
    });
    input.value = '';
  }

  protected abrirConciliar(t: TransacaoBancariaResponse): void {
    this.transacaoAtiva.set(t);
    this.sugestoes.set([]);
    this.dialogConciliar = true;
    this.carregandoSugestoes.set(true);
    this.concilSvc.sugerirMatch(t.id).subscribe({
      next: s => { this.sugestoes.set(s); this.carregandoSugestoes.set(false); },
      error: () => this.carregandoSugestoes.set(false),
    });
  }

  protected conciliarComLancamento(lancamentoId: string): void {
    const t = this.transacaoAtiva();
    if (!t) return;
    this.concilSvc.conciliar(t.id, lancamentoId).subscribe({
      next: updated => {
        this.transacoes.update(list => list.map(x => x.id === updated.id ? updated : x));
        this.atualizarContadores(updated.importacao_id);
        this.dialogConciliar = false;
        this.msgSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Transação conciliada.' });
      },
      error: err => this.msgSvc.add({ severity: 'error', summary: 'Erro',
        detail: err?.error?.detail ?? 'Erro ao conciliar.' }),
    });
  }

  protected abrirCriarLancamento(t: TransacaoBancariaResponse): void {
    this.transacaoAtiva.set(t);
    this.criarForm = {
      empresaId: t.empresa_id,
      descricao: t.descricao_original,
      tipo: t.tipo === 'credito' ? 'RECEITA' : 'DESPESA',
      dataCompetencia: t.data,
      dataVencimento: t.data,
      categoriaId: null,
      observacoes: '',
    };
    this.dialogCriarLanc = true;
  }

  protected confirmarCriarLancamento(): void {
    const t = this.transacaoAtiva();
    if (!t || !this.criarForm.descricao || !this.criarForm.dataCompetencia || !this.criarForm.dataVencimento) {
      this.msgSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha os campos obrigatórios.' });
      return;
    }
    const payload: CriarLancamentoConciliacaoRequest = {
      empresa_id: this.criarForm.empresaId,
      descricao: this.criarForm.descricao,
      tipo: this.criarForm.tipo,
      data_competencia: this.criarForm.dataCompetencia,
      data_vencimento: this.criarForm.dataVencimento,
      categoria_id: this.criarForm.categoriaId || null,
      observacoes: this.criarForm.observacoes || null,
    };
    this.salvandoLanc.set(true);
    this.concilSvc.criarLancamento(t.id, payload).subscribe({
      next: updated => {
        this.transacoes.update(list => list.map(x => x.id === updated.id ? updated : x));
        this.atualizarContadores(updated.importacao_id);
        this.salvandoLanc.set(false);
        this.dialogCriarLanc = false;
        this.msgSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento criado e transação conciliada.' });
      },
      error: err => {
        this.salvandoLanc.set(false);
        this.msgSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao criar lançamento.' });
      },
    });
  }

  protected ignorarTransacao(t: TransacaoBancariaResponse): void {
    this.concilSvc.ignorar(t.id).subscribe({
      next: updated => {
        this.transacoes.update(list => list.map(x => x.id === updated.id ? updated : x));
        this.atualizarContadores(updated.importacao_id);
        this.msgSvc.add({ severity: 'info', summary: 'Ignorada', detail: 'Transação marcada como ignorada.' });
      },
      error: err => this.msgSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro.' }),
    });
  }

  private atualizarContadores(importacaoId: string): void {
    const transacoes = this.transacoes();
    const total = transacoes.length;
    const conciliadas = transacoes.filter(t => t.status === 'conciliada').length;
    const ignoradas = transacoes.filter(t => t.status === 'ignorada').length;
    this.importacoes.update(list => list.map(imp =>
      imp.id === importacaoId
        ? { ...imp, total_transacoes: total, conciliadas, ignoradas }
        : imp
    ));
    const sel = this.importacaoSelecionada();
    if (sel?.id === importacaoId) {
      this.importacaoSelecionada.set({ ...sel, total_transacoes: total, conciliadas, ignoradas });
    }
  }

  protected labelStatusImp(status: string): string {
    const m: Record<string, string> = { processando: 'Processando', concluida: 'Concluída', erro: 'Erro' };
    return m[status] ?? status;
  }
  protected severityStatusImp(status: string): 'warn' | 'success' | 'danger' {
    if (status === 'concluida') return 'success';
    if (status === 'erro') return 'danger';
    return 'warn';
  }
  protected labelStatusTrans(status: string): string {
    const m: Record<string, string> = { pendente: 'Pendente', conciliada: 'Conciliada', ignorada: 'Ignorada' };
    return m[status] ?? status;
  }
  protected severityStatusTrans(status: string): 'warn' | 'success' | 'secondary' {
    if (status === 'conciliada') return 'success';
    if (status === 'ignorada') return 'secondary';
    return 'warn';
  }
}
