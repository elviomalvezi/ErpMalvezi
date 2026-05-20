import { Component, computed, effect, inject, signal, untracked } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { DatePickerModule } from 'primeng/datepicker';
import { DialogModule } from 'primeng/dialog';
import { DividerModule } from 'primeng/divider';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { TextareaModule } from 'primeng/textarea';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { CategoriaService } from '../../core/services/categoria.service';
import { ContatoService } from '../../core/services/contato.service';
import { ContaBancariaService } from '../../core/services/conta-bancaria.service';
import { LancamentoService } from '../../core/services/lancamento.service';
import { LancamentoImportacaoComponent } from './lancamento-importacao.component';
import type {
  Lancamento,
  LancamentoAnexo,
  LancamentoCreate,
  LancamentoParceladoCreate,
  LancamentoRecorrenteCreate,
  LancamentoBaixaCreate,
  LancamentoUpdate,
  Categoria,
  Contato,
  ContaBancaria,
} from '../../core/models';

type FiltroStatus = 'TODOS' | 'pendente' | 'pago' | 'cancelado';
type ModoDialog = 'simples' | 'parcelado' | 'recorrente';

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];

@Component({
  selector: 'app-lancamentos',
  standalone: true,
  providers: [ConfirmationService, MessageService],
  imports: [
    ReactiveFormsModule,
    ButtonModule, TableModule, DialogModule, TagModule, ToastModule,
    InputTextModule, InputNumberModule, SelectModule, DatePickerModule,
    TextareaModule, DividerModule, ConfirmPopupModule, TooltipModule,
    LancamentoImportacaoComponent,
  ],
  template: `
<p-toast />
<p-confirmpopup />

@if (!empresaAtiva()) {
  <div class="sem-empresa">Selecione uma empresa para visualizar os lançamentos.</div>
} @else {
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ titulo() }}</h1>
        <div class="month-nav">
          <p-button icon="pi pi-chevron-left" [text]="true" [rounded]="true" (onClick)="mesAnterior()" />
          <span class="month-label">{{ mesTitulo() }}</span>
          <p-button icon="pi pi-chevron-right" [text]="true" [rounded]="true" (onClick)="proximoMes()" />
        </div>
      </div>
      <div class="header-actions">
        @if (empresaAtiva()) {
          <app-lancamento-importacao
            [empresaId]="empresaAtiva()!.id"
            [tipo]="tipo()"
            (importado)="carregarDados()"
          />
        }
        <p-button label="Novo" icon="pi pi-plus" (onClick)="abrirCriar()" />
      </div>
    </div>

    <div class="status-bar">
      @for (opt of statusOpts; track opt.value) {
        <p-button
          [label]="opt.label"
          [outlined]="filtroStatus() !== opt.value"
          size="small"
          (onClick)="filtroStatus.set(opt.value)"
        />
      }
    </div>

    <p-table
      [value]="listaFiltrada()"
      [loading]="loading()"
      [paginator]="true"
      [rows]="20"
      [rowsPerPageOptions]="[10, 20, 50]"
      [showCurrentPageReport]="true"
      currentPageReportTemplate="{first}–{last} de {totalRecords}"
      size="small"
    >
      <ng-template pTemplate="header">
        <tr>
          <th>Descrição</th>
          <th>Categoria</th>
          <th>Contato</th>
          <th>Vencimento</th>
          <th class="col-right">Valor</th>
          <th class="col-right">Pago</th>
          <th>Status</th>
          <th style="width:7rem"></th>
        </tr>
      </ng-template>
      <ng-template pTemplate="body" let-lct>
        <tr [class.row-pago]="lct.status === 'pago'" [class.row-cancelado]="lct.status === 'cancelado'">
          <td>
            <span>{{ lct.descricao }}</span>
            @if (lct.numero_parcela) {
              <span class="parcela-badge">{{ lct.numero_parcela }}/{{ lct.total_parcelas }}</span>
            }
          </td>
          <td>{{ categoriaMap().get(lct.categoria_id) ?? '—' }}</td>
          <td>{{ contatoMap().get(lct.contato_id) ?? '—' }}</td>
          <td>{{ formatDate(lct.data_vencimento) }}</td>
          <td class="col-right">{{ formatMoeda(lct.valor) }}</td>
          <td class="col-right">{{ formatMoeda(lct.valor_pago) }}</td>
          <td>
            <p-tag [value]="statusLabel(lct.status)" [severity]="statusSeverity(lct.status)" />
          </td>
          <td>
            <div class="acoes">
              @if (lct.status === 'pendente') {
                <p-button
                  icon="pi pi-check"
                  [text]="true" [rounded]="true" size="small"
                  pTooltip="Registrar pagamento" tooltipPosition="left"
                  (onClick)="abrirBaixa(lct)"
                />
                <p-button
                  icon="pi pi-pencil"
                  [text]="true" [rounded]="true" size="small"
                  pTooltip="Editar" tooltipPosition="left"
                  (onClick)="abrirEditar(lct)"
                />
              }
              @if (lct.status !== 'cancelado') {
                <p-button
                  icon="pi pi-times"
                  [text]="true" [rounded]="true" size="small"
                  severity="danger"
                  pTooltip="Cancelar" tooltipPosition="left"
                  (onClick)="confirmarCancelamento($event, lct.id)"
                />
              }
            </div>
          </td>
        </tr>
      </ng-template>
      <ng-template pTemplate="emptymessage">
        <tr>
          <td colspan="8" class="empty-msg">Nenhum lançamento encontrado neste período.</td>
        </tr>
      </ng-template>
    </p-table>
  </div>
}

<!-- Dialog Criar / Editar -->
<p-dialog
  [header]="dialogTitulo()"
  [visible]="dialogVisivel()"
  (visibleChange)="dialogVisivel.set($event)"
  [modal]="true"
  [style]="{width: '640px'}"
  [closeOnEscape]="true"
>
  <form [formGroup]="form" (ngSubmit)="salvar()">
    @if (!editandoId()) {
      <div class="modo-selector">
        @for (m of modoOpts; track m.value) {
          <p-button
            [label]="m.label"
            [outlined]="modoDialog() !== m.value"
            size="small"
            type="button"
            (onClick)="modoDialog.set(m.value)"
          />
        }
      </div>
      <p-divider />
    }

    <div class="form-grid">
      <div class="field full">
        <label>Descrição *</label>
        <input pInputText formControlName="descricao" placeholder="Ex: Aluguel escritório" class="w-full" />
      </div>

      @if (modoDialog() === 'simples' || modoDialog() === 'recorrente' || editandoId()) {
        <div class="field">
          <label>Valor *</label>
          <p-inputNumber
            formControlName="valor"
            mode="decimal"
            [minFractionDigits]="2"
            [maxFractionDigits]="2"
            [min]="0.01"
            locale="pt-BR"
            class="w-full"
          />
        </div>
      }

      @if (modoDialog() === 'parcelado' && !editandoId()) {
        <div class="field">
          <label>Valor Total *</label>
          <p-inputNumber
            formControlName="valor_total"
            mode="decimal"
            [minFractionDigits]="2"
            [maxFractionDigits]="2"
            [min]="0.01"
            locale="pt-BR"
            class="w-full"
          />
        </div>
        <div class="field">
          <label>Nº de Parcelas *</label>
          <p-inputNumber formControlName="parcelas" [min]="2" [max]="360" [useGrouping]="false" class="w-full" />
        </div>
      }

      @if (modoDialog() === 'simples' || editandoId()) {
        <div class="field">
          <label>Data Competência *</label>
          <p-datepicker formControlName="data_competencia" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
        <div class="field">
          <label>Data Vencimento *</label>
          <p-datepicker formControlName="data_vencimento" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
      }

      @if ((modoDialog() === 'parcelado' || modoDialog() === 'recorrente') && !editandoId()) {
        <div class="field">
          <label>1ª Competência *</label>
          <p-datepicker formControlName="data_primeira_competencia" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
        <div class="field">
          <label>1º Vencimento *</label>
          <p-datepicker formControlName="data_primeiro_vencimento" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
      }

      @if (modoDialog() === 'recorrente' && !editandoId()) {
        <div class="field">
          <label>Frequência *</label>
          <p-select
            formControlName="frequencia"
            [options]="frequenciaOpts"
            optionLabel="label"
            optionValue="value"
            placeholder="Selecione"
            class="w-full"
          />
        </div>
        <div class="field">
          <label>Quantidade *</label>
          <p-inputNumber formControlName="quantidade" [min]="2" [max]="120" [useGrouping]="false" class="w-full" />
        </div>
      }

      <div class="field">
        <label>Categoria</label>
        <p-select
          formControlName="categoria_id"
          [options]="categoriaOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          placeholder="— Sem categoria —"
          [showClear]="true"
          class="w-full"
        />
      </div>

      <div class="field">
        <label>Contato</label>
        <p-select
          formControlName="contato_id"
          [options]="contatoOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          placeholder="— Sem contato —"
          [showClear]="true"
          class="w-full"
        />
      </div>

      <div class="field full">
        <label>Conta Bancária</label>
        <p-select
          formControlName="conta_bancaria_id"
          [options]="contaOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          placeholder="— Sem conta —"
          [showClear]="true"
          class="w-full"
        />
      </div>

      <div class="field full">
        <label>Observações</label>
        <textarea pTextarea formControlName="observacoes" rows="2" class="w-full" placeholder="Opcional"></textarea>
      </div>
    </div>

    @if (editandoId()) {
      <p-divider />
      <div class="anexos-section">
        <div class="anexos-header">
          <span class="anexos-title">Anexos</span>
          @if (carregandoAnexos()) {
            <i class="pi pi-spin pi-spinner" style="font-size:0.85rem; color:var(--p-surface-400)"></i>
          }
        </div>

        <div
          class="drop-zone"
          [class.drag-over]="dragOver()"
          (dragover)="$event.preventDefault(); dragOver.set(true)"
          (dragleave)="dragOver.set(false)"
          (drop)="onDrop($event)"
          (click)="fileInput.click()"
        >
          <i class="pi pi-upload drop-icon"></i>
          <span class="drop-text">Arraste arquivos ou clique para selecionar</span>
          <span class="drop-hint">PDF, imagens, Word, Excel, CSV — máx. 10 MB</span>
        </div>
        <input #fileInput type="file" hidden multiple
          accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.doc,.docx,.xls,.xlsx,.csv,.txt"
          (change)="onFileInputChange($event)" />

        @if (uploadando()) {
          <div class="upload-progress">
            <i class="pi pi-spin pi-spinner"></i>
            <span>Enviando...</span>
          </div>
        }

        <div class="anexos-list">
          @for (anexo of anexos(); track anexo.id) {
            <div class="anexo-item">
              <i [class]="'pi ' + mimeIcon(anexo.mime_type) + ' anexo-icon'"></i>
              <span class="anexo-nome" [title]="anexo.nome_original">{{ anexo.nome_original }}</span>
              <span class="anexo-tamanho">{{ formatBytes(anexo.tamanho) }}</span>
              <a [href]="downloadUrl(anexo)" target="_blank" rel="noopener"
                class="p-button p-button-text p-button-sm p-button-rounded"
                pTooltip="Baixar" tooltipPosition="left">
                <i class="pi pi-download"></i>
              </a>
              <p-button icon="pi pi-trash" [text]="true" [rounded]="true" size="small"
                severity="danger" pTooltip="Excluir" tooltipPosition="left"
                (onClick)="confirmarExcluirAnexo($event, anexo.id)" />
            </div>
          } @empty {
            <span class="anexos-empty">Nenhum arquivo anexado.</span>
          }
        </div>
      </div>
    }

    <div class="dialog-footer">
      <p-button label="Cancelar" [outlined]="true" type="button" (onClick)="fecharDialog()" />
      <p-button [label]="editandoId() ? 'Salvar' : 'Criar'" type="submit" [loading]="salvando()" />
    </div>
  </form>
</p-dialog>

<!-- Dialog Registrar Pagamento -->
<p-dialog
  header="Registrar Pagamento"
  [visible]="baixaDialogVisivel()"
  (visibleChange)="baixaDialogVisivel.set($event)"
  [modal]="true"
  [style]="{width: '420px'}"
>
  <form [formGroup]="baixaForm" (ngSubmit)="registrarBaixa()">
    <div class="form-grid">
      <div class="field">
        <label>Valor Pago *</label>
        <p-inputNumber
          formControlName="valor_pago"
          mode="decimal"
          [minFractionDigits]="2"
          [maxFractionDigits]="2"
          [min]="0.01"
          locale="pt-BR"
          class="w-full"
        />
      </div>
      <div class="field">
        <label>Data Pagamento *</label>
        <p-datepicker formControlName="data_pagamento" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
      </div>
      <div class="field full">
        <label>Conta Bancária *</label>
        <p-select
          formControlName="conta_bancaria_id"
          [options]="contaOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          placeholder="Selecione a conta"
          class="w-full"
        />
      </div>
      <div class="field full">
        <label>Categoria *</label>
        <p-select
          formControlName="categoria_id"
          [options]="categoriaOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          placeholder="Selecione a categoria"
          class="w-full"
        />
      </div>
    </div>
    <div class="dialog-footer">
      <p-button label="Cancelar" [outlined]="true" type="button" (onClick)="baixaDialogVisivel.set(false)" />
      <p-button label="Registrar" type="submit" [loading]="salvando()" severity="success" [disabled]="baixaForm.invalid" />
    </div>
  </form>
</p-dialog>
  `,
  styles: [`
    .sem-empresa { color: var(--p-surface-500); padding: 2rem; }
    .page { display: flex; flex-direction: column; gap: 1rem; }
    .page-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
    .header-left { display: flex; align-items: center; gap: 1.5rem; }
    .header-actions { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .page-title { margin: 0; font-size: 1.5rem; font-weight: 700; }
    .month-nav { display: flex; align-items: center; gap: 0.25rem; }
    .month-label { font-size: 1rem; font-weight: 600; min-width: 11rem; text-align: center; }
    .status-bar { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .col-right { text-align: right; }
    .acoes { display: flex; gap: 0.125rem; justify-content: flex-end; }
    .parcela-badge { margin-left: 0.4rem; font-size: 0.72rem; color: var(--p-surface-500); background: var(--p-surface-100); padding: 0.1rem 0.35rem; border-radius: 999px; }
    .row-pago td { opacity: 0.7; }
    .row-cancelado td { opacity: 0.45; text-decoration: line-through; }
    .empty-msg { text-align: center; padding: 2rem; color: var(--p-surface-500); }
    .modo-selector { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem 1.5rem; }
    .field { display: flex; flex-direction: column; gap: 0.25rem; }
    .field.full { grid-column: 1 / -1; }
    label { font-size: 0.875rem; font-weight: 500; }
    .dialog-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--p-surface-200); }
    :host ::ng-deep .w-full .p-inputnumber,
    :host ::ng-deep .p-select.w-full,
    :host ::ng-deep .p-datepicker.w-full { width: 100%; }
    .anexos-section { margin-top: 0.25rem; }
    .anexos-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
    .anexos-title { font-size: 0.85rem; font-weight: 600; color: var(--p-surface-500); text-transform: uppercase; letter-spacing: 0.05em; }
    .drop-zone {
      border: 2px dashed var(--p-surface-300); border-radius: 8px;
      padding: 1.25rem 1rem; display: flex; flex-direction: column;
      align-items: center; gap: 0.2rem; cursor: pointer;
      transition: border-color 0.15s, background 0.15s; user-select: none;
    }
    .drop-zone:hover, .drop-zone.drag-over { border-color: var(--p-primary-color); background: var(--p-primary-50); }
    .drop-icon { font-size: 1.5rem; color: var(--p-surface-400); }
    .drop-zone.drag-over .drop-icon { color: var(--p-primary-color); }
    .drop-text { font-size: 0.875rem; color: var(--p-surface-600); }
    .drop-hint { font-size: 0.75rem; color: var(--p-surface-400); }
    .upload-progress { display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0; color: var(--p-surface-500); font-size: 0.85rem; }
    .anexos-list { margin-top: 0.625rem; display: flex; flex-direction: column; gap: 0.3rem; }
    .anexo-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0.5rem; background: var(--p-surface-50); border-radius: 6px; border: 1px solid var(--p-surface-200); }
    .anexo-icon { font-size: 1rem; color: var(--p-surface-500); flex-shrink: 0; }
    .anexo-nome { flex: 1; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
    .anexo-tamanho { font-size: 0.75rem; color: var(--p-surface-400); white-space: nowrap; }
    .anexos-empty { font-size: 0.85rem; color: var(--p-surface-400); display: block; padding: 0.25rem 0; }
  `],
})
export class LancamentosComponent {
  private readonly route = inject(ActivatedRoute);
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(LancamentoService);
  private readonly categoriaSvc = inject(CategoriaService);
  private readonly contatoSvc = inject(ContatoService);
  private readonly contaSvc = inject(ContaBancariaService);
  private readonly confirmSvc = inject(ConfirmationService);
  private readonly messageSvc = inject(MessageService);
  protected readonly empresaStore = inject(EmpresaStore);

  protected readonly tipo = signal<'RECEITA' | 'DESPESA'>('DESPESA');
  protected readonly empresaAtiva = computed(() => this.empresaStore.empresaAtiva());
  protected readonly titulo = computed(() => this.tipo() === 'RECEITA' ? 'Contas a Receber' : 'Contas a Pagar');

  protected readonly mesAtual = signal(new Date());
  protected readonly mesTitulo = computed(() => {
    const d = this.mesAtual();
    return `${MESES[d.getMonth()]} / ${d.getFullYear()}`;
  });

  protected readonly filtroStatus = signal<FiltroStatus>('TODOS');
  protected readonly lista = signal<Lancamento[]>([]);
  protected readonly loading = signal(false);
  protected readonly salvando = signal(false);

  protected readonly categorias = signal<Categoria[]>([]);
  protected readonly contatos = signal<Contato[]>([]);
  protected readonly contas = signal<ContaBancaria[]>([]);

  protected readonly categoriaMap = computed(() =>
    new Map(this.categorias().map(c => [c.id, c.nome]))
  );
  protected readonly contatoMap = computed(() =>
    new Map(this.contatos().map(c => [c.id, c.nome_principal]))
  );

  protected readonly categoriaOpts = computed(() =>
    this.categorias()
      .filter(c => c.ativa && c.tipo === this.tipo())
      .map(c => ({
        label: (c.nivel > 1 ? '  '.repeat(c.nivel - 1) + '↳ ' : '') + c.nome,
        value: c.id,
      }))
  );
  protected readonly contatoOpts = computed(() =>
    this.contatos().filter(c => c.ativa).map(c => ({ label: c.nome_principal, value: c.id }))
  );
  protected readonly contaOpts = computed(() =>
    this.contas().filter(c => c.ativa).map(c => ({ label: c.nome, value: c.id }))
  );

  protected readonly listaFiltrada = computed(() => {
    const status = this.filtroStatus();
    const items = this.lista();
    if (status === 'TODOS') return items;
    return items.filter(l => l.status === status);
  });

  // Dialog state
  protected readonly dialogVisivel = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected readonly modoDialog = signal<ModoDialog>('simples');
  protected readonly dialogTitulo = computed(() =>
    this.editandoId() ? `Editar ${this.titulo()}` : `Novo ${this.titulo()}`
  );

  // Baixa state
  protected readonly baixaDialogVisivel = signal(false);
  protected readonly baixandoId = signal<string | null>(null);

  // Anexos state
  protected readonly anexos = signal<LancamentoAnexo[]>([]);
  protected readonly carregandoAnexos = signal(false);
  protected readonly dragOver = signal(false);
  protected readonly uploadando = signal(false);

  readonly statusOpts: { label: string; value: FiltroStatus }[] = [
    { label: 'Todos', value: 'TODOS' },
    { label: 'Pendente', value: 'pendente' },
    { label: 'Pago', value: 'pago' },
    { label: 'Cancelado', value: 'cancelado' },
  ];

  readonly modoOpts: { label: string; value: ModoDialog }[] = [
    { label: 'Simples', value: 'simples' },
    { label: 'Parcelado', value: 'parcelado' },
    { label: 'Recorrente', value: 'recorrente' },
  ];

  readonly frequenciaOpts = [
    { label: 'Semanal', value: 'semanal' },
    { label: 'Quinzenal', value: 'quinzenal' },
    { label: 'Mensal', value: 'mensal' },
    { label: 'Anual', value: 'anual' },
  ];

  readonly form = this.fb.group({
    descricao: ['', [Validators.required, Validators.minLength(2)]],
    valor: [null as number | null],
    valor_total: [null as number | null],
    parcelas: [2 as number | null],
    frequencia: [null as string | null],
    quantidade: [12 as number | null],
    data_competencia: [null as Date | null],
    data_vencimento: [null as Date | null],
    data_primeira_competencia: [null as Date | null],
    data_primeiro_vencimento: [null as Date | null],
    categoria_id: [null as string | null],
    contato_id: [null as string | null],
    conta_bancaria_id: [null as string | null],
    observacoes: [null as string | null],
  });

  readonly baixaForm = this.fb.group({
    valor_pago: [null as number | null, [Validators.required, Validators.min(0.01)]],
    data_pagamento: [new Date() as Date | null, Validators.required],
    conta_bancaria_id: [null as string | null, Validators.required],
    categoria_id: [null as string | null, Validators.required],
  });

  constructor() {
    const routeTipo = this.route.snapshot.data['tipo'] as string;
    this.tipo.set(routeTipo === 'receita' ? 'RECEITA' : 'DESPESA');

    effect(() => {
      const empresa = this.empresaStore.empresaAtiva();
      this.mesAtual();
      if (empresa) untracked(() => this.carregarDados());
    });

    effect(() => {
      if (this.empresaStore.empresaAtiva()) {
        untracked(() => {
          this.carregarCategorias();
          this.carregarContatos();
          this.carregarContas();
        });
      }
    });
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

  protected carregarDados(): void {
    const empresa = this.empresaAtiva();
    if (!empresa) return;
    const d = this.mesAtual();
    const inicio = this.toISODate(new Date(d.getFullYear(), d.getMonth(), 1));
    const fim = this.toISODate(new Date(d.getFullYear(), d.getMonth() + 1, 0));
    this.loading.set(true);
    this.svc.listar({
      empresaId: empresa.id,
      tipo: this.tipo(),
      dataInicio: inicio,
      dataFim: fim,
      apenasAtivos: false,
    }).subscribe({
      next: (data) => { this.lista.set(data); this.loading.set(false); },
      error: () => {
        this.loading.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar lançamentos.' });
      },
    });
  }

  private carregarCategorias(): void {
    this.categoriaSvc.listar(null, true).subscribe({
      next: (data) => this.categorias.set(data),
      error: () => {},
    });
  }

  private carregarContatos(): void {
    const empresa = this.empresaAtiva();
    this.contatoSvc.listar({ empresaId: empresa?.id, apenasAtivas: true }).subscribe({
      next: (data) => this.contatos.set(data),
      error: () => {},
    });
  }

  private carregarContas(): void {
    const empresa = this.empresaAtiva();
    this.contaSvc.listar({ empresaId: empresa?.id, apenasAtivas: true }).subscribe({
      next: (data) => this.contas.set(data),
      error: () => {},
    });
  }

  protected abrirCriar(): void {
    this.editandoId.set(null);
    this.modoDialog.set('simples');
    this.form.reset({
      descricao: '',
      valor: null,
      valor_total: null,
      parcelas: 2,
      frequencia: null,
      quantidade: 12,
      data_competencia: new Date(),
      data_vencimento: new Date(),
      data_primeira_competencia: new Date(),
      data_primeiro_vencimento: new Date(),
      categoria_id: null,
      contato_id: null,
      conta_bancaria_id: null,
      observacoes: null,
    });
    this.dialogVisivel.set(true);
  }

  protected abrirEditar(lct: Lancamento): void {
    this.editandoId.set(lct.id);
    this.modoDialog.set('simples');
    this.carregarAnexos(lct.id);
    this.form.reset({
      descricao: lct.descricao,
      valor: Number(lct.valor),
      valor_total: null,
      parcelas: null,
      frequencia: null,
      quantidade: null,
      data_competencia: lct.data_competencia ? new Date(lct.data_competencia + 'T00:00:00') : null,
      data_vencimento: lct.data_vencimento ? new Date(lct.data_vencimento + 'T00:00:00') : null,
      data_primeira_competencia: null,
      data_primeiro_vencimento: null,
      categoria_id: lct.categoria_id,
      contato_id: lct.contato_id,
      conta_bancaria_id: lct.conta_bancaria_id,
      observacoes: lct.observacoes,
    });
    this.dialogVisivel.set(true);
  }

  protected fecharDialog(): void {
    this.dialogVisivel.set(false);
    this.anexos.set([]);
  }

  protected salvar(): void {
    const empresa = this.empresaAtiva();
    if (!empresa) return;
    const v = this.form.value;
    const modo = this.modoDialog();
    const editandoId = this.editandoId();

    if (editandoId) {
      if (!v.descricao || v.descricao.length < 2) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Descrição é obrigatória.' });
        return;
      }
      const payload: LancamentoUpdate = {};
      payload.descricao = v.descricao;
      if (v.valor != null) payload.valor = v.valor;
      if (v.data_competencia) payload.data_competencia = this.toISODate(v.data_competencia);
      if (v.data_vencimento) payload.data_vencimento = this.toISODate(v.data_vencimento);
      payload.categoria_id = v.categoria_id ?? null;
      payload.contato_id = v.contato_id ?? null;
      payload.observacoes = v.observacoes ?? null;

      this.salvando.set(true);
      this.svc.atualizar(editandoId, payload).subscribe({
        next: (updated) => {
          this.lista.update(lst => lst.map(l => l.id === updated.id ? updated : l));
          this.salvando.set(false);
          this.dialogVisivel.set(false);
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento atualizado.' });
        },
        error: (err) => {
          this.salvando.set(false);
          const detail = err?.error?.detail ?? 'Erro ao atualizar lançamento.';
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
        },
      });
      return;
    }

    if (!v.descricao || v.descricao.length < 2) {
      this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Descrição é obrigatória.' });
      return;
    }

    this.salvando.set(true);

    if (modo === 'simples') {
      if (!v.valor || !v.data_competencia || !v.data_vencimento) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha valor, competência e vencimento.' });
        this.salvando.set(false);
        return;
      }
      const payload: LancamentoCreate = {
        empresa_id: empresa.id,
        tipo: this.tipo(),
        descricao: v.descricao,
        valor: v.valor,
        data_competencia: this.toISODate(v.data_competencia),
        data_vencimento: this.toISODate(v.data_vencimento),
        categoria_id: v.categoria_id ?? null,
        contato_id: v.contato_id ?? null,
        conta_bancaria_id: v.conta_bancaria_id ?? null,
        observacoes: v.observacoes ?? null,
      };
      this.svc.criar(payload).subscribe({
        next: (lct) => {
          this.lista.update(lst => [...lst, lct]);
          this.salvando.set(false);
          this.dialogVisivel.set(false);
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento criado.' });
        },
        error: (err) => {
          this.salvando.set(false);
          const detail = err?.error?.detail ?? 'Erro ao criar lançamento.';
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
        },
      });

    } else if (modo === 'parcelado') {
      if (!v.valor_total || !v.parcelas || !v.data_primeira_competencia || !v.data_primeiro_vencimento) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha valor total, parcelas e datas.' });
        this.salvando.set(false);
        return;
      }
      const payload: LancamentoParceladoCreate = {
        empresa_id: empresa.id,
        tipo: this.tipo(),
        descricao: v.descricao,
        valor_total: v.valor_total,
        parcelas: v.parcelas,
        data_primeira_competencia: this.toISODate(v.data_primeira_competencia),
        data_primeiro_vencimento: this.toISODate(v.data_primeiro_vencimento),
        categoria_id: v.categoria_id ?? null,
        contato_id: v.contato_id ?? null,
        conta_bancaria_id: v.conta_bancaria_id ?? null,
        observacoes: v.observacoes ?? null,
      };
      this.svc.criarParcelado(payload).subscribe({
        next: (lancamentos) => {
          this.salvando.set(false);
          this.dialogVisivel.set(false);
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: `${lancamentos.length} parcelas criadas.` });
          this.carregarDados();
        },
        error: (err) => {
          this.salvando.set(false);
          const detail = err?.error?.detail ?? 'Erro ao criar parcelamento.';
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
        },
      });

    } else {
      if (!v.valor || !v.frequencia || !v.quantidade || !v.data_primeira_competencia || !v.data_primeiro_vencimento) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha todos os campos obrigatórios.' });
        this.salvando.set(false);
        return;
      }
      const payload: LancamentoRecorrenteCreate = {
        empresa_id: empresa.id,
        tipo: this.tipo(),
        descricao: v.descricao,
        valor: v.valor,
        data_primeira_competencia: this.toISODate(v.data_primeira_competencia),
        data_primeiro_vencimento: this.toISODate(v.data_primeiro_vencimento),
        frequencia: v.frequencia as 'semanal' | 'quinzenal' | 'mensal' | 'anual',
        quantidade: v.quantidade,
        categoria_id: v.categoria_id ?? null,
        contato_id: v.contato_id ?? null,
        conta_bancaria_id: v.conta_bancaria_id ?? null,
        observacoes: v.observacoes ?? null,
      };
      this.svc.criarRecorrente(payload).subscribe({
        next: (lancamentos) => {
          this.salvando.set(false);
          this.dialogVisivel.set(false);
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: `${lancamentos.length} recorrências criadas.` });
          this.carregarDados();
        },
        error: (err) => {
          this.salvando.set(false);
          const detail = err?.error?.detail ?? 'Erro ao criar recorrência.';
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
        },
      });
    }
  }

  protected abrirBaixa(lct: Lancamento): void {
    this.baixandoId.set(lct.id);
    const restante = Number(lct.valor) - Number(lct.valor_pago);
    this.baixaForm.reset({
      valor_pago: restante > 0 ? restante : null,
      data_pagamento: new Date(),
      conta_bancaria_id: lct.conta_bancaria_id,
      categoria_id: lct.categoria_id,
    });
    this.baixaDialogVisivel.set(true);
  }

  protected registrarBaixa(): void {
    const id = this.baixandoId();
    if (!id) return;
    const v = this.baixaForm.value;
    if (!v.valor_pago || !v.data_pagamento || !v.conta_bancaria_id || !v.categoria_id) {
      this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha todos os campos obrigatórios.' });
      return;
    }
    const payload: LancamentoBaixaCreate = {
      valor_pago: v.valor_pago,
      data_pagamento: this.toISODate(v.data_pagamento),
      conta_bancaria_id: v.conta_bancaria_id,
      categoria_id: v.categoria_id,
    };
    this.salvando.set(true);
    this.svc.registrarBaixa(id, payload).subscribe({
      next: (updated) => {
        this.lista.update(lst => lst.map(l => l.id === updated.id ? updated : l));
        this.salvando.set(false);
        this.baixaDialogVisivel.set(false);
        this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Pagamento registrado.' });
      },
      error: (err) => {
        this.salvando.set(false);
        const detail = err?.error?.detail ?? 'Erro ao registrar pagamento.';
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
      },
    });
  }

  protected confirmarCancelamento(event: Event, id: string): void {
    this.confirmSvc.confirm({
      target: event.target as EventTarget,
      message: 'Confirma o cancelamento deste lançamento?',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        this.svc.cancelar(id).subscribe({
          next: (updated) => {
            this.lista.update(lst => lst.map(l => l.id === updated.id ? updated : l));
            this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento cancelado.' });
          },
          error: (err) => {
            const detail = err?.error?.detail ?? 'Erro ao cancelar lançamento.';
            this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
          },
        });
      },
    });
  }

  protected formatDate(d: string | null): string {
    if (!d) return '—';
    const [y, m, day] = d.split('-');
    return `${day}/${m}/${y}`;
  }

  protected formatMoeda(v: number | string | null): string {
    if (v == null) return '—';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v));
  }

  protected statusSeverity(s: string): 'warn' | 'success' | 'danger' | 'secondary' {
    if (s === 'pendente') return 'warn';
    if (s === 'pago') return 'success';
    if (s === 'cancelado') return 'danger';
    return 'secondary';
  }

  protected statusLabel(s: string): string {
    if (s === 'pendente') return 'Pendente';
    if (s === 'pago') return 'Pago';
    if (s === 'cancelado') return 'Cancelado';
    return s;
  }

  // ── Anexos ──────────────────────────────────────────────────────────────────

  private carregarAnexos(lancamentoId: string): void {
    this.carregandoAnexos.set(true);
    this.svc.listarAnexos(lancamentoId).subscribe({
      next: (data) => { this.anexos.set(data); this.carregandoAnexos.set(false); },
      error: () => this.carregandoAnexos.set(false),
    });
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(false);
    Array.from(event.dataTransfer?.files ?? []).forEach(f => this.uploadFile(f));
  }

  protected onFileInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    Array.from(input.files ?? []).forEach(f => this.uploadFile(f));
    input.value = '';
  }

  private uploadFile(file: File): void {
    const id = this.editandoId();
    if (!id) return;
    this.uploadando.set(true);
    this.svc.uploadAnexo(id, file).subscribe({
      next: (anexo) => {
        this.anexos.update(l => [...l, anexo]);
        this.uploadando.set(false);
        this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: `"${file.name}" anexado.` });
      },
      error: (err) => {
        this.uploadando.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao enviar arquivo.' });
      },
    });
  }

  protected confirmarExcluirAnexo(event: Event, anexoId: string): void {
    this.confirmSvc.confirm({
      target: event.target as EventTarget,
      message: 'Excluir este anexo?',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        const id = this.editandoId();
        if (!id) return;
        this.svc.deletarAnexo(id, anexoId).subscribe({
          next: () => {
            this.anexos.update(l => l.filter(a => a.id !== anexoId));
            this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Anexo excluído.' });
          },
          error: (err) => this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro.' }),
        });
      },
    });
  }

  protected mimeIcon(mime: string): string {
    if (mime === 'application/pdf') return 'pi-file-pdf';
    if (mime.startsWith('image/')) return 'pi-image';
    if (mime.includes('spreadsheet') || mime.includes('excel') || mime === 'text/csv') return 'pi-file-excel';
    if (mime.includes('word')) return 'pi-file-word';
    return 'pi-file';
  }

  protected formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1_048_576).toFixed(1)} MB`;
  }

  protected downloadUrl(anexo: LancamentoAnexo): string {
    return this.svc.downloadUrlAnexo(anexo.lancamento_id, anexo.id);
  }
}
