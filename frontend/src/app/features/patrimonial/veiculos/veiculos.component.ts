import { DecimalPipe } from '@angular/common';
import { Component, computed, effect, inject, signal, untracked } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
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

import { EmpresaStore } from '../../../core/stores/empresa.store';
import { PatrimonioService } from '../../../core/services/patrimonio.service';
import { AnexosPanelComponent } from '../../../shared/components/anexos-panel/anexos-panel.component';
import type { CombustivelVeiculo, Lancamento, StatusVeiculo, Veiculo, VeiculoCreate, VeiculoUpdate } from '../../../core/models';

type FiltroStatus = 'TODOS' | StatusVeiculo;

@Component({
  selector: 'app-veiculos',
  standalone: true,
  providers: [ConfirmationService, MessageService],
  imports: [
    DecimalPipe, ReactiveFormsModule,
    ButtonModule, TableModule, DialogModule, TagModule, ToastModule,
    InputTextModule, InputNumberModule, SelectModule, DatePickerModule,
    TextareaModule, DividerModule, ConfirmPopupModule, TooltipModule,
    AnexosPanelComponent,
  ],
  template: `
<p-toast />
<p-confirmpopup />

@if (!empresaAtiva()) {
  <p class="sem-empresa">Selecione uma empresa para visualizar os veículos.</p>
} @else {
  <div class="section-header">
    <div class="header-left">
      <h2 class="section-title">Veículos</h2>
      <span class="count-badge">{{ listaFiltrada().length }}</span>
    </div>
    <p-button label="Novo Veículo" icon="pi pi-plus" (onClick)="abrirCriar()" />
  </div>

  <div class="filtro-bar">
    @for (opt of statusOpts; track opt.value) {
      <p-button
        [label]="opt.label"
        [outlined]="filtroStatus() !== opt.value"
        size="small"
        (onClick)="filtroStatus.set(opt.value)"
      />
    }
    <div class="spacer"></div>
    <p-button
      [label]="mostrarInativos() ? 'Ocultar inativos' : 'Mostrar inativos'"
      [outlined]="true"
      size="small"
      severity="secondary"
      (onClick)="mostrarInativos.set(!mostrarInativos())"
    />
  </div>

  <p-table
    [value]="listaFiltrada()"
    [loading]="loading()"
    [paginator]="true"
    [rows]="15"
    [rowsPerPageOptions]="[15, 30, 50]"
    [showCurrentPageReport]="true"
    currentPageReportTemplate="{first}–{last} de {totalRecords}"
    size="small"
  >
    <ng-template pTemplate="header">
      <tr>
        <th>Veículo</th>
        <th>Placa</th>
        <th>Ano</th>
        <th>Combustível</th>
        <th class="col-right">Quilometragem</th>
        <th class="col-right">Valor Aquisição</th>
        <th class="col-right">Valor Mercado</th>
        <th>Status</th>
        <th style="width:6rem"></th>
      </tr>
    </ng-template>
    <ng-template pTemplate="body" let-v>
      <tr [class.row-inativo]="!v.ativo">
        <td>
          <div class="veiculo-nome">{{ v.marca }} {{ v.modelo }}</div>
          @if (v.cor) { <div class="veiculo-detalhe">{{ v.cor }}</div> }
        </td>
        <td>{{ v.placa ?? '—' }}</td>
        <td>
          {{ v.ano_fabricacao }}
          @if (v.ano_modelo && v.ano_modelo !== v.ano_fabricacao) {
            <span class="ano-modelo">/{{ v.ano_modelo }}</span>
          }
        </td>
        <td>{{ combustivelLabel(v.combustivel) }}</td>
        <td class="col-right">{{ v.quilometragem != null ? (v.quilometragem | number:'1.0-0':'pt-BR') + ' km' : '—' }}</td>
        <td class="col-right">{{ formatMoeda(v.valor_aquisicao) }}</td>
        <td class="col-right">{{ v.valor_mercado ? formatMoeda(v.valor_mercado) : '—' }}</td>
        <td><p-tag [value]="statusLabel(v.status)" [severity]="statusSeverity(v.status)" /></td>
        <td>
          <div class="acoes">
            <p-button icon="pi pi-pencil" [text]="true" [rounded]="true" size="small"
              pTooltip="Editar" tooltipPosition="left" (onClick)="abrirEditar(v)" />
            @if (v.ativo) {
              <p-button icon="pi pi-ban" [text]="true" [rounded]="true" size="small"
                severity="danger" pTooltip="Inativar" tooltipPosition="left"
                (onClick)="confirmarInativar($event, v.id)" />
            } @else {
              <p-button icon="pi pi-check-circle" [text]="true" [rounded]="true" size="small"
                severity="success" pTooltip="Reativar" tooltipPosition="left"
                (onClick)="reativar(v.id)" />
            }
          </div>
        </td>
      </tr>
    </ng-template>
    <ng-template pTemplate="emptymessage">
      <tr><td colspan="9" class="empty-msg">Nenhum veículo cadastrado.</td></tr>
    </ng-template>
  </p-table>
}

<!-- Dialog -->
<p-dialog
  [header]="editandoId() ? 'Editar Veículo' : 'Novo Veículo'"
  [visible]="dialogVisivel()"
  (visibleChange)="dialogVisivel.set($event)"
  [modal]="true" [style]="{width: '720px'}" [closeOnEscape]="true"
>
  <form [formGroup]="form" (ngSubmit)="salvar()">
    <div class="form-section">
      <h4 class="form-section-title">Identificação</h4>
      <div class="form-grid">
        <div class="field">
          <label>Marca *</label>
          <input pInputText formControlName="marca" placeholder="Ex: Toyota" class="w-full" />
        </div>
        <div class="field">
          <label>Modelo *</label>
          <input pInputText formControlName="modelo" placeholder="Ex: Corolla" class="w-full" />
        </div>
        <div class="field">
          <label>Placa</label>
          <input pInputText formControlName="placa" placeholder="Ex: ABC-1234" class="w-full" />
        </div>
        <div class="field">
          <label>RENAVAM</label>
          <input pInputText formControlName="renavam" class="w-full" />
        </div>
        <div class="field">
          <label>Chassi</label>
          <input pInputText formControlName="chassi" class="w-full" />
        </div>
        <div class="field">
          <label>Número do Motor</label>
          <input pInputText formControlName="numero_motor" class="w-full" />
        </div>
      </div>
    </div>

    <p-divider />

    <div class="form-section">
      <h4 class="form-section-title">Características</h4>
      <div class="form-grid">
        <div class="field">
          <label>Ano Fabricação *</label>
          <p-inputNumber formControlName="ano_fabricacao" [useGrouping]="false" [min]="1900" [max]="2100" class="w-full" />
        </div>
        <div class="field">
          <label>Ano Modelo</label>
          <p-inputNumber formControlName="ano_modelo" [useGrouping]="false" [min]="1900" [max]="2100" class="w-full" />
        </div>
        <div class="field">
          <label>Cor</label>
          <input pInputText formControlName="cor" placeholder="Ex: Prata" class="w-full" />
        </div>
        <div class="field">
          <label>Combustível</label>
          <p-select formControlName="combustivel" [options]="combustivelOpts"
            optionLabel="label" optionValue="value" [showClear]="true"
            placeholder="Selecione" class="w-full" />
        </div>
        <div class="field">
          <label>Quilometragem</label>
          <p-inputNumber formControlName="quilometragem" [min]="0" suffix=" km" locale="pt-BR" class="w-full" />
        </div>
        @if (editandoId()) {
          <div class="field">
            <label>Status</label>
            <p-select formControlName="status" [options]="statusEditOpts"
              optionLabel="label" optionValue="value" class="w-full" />
          </div>
        }
      </div>
    </div>

    <p-divider />

    <div class="form-section">
      <h4 class="form-section-title">Valores</h4>
      <div class="form-grid">
        <div class="field">
          <label>Valor de Aquisição *</label>
          <p-inputNumber formControlName="valor_aquisicao" mode="currency" currency="BRL" locale="pt-BR" class="w-full" />
        </div>
        <div class="field">
          <label>Data de Aquisição</label>
          <p-datepicker formControlName="data_aquisicao" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
        <div class="field full">
          <label>Valor de Mercado Atual</label>
          <p-inputNumber formControlName="valor_mercado" mode="currency" currency="BRL" locale="pt-BR" class="w-full" />
        </div>
      </div>
    </div>

    <p-divider />

    <div class="form-section">
      <h4 class="form-section-title">Observações</h4>
      <textarea pTextarea formControlName="observacoes" rows="3" class="w-full" placeholder="Informações adicionais..."></textarea>
    </div>

    @if (editandoId()) {
      <p-divider />
      <app-anexos-panel
        [registroId]="editandoId()"
        [listarFn]="listarAnexos"
        [uploadFn]="uploadAnexo"
        [deletarFn]="deletarAnexo"
        [downloadUrlFn]="downloadUrl"
      />

      <p-divider />
      <div class="form-section">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
          <h4 class="form-section-title" style="margin:0">Lançamentos Vinculados</h4>
          @if (carregandoLancamentos()) {
            <i class="pi pi-spin pi-spinner" style="font-size:0.85rem;color:var(--p-surface-400)"></i>
          }
        </div>
        @if (lancamentosVeiculo().length === 0) {
          <p class="lancamentos-vazio">Nenhum lançamento vinculado a este veículo.</p>
        } @else {
          <div class="lancamentos-lista">
            @for (lct of lancamentosVeiculo(); track lct.id) {
              <div class="lancamento-item" [class.lct-pago]="lct.status === 'pago'" [class.lct-cancelado]="lct.status === 'cancelado'">
                <span class="lct-data">{{ formatData(lct.data_vencimento) }}</span>
                <span class="lct-desc">{{ lct.descricao }}</span>
                <span class="lct-valor" [class.lct-receita]="lct.tipo === 'RECEITA'">{{ formatMoeda(lct.valor) }}</span>
                <span class="lct-status">{{ lct.status }}</span>
              </div>
            }
          </div>
        }
      </div>
    }

    <div class="dialog-footer">
      <p-button label="Cancelar" [outlined]="true" type="button" (onClick)="fecharDialog()" />
      <p-button [label]="editandoId() ? 'Salvar' : 'Cadastrar'" type="submit" [loading]="salvando()" />
    </div>
  </form>
</p-dialog>
  `,
  styles: [`
    .sem-empresa { color: var(--p-surface-500); }
    .section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
    .header-left { display: flex; align-items: center; gap: 0.75rem; }
    .section-title { margin: 0; font-size: 1.25rem; font-weight: 700; }
    .count-badge { background: var(--p-surface-200); color: var(--p-surface-600); padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }
    .filtro-bar { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; margin-bottom: 1rem; }
    .spacer { flex: 1; }
    .col-right { text-align: right; }
    .acoes { display: flex; gap: 0.125rem; justify-content: flex-end; }
    .row-inativo td { opacity: 0.5; }
    .veiculo-nome { font-weight: 500; }
    .veiculo-detalhe { font-size: 0.8rem; color: var(--p-surface-500); }
    .ano-modelo { color: var(--p-surface-400); font-size: 0.85rem; }
    .empty-msg { text-align: center; padding: 2rem; color: var(--p-surface-500); }
    .form-section { margin-bottom: 0.5rem; }
    .form-section-title { margin: 0 0 0.75rem; font-size: 0.85rem; font-weight: 600; color: var(--p-surface-500); text-transform: uppercase; letter-spacing: 0.05em; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.875rem 1.5rem; }
    .field { display: flex; flex-direction: column; gap: 0.25rem; }
    .field.full { grid-column: 1 / -1; }
    label { font-size: 0.875rem; font-weight: 500; }
    .dialog-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--p-surface-200); }
    .lancamentos-vazio { font-size: 0.85rem; color: var(--p-surface-400); margin: 0; }
    .lancamentos-lista { display: flex; flex-direction: column; gap: 0.25rem; max-height: 200px; overflow-y: auto; }
    .lancamento-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.35rem 0.5rem; border-radius: 6px; border: 1px solid var(--p-surface-200); font-size: 0.82rem; }
    .lancamento-item.lct-pago { opacity: 0.7; }
    .lancamento-item.lct-cancelado { opacity: 0.45; text-decoration: line-through; }
    .lct-data { color: var(--p-surface-500); white-space: nowrap; min-width: 70px; }
    .lct-desc { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .lct-valor { white-space: nowrap; font-weight: 600; }
    .lct-receita { color: var(--p-green-600); }
    .lct-status { font-size: 0.75rem; color: var(--p-surface-400); white-space: nowrap; }
  `],
})
export class VeiculosComponent {
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(PatrimonioService);
  private readonly confirmSvc = inject(ConfirmationService);
  private readonly messageSvc = inject(MessageService);
  protected readonly empresaStore = inject(EmpresaStore);

  protected readonly empresaAtiva = computed(() => this.empresaStore.empresaAtiva());
  protected readonly lista = signal<Veiculo[]>([]);
  protected readonly loading = signal(false);
  protected readonly salvando = signal(false);
  protected readonly filtroStatus = signal<FiltroStatus>('TODOS');
  protected readonly mostrarInativos = signal(false);
  protected readonly dialogVisivel = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected readonly lancamentosVeiculo = signal<Lancamento[]>([]);
  protected readonly carregandoLancamentos = signal(false);

  protected readonly listaFiltrada = computed(() => {
    const status = this.filtroStatus();
    const inativos = this.mostrarInativos();
    return this.lista().filter(v => {
      if (!inativos && !v.ativo) return false;
      if (status !== 'TODOS' && v.status !== status) return false;
      return true;
    });
  });

  readonly statusOpts: { label: string; value: FiltroStatus }[] = [
    { label: 'Todos', value: 'TODOS' },
    { label: 'Ativo', value: 'ativo' },
    { label: 'Vendido', value: 'vendido' },
    { label: 'Sinistrado', value: 'sinistrado' },
    { label: 'Inativo', value: 'inativo' },
  ];

  readonly statusEditOpts = [
    { label: 'Ativo', value: 'ativo' },
    { label: 'Vendido', value: 'vendido' },
    { label: 'Sinistrado', value: 'sinistrado' },
    { label: 'Inativo', value: 'inativo' },
  ];

  readonly combustivelOpts: { label: string; value: CombustivelVeiculo }[] = [
    { label: 'Gasolina', value: 'gasolina' },
    { label: 'Etanol', value: 'etanol' },
    { label: 'Flex', value: 'flex' },
    { label: 'Diesel', value: 'diesel' },
    { label: 'Elétrico', value: 'eletrico' },
    { label: 'Híbrido', value: 'hibrido' },
    { label: 'GNV', value: 'gnv' },
  ];

  readonly form = this.fb.group({
    marca: ['', [Validators.required, Validators.minLength(1)]],
    modelo: ['', [Validators.required, Validators.minLength(1)]],
    placa: [null as string | null],
    renavam: [null as string | null],
    chassi: [null as string | null],
    numero_motor: [null as string | null],
    ano_fabricacao: [new Date().getFullYear() as number | null, Validators.required],
    ano_modelo: [null as number | null],
    cor: [null as string | null],
    combustivel: [null as CombustivelVeiculo | null],
    quilometragem: [null as number | null],
    status: ['ativo' as string | null],
    valor_aquisicao: [null as number | null, [Validators.required, Validators.min(0.01)]],
    data_aquisicao: [null as Date | null],
    valor_mercado: [null as number | null],
    observacoes: [null as string | null],
  });

  constructor() {
    effect(() => {
      if (this.empresaStore.empresaAtiva()) untracked(() => this.carregarDados());
    });
  }

  private carregarDados(): void {
    const empresa = this.empresaAtiva();
    if (!empresa) return;
    this.loading.set(true);
    this.svc.listarVeiculos({ empresaId: empresa.id, apenasAtivos: false }).subscribe({
      next: (data) => { this.lista.set(data); this.loading.set(false); },
      error: () => {
        this.loading.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar veículos.' });
      },
    });
  }

  readonly listarAnexos = (id: string) => this.svc.listarAnexosVeiculo(id);
  readonly uploadAnexo = (id: string, file: File) => this.svc.uploadAnexoVeiculo(id, file);
  readonly deletarAnexo = (id: string, anexoId: string) => this.svc.deletarAnexoVeiculo(id, anexoId);
  readonly downloadUrl = (id: string, anexoId: string) => this.svc.downloadUrlVeiculo(id, anexoId);

  protected fecharDialog(): void {
    this.editandoId.set(null);
    this.dialogVisivel.set(false);
  }

  protected abrirCriar(): void {
    this.editandoId.set(null);
    this.form.reset({ ano_fabricacao: new Date().getFullYear(), status: 'ativo' });
    this.dialogVisivel.set(true);
  }

  protected abrirEditar(v: Veiculo): void {
    this.editandoId.set(v.id);
    this.carregarLancamentosVeiculo(v.id);
    this.form.reset({
      marca: v.marca,
      modelo: v.modelo,
      placa: v.placa,
      renavam: v.renavam,
      chassi: v.chassi,
      numero_motor: v.numero_motor,
      ano_fabricacao: v.ano_fabricacao,
      ano_modelo: v.ano_modelo,
      cor: v.cor,
      combustivel: v.combustivel,
      quilometragem: v.quilometragem,
      status: v.status,
      valor_aquisicao: Number(v.valor_aquisicao),
      data_aquisicao: v.data_aquisicao ? new Date(v.data_aquisicao + 'T00:00:00') : null,
      valor_mercado: v.valor_mercado ? Number(v.valor_mercado) : null,
      observacoes: v.observacoes,
    });
    this.dialogVisivel.set(true);
  }

  protected salvar(): void {
    const empresa = this.empresaAtiva();
    if (!empresa || this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const fv = this.form.value;
    const id = this.editandoId();

    if (id) {
      const payload: VeiculoUpdate = {
        marca: fv.marca ?? undefined,
        modelo: fv.modelo ?? undefined,
        placa: fv.placa,
        renavam: fv.renavam,
        chassi: fv.chassi,
        numero_motor: fv.numero_motor,
        ano_fabricacao: fv.ano_fabricacao ?? undefined,
        ano_modelo: fv.ano_modelo,
        cor: fv.cor,
        combustivel: fv.combustivel as CombustivelVeiculo | null,
        quilometragem: fv.quilometragem,
        status: fv.status as StatusVeiculo | null,
        valor_aquisicao: fv.valor_aquisicao ?? undefined,
        data_aquisicao: fv.data_aquisicao ? this.toISO(fv.data_aquisicao) : null,
        valor_mercado: fv.valor_mercado,
        observacoes: fv.observacoes,
      };
      this.salvando.set(true);
      this.svc.atualizarVeiculo(id, payload).subscribe({
        next: (updated) => {
          this.lista.update(l => l.map(x => x.id === updated.id ? updated : x));
          this.salvando.set(false);
          this.fecharDialog();
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Veículo atualizado.' });
        },
        error: (err) => {
          this.salvando.set(false);
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao atualizar.' });
        },
      });
    } else {
      if (!fv.marca || !fv.modelo || !fv.ano_fabricacao || !fv.valor_aquisicao) return;
      const payload: VeiculoCreate = {
        empresa_id: empresa.id,
        marca: fv.marca,
        modelo: fv.modelo,
        placa: fv.placa,
        renavam: fv.renavam,
        chassi: fv.chassi,
        numero_motor: fv.numero_motor,
        ano_fabricacao: fv.ano_fabricacao,
        ano_modelo: fv.ano_modelo,
        cor: fv.cor,
        combustivel: fv.combustivel as CombustivelVeiculo | null,
        quilometragem: fv.quilometragem,
        valor_aquisicao: fv.valor_aquisicao,
        data_aquisicao: fv.data_aquisicao ? this.toISO(fv.data_aquisicao) : null,
        valor_mercado: fv.valor_mercado,
        observacoes: fv.observacoes,
      };
      this.salvando.set(true);
      this.svc.criarVeiculo(payload).subscribe({
        next: (created) => {
          this.lista.update(l => [...l, created]);
          this.salvando.set(false);
          this.fecharDialog();
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Veículo cadastrado.' });
        },
        error: (err) => {
          this.salvando.set(false);
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao cadastrar.' });
        },
      });
    }
  }

  protected confirmarInativar(event: Event, id: string): void {
    this.confirmSvc.confirm({
      target: event.target as EventTarget,
      message: 'Inativar este veículo?',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        this.svc.inativarVeiculo(id).subscribe({
          next: (updated) => {
            this.lista.update(l => l.map(x => x.id === updated.id ? updated : x));
            this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Veículo inativado.' });
          },
          error: (err) => this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro.' }),
        });
      },
    });
  }

  protected reativar(id: string): void {
    this.svc.reativarVeiculo(id).subscribe({
      next: (updated) => {
        this.lista.update(l => l.map(x => x.id === updated.id ? updated : x));
        this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Veículo reativado.' });
      },
      error: (err) => this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro.' }),
    });
  }

  protected combustivelLabel(c: CombustivelVeiculo | null): string {
    return this.combustivelOpts.find(o => o.value === c)?.label ?? '—';
  }

  protected statusSeverity(s: StatusVeiculo): 'success' | 'warn' | 'danger' | 'secondary' {
    if (s === 'ativo') return 'success';
    if (s === 'vendido') return 'secondary';
    if (s === 'sinistrado') return 'danger';
    return 'secondary';
  }

  protected statusLabel(s: StatusVeiculo): string {
    const m: Record<StatusVeiculo, string> = {
      ativo: 'Ativo', vendido: 'Vendido', sinistrado: 'Sinistrado', inativo: 'Inativo',
    };
    return m[s] ?? s;
  }

  private carregarLancamentosVeiculo(id: string): void {
    this.carregandoLancamentos.set(true);
    this.lancamentosVeiculo.set([]);
    this.svc.listarLancamentosVeiculo(id).subscribe({
      next: (data) => { this.lancamentosVeiculo.set(data); this.carregandoLancamentos.set(false); },
      error: () => this.carregandoLancamentos.set(false),
    });
  }

  protected formatMoeda(v: number | null): string {
    if (v == null) return '—';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v));
  }

  protected formatData(d: string | null): string {
    if (!d) return '—';
    const [y, m, day] = d.split('-');
    return `${day}/${m}/${y}`;
  }

  private toISO(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
}
