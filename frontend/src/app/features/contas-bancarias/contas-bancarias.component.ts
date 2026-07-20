import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { MessageModule } from 'primeng/message';
import { TooltipModule } from 'primeng/tooltip';
import { ToggleSwitchModule } from 'primeng/toggleswitch';
import { DividerModule } from 'primeng/divider';
import { DatePickerModule } from 'primeng/datepicker';
import { MessageService } from 'primeng/api';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { ContaBancariaService } from '../../core/services/conta-bancaria.service';
import {
  ContaBancaria,
  ContaBancariaCreate,
  ContaBancariaUpdate,
  TipoConta,
  BandeiraCartao,
} from '../../core/models';

type FiltroTipo = 'TODOS' | 'CONTAS' | 'CARTOES';

@Component({
  selector: 'app-contas-bancarias',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule,
    ReactiveFormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    InputNumberModule,
    SelectModule,
    TagModule,
    ToastModule,
    MessageModule,
    TooltipModule,
    ToggleSwitchModule,
    DividerModule,
    DatePickerModule,
  ],
  template: `
    <p-toast />

    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Contas e Cartões</h1>
          <p class="page-subtitle">Contas bancárias e cartões de crédito</p>
        </div>
        <p-button label="Nova Conta/Cartão" icon="pi pi-plus" (onClick)="abrirNovo()" />
      </div>

      <div class="toolbar">
        <div class="filtro-tipo">
          <p-button label="Todos" [outlined]="filtroTipo() !== 'TODOS'" size="small" (onClick)="filtroTipo.set('TODOS')" />
          <p-button label="Contas" [outlined]="filtroTipo() !== 'CONTAS'" severity="info" size="small" (onClick)="filtroTipo.set('CONTAS')" />
          <p-button label="Cartões" [outlined]="filtroTipo() !== 'CARTOES'" severity="warn" size="small" (onClick)="filtroTipo.set('CARTOES')" />
        </div>
        <div class="toggle-inativos">
          <p-toggleswitch
            [ngModel]="mostrarInativos()"
            (ngModelChange)="mostrarInativos.set($event)"
            inputId="mostrarInativos"
          />
          <label for="mostrarInativos">Mostrar inativas</label>
        </div>
      </div>

      <p-table
        [value]="listaFiltrada()"
        [loading]="carregando()"
        [rowHover]="true"
        class="p-datatable-sm"
        [tableStyle]="{ 'min-width': '700px' }"
      >
        <ng-template pTemplate="header">
          <tr>
            <th>Nome</th>
            <th style="width:120px">Tipo</th>
            <th style="width:150px">Banco / Bandeira</th>
            <th style="width:130px">Saldo Inicial / Limite</th>
            <th style="width:90px">Status</th>
            <th style="width:80px">Ações</th>
          </tr>
        </ng-template>

        <ng-template pTemplate="body" let-c>
          <tr [class.row-inativo]="!c.ativa">
            <td>
              <div class="nome-cell">
                <i [class]="'pi ' + tipoIcon(c.tipo)" class="tipo-icon"></i>
                <span>{{ c.nome }}</span>
              </div>
            </td>
            <td>
              <p-tag [value]="tipoLabel(c.tipo)" [severity]="tipoSeverity(c.tipo)" />
            </td>
            <td class="banco-cell">
              @if (c.tipo === 'cartao_credito') {
                {{ c.bandeira ? bandeiraLabel(c.bandeira) : '—' }}
              } @else {
                {{ c.banco ?? '—' }}
              }
            </td>
            <td class="valor-cell">
              @if (c.tipo === 'cartao_credito') {
                {{ c.limite != null ? formatCurrency(c.limite) : '—' }}
              } @else {
                {{ formatCurrency(c.saldo_inicial) }}
              }
            </td>
            <td>
              <p-tag [value]="c.ativa ? 'Ativa' : 'Inativa'" [severity]="c.ativa ? 'success' : 'danger'" />
            </td>
            <td>
              <div class="acoes-cell">
                <p-button icon="pi pi-pencil" [text]="true" size="small" severity="secondary"
                  (onClick)="abrirEditar(c)" pTooltip="Editar" tooltipPosition="top" />
                <p-button
                  [icon]="c.ativa ? 'pi pi-ban' : 'pi pi-check-circle'"
                  [severity]="c.ativa ? 'danger' : 'success'"
                  [text]="true" size="small"
                  (onClick)="toggleAtivo(c)"
                  [pTooltip]="c.ativa ? 'Inativar' : 'Reativar'"
                  tooltipPosition="top"
                />
              </div>
            </td>
          </tr>
        </ng-template>

        <ng-template pTemplate="emptymessage">
          <tr>
            <td colspan="6" class="empty-msg">Nenhuma conta ou cartão cadastrado.</td>
          </tr>
        </ng-template>
      </p-table>
    </div>

    <!-- Dialog Nova/Editar -->
    <p-dialog
      [header]="editandoId() ? 'Editar Conta/Cartão' : 'Nova Conta/Cartão'"
      [visible]="dialogVisivel()"
      (visibleChange)="$event ? dialogVisivel.set(true) : fecharDialog()"
      [modal]="true"
      [style]="{ width: '560px', 'max-width': '95vw' }"
      [draggable]="true"
      [resizable]="false"
    >
      <form [formGroup]="form" class="dialog-form">

        <div class="section-title">Identificação</div>

        <div class="field">
          <label>Empresa *</label>
          <p-select
            formControlName="empresa_id"
            [options]="empresaOptions()"
            optionLabel="nome"
            optionValue="id"
            placeholder="Selecione a empresa"
            [style]="{ width: '100%' }"
          />
        </div>

        <div class="form-row">
          <div class="field flex-2">
            <label>Nome *</label>
            <input pInputText formControlName="nome" placeholder="Ex: Conta Bradesco, Cartão Itaú Visa" [style]="{ width: '100%' }" />
          </div>
          <div class="field">
            <label>Tipo *</label>
            <p-select
              formControlName="tipo"
              [options]="tipoOptions"
              optionLabel="label"
              optionValue="value"
              [style]="{ width: '100%' }"
              [disabled]="!!editandoId()"
            />
          </div>
        </div>

        <!-- Campos de Conta Bancária -->
        @if (tipoSelecionado() !== 'cartao_credito') {
          <p-divider />
          <div class="section-title">Dados Bancários</div>

          <div class="field">
            <label>Banco</label>
            <input pInputText formControlName="banco" placeholder="Nome do banco (opcional)" [style]="{ width: '100%' }" />
          </div>

          <div class="form-row">
            <div class="field">
              <label>Agência</label>
              <input pInputText formControlName="agencia" placeholder="0000" [style]="{ width: '100%' }" />
            </div>
            <div class="field flex-2">
              <label>Número da Conta</label>
              <input pInputText formControlName="numero_conta" placeholder="00000-0" [style]="{ width: '100%' }" />
            </div>
            <div class="field" style="max-width:70px">
              <label>Dígito</label>
              <input pInputText formControlName="digito" placeholder="0" [style]="{ width: '100%' }" />
            </div>
          </div>

          <p-divider />
          <div class="section-title">Saldo Inicial</div>
          <div class="form-row">
            <div class="field">
              <label>Saldo Inicial (R$)</label>
              <p-inputnumber
                formControlName="saldo_inicial"
                mode="decimal"
                [minFractionDigits]="2"
                [maxFractionDigits]="2"
                [style]="{ width: '100%' }"
                [inputStyle]="{ width: '100%' }"
              />
            </div>
            <div class="field">
              <label>Data do Saldo</label>
              <p-datepicker
                formControlName="data_saldo_inicial"
                dateFormat="dd/mm/yy"
                placeholder="dd/mm/aaaa"
                [style]="{ width: '100%' }"
              />
            </div>
          </div>
        }

        <!-- Campos de Cartão de Crédito -->
        @if (tipoSelecionado() === 'cartao_credito') {
          <p-divider />
          <div class="section-title">Cartão de Crédito</div>

          <div class="form-row">
            <div class="field">
              <label>Bandeira</label>
              <p-select
                formControlName="bandeira"
                [options]="bandeiraOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Selecione a bandeira"
                [style]="{ width: '100%' }"
              />
            </div>
            <div class="field">
              <label>Limite (R$) *</label>
              <p-inputnumber
                formControlName="limite"
                mode="decimal"
                [minFractionDigits]="2"
                [maxFractionDigits]="2"
                [style]="{ width: '100%' }"
                [inputStyle]="{ width: '100%' }"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="field">
              <label>Dia de Vencimento *</label>
              <p-inputnumber
                formControlName="dia_vencimento"
                placeholder="Ex: 10"
                [min]="1"
                [max]="31"
                [useGrouping]="false"
                [style]="{ width: '100%' }"
                [inputStyle]="{ width: '100%' }"
              />
            </div>
            <div class="field">
              <label>Dia de Fechamento *</label>
              <p-inputnumber
                formControlName="dia_fechamento"
                placeholder="Ex: 3"
                [min]="1"
                [max]="31"
                [useGrouping]="false"
                [style]="{ width: '100%' }"
                [inputStyle]="{ width: '100%' }"
              />
            </div>
          </div>
        }

      </form>

      <ng-template pTemplate="footer">
        @if (formErro()) {
          <p-message severity="error">{{ formErro() }}</p-message>
        }
        <div class="footer-acoes">
          <p-button label="Cancelar" severity="secondary" (onClick)="fecharDialog()" />
          <p-button
            [label]="editandoId() ? 'Salvar' : 'Criar'"
            icon="pi pi-check"
            (onClick)="salvar()"
            [loading]="salvando()"
          />
        </div>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .page { max-width: 1000px; }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1rem;
    }
    .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; }
    .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.875rem; }

    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      gap: 1rem;
      flex-wrap: wrap;
    }
    .filtro-tipo { display: flex; gap: 0.4rem; }
    .toggle-inativos {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      color: var(--p-surface-600);
    }

    .nome-cell { display: flex; align-items: center; gap: 0.5rem; }
    .tipo-icon { color: var(--p-surface-500); font-size: 0.9rem; }
    .banco-cell { font-size: 0.875rem; color: var(--p-surface-600); }
    .valor-cell { font-family: monospace; font-size: 0.875rem; }

    :host ::ng-deep .row-inativo td { opacity: 0.45; }
    .acoes-cell { display: flex; gap: 0.1rem; }

    .empty-msg {
      text-align: center;
      color: var(--p-surface-400);
      padding: 2.5rem 1rem;
      font-size: 0.9rem;
    }

    .dialog-form {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      padding: 0.25rem 0;
      max-height: 70vh;
      overflow-y: auto;
      padding-right: 0.25rem;
    }

    .section-title {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--p-surface-500);
      margin-bottom: -0.25rem;
    }

    .field { display: flex; flex-direction: column; gap: 0.3rem; flex: 1; }
    .field label { font-size: 0.8rem; font-weight: 600; }
    .field.flex-2 { flex: 2; }
    .form-row { display: flex; gap: 0.75rem; align-items: flex-start; }

    .footer-acoes {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }
  `],
})
export class ContasBancariasComponent implements OnInit {
  private readonly contaBancariaService = inject(ContaBancariaService);
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly messageService = inject(MessageService);
  private readonly fb = inject(FormBuilder);

  protected readonly lista = signal<ContaBancaria[]>([]);
  protected readonly carregando = signal(false);
  protected readonly filtroTipo = signal<FiltroTipo>('TODOS');
  protected readonly mostrarInativos = signal(false);
  protected readonly dialogVisivel = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected readonly salvando = signal(false);
  protected readonly formErro = signal<string | null>(null);
  protected readonly tipoSelecionado = signal<TipoConta>('corrente');

  protected readonly listaFiltrada = computed(() => {
    const filtro = this.filtroTipo();
    const mostrar = this.mostrarInativos();
    return this.lista().filter(c => {
      if (!mostrar && !c.ativa) return false;
      if (filtro === 'CONTAS' && c.tipo === 'cartao_credito') return false;
      if (filtro === 'CARTOES' && c.tipo !== 'cartao_credito') return false;
      return true;
    });
  });

  protected readonly empresaOptions = computed(() => this.empresaStore.empresas());

  protected readonly tipoOptions = [
    { label: 'Conta Corrente', value: 'corrente' },
    { label: 'Poupança', value: 'poupanca' },
    { label: 'Caixinha', value: 'caixinha' },
    { label: 'Aplicação', value: 'aplicacao' },
    { label: 'Cartão de Crédito', value: 'cartao_credito' },
  ];

  protected readonly bandeiraOptions = [
    { label: 'Visa', value: 'visa' },
    { label: 'Mastercard', value: 'mastercard' },
    { label: 'Elo', value: 'elo' },
    { label: 'American Express', value: 'amex' },
    { label: 'Hipercard', value: 'hipercard' },
    { label: 'Outra', value: 'outro' },
  ];

  protected readonly form = this.fb.group({
    empresa_id: ['', Validators.required],
    nome: ['', [Validators.required, Validators.minLength(2)]],
    tipo: ['corrente' as TipoConta, Validators.required],
    banco: [null as string | null],
    agencia: [null as string | null],
    numero_conta: [null as string | null],
    digito: [null as string | null],
    saldo_inicial: [0 as number | null],
    data_saldo_inicial: [null as Date | null],
    bandeira: [null as BandeiraCartao | null],
    limite: [null as number | null],
    dia_vencimento: [null as number | null],
    dia_fechamento: [null as number | null],
  });

  ngOnInit(): void {
    this.form.get('tipo')!.valueChanges.subscribe(v => {
      if (v) this.tipoSelecionado.set(v as TipoConta);
    });
    this.carregar();
  }

  private carregar(): void {
    const empresaId = this.empresaStore.empresaAtiva()?.id;
    this.carregando.set(true);
    this.contaBancariaService.listar({ empresaId, apenasAtivas: false }).subscribe({
      next: (data) => { this.lista.set(data); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  protected abrirNovo(): void {
    this.editandoId.set(null);
    this.formErro.set(null);
    const empresaId = this.empresaStore.empresaAtiva()?.id ?? '';
    this.form.reset({
      empresa_id: empresaId,
      nome: '', tipo: 'corrente',
      banco: null, agencia: null, numero_conta: null, digito: null,
      saldo_inicial: 0, data_saldo_inicial: null,
      bandeira: null, limite: null, dia_vencimento: null, dia_fechamento: null,
    });
    this.form.get('tipo')?.enable();
    this.tipoSelecionado.set('corrente');
    this.dialogVisivel.set(true);
  }

  protected abrirEditar(c: ContaBancaria): void {
    this.editandoId.set(c.id);
    this.formErro.set(null);
    this.form.patchValue({
      empresa_id: c.empresa_id,
      nome: c.nome,
      tipo: c.tipo,
      banco: c.banco,
      agencia: c.agencia,
      numero_conta: c.numero_conta,
      digito: c.digito,
      saldo_inicial: c.saldo_inicial,
      data_saldo_inicial: c.data_saldo_inicial ? new Date(c.data_saldo_inicial) : null,
      bandeira: c.bandeira,
      limite: c.limite,
      dia_vencimento: c.dia_vencimento,
      dia_fechamento: c.dia_fechamento,
    });
    this.form.get('tipo')?.disable();
    this.tipoSelecionado.set(c.tipo);
    this.dialogVisivel.set(true);
  }

  protected fecharDialog(): void {
    this.dialogVisivel.set(false);
    this.formErro.set(null);
  }

  protected salvar(): void {
    this.formErro.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.formErro.set('Preencha todos os campos obrigatórios.');
      return;
    }

    const v = this.form.getRawValue();
    const tipo = v.tipo as TipoConta;
    const isCartao = tipo === 'cartao_credito';

    if (isCartao && !v.limite) {
      this.formErro.set('Limite é obrigatório para cartão de crédito.');
      return;
    }
    if (isCartao && !v.dia_vencimento) {
      this.formErro.set('Dia de vencimento é obrigatório para cartão de crédito.');
      return;
    }
    if (isCartao && !v.dia_fechamento) {
      this.formErro.set('Dia de fechamento é obrigatório para cartão de crédito.');
      return;
    }

    const dataSaldoStr = v.data_saldo_inicial instanceof Date
      ? v.data_saldo_inicial.toISOString().split('T')[0]
      : null;

    if (this.editandoId()) {
      const payload: ContaBancariaUpdate = {
        nome: v.nome || undefined,
        banco: v.banco || null,
        agencia: v.agencia || null,
        numero_conta: v.numero_conta || null,
        digito: v.digito || null,
        saldo_inicial: isCartao ? undefined : (v.saldo_inicial ?? 0),
        data_saldo_inicial: isCartao ? undefined : dataSaldoStr,
        bandeira: isCartao ? (v.bandeira ?? null) : null,
        limite: isCartao ? (v.limite ?? undefined) : null,
        dia_vencimento: isCartao ? (v.dia_vencimento ?? undefined) : null,
        dia_fechamento: isCartao ? (v.dia_fechamento ?? undefined) : null,
      };
      this.salvando.set(true);
      this.contaBancariaService.atualizar(this.editandoId()!, payload).subscribe({
        next: () => {
          this.dialogVisivel.set(false);
          this.salvando.set(false);
          this.carregar();
          this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: 'Conta atualizada.' });
        },
        error: (err) => {
          this.formErro.set(this.extractError(err, 'Erro ao atualizar conta.'));
          this.salvando.set(false);
        },
      });
    } else {
      const payload: ContaBancariaCreate = {
        empresa_id: v.empresa_id!,
        nome: v.nome!,
        tipo,
        banco: isCartao ? null : (v.banco || null),
        agencia: isCartao ? null : (v.agencia || null),
        numero_conta: isCartao ? null : (v.numero_conta || null),
        digito: isCartao ? null : (v.digito || null),
        saldo_inicial: isCartao ? 0 : (v.saldo_inicial ?? 0),
        data_saldo_inicial: isCartao ? null : dataSaldoStr,
        bandeira: isCartao ? (v.bandeira ?? null) : null,
        limite: isCartao ? (v.limite ?? undefined) : undefined,
        dia_vencimento: isCartao ? (v.dia_vencimento ?? undefined) : undefined,
        dia_fechamento: isCartao ? (v.dia_fechamento ?? undefined) : undefined,
      };
      this.salvando.set(true);
      this.contaBancariaService.criar(payload).subscribe({
        next: () => {
          this.dialogVisivel.set(false);
          this.salvando.set(false);
          this.carregar();
          this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: 'Conta criada.' });
        },
        error: (err) => {
          this.formErro.set(this.extractError(err, 'Erro ao criar conta.'));
          this.salvando.set(false);
        },
      });
    }
  }

  protected toggleAtivo(c: ContaBancaria): void {
    const obs = c.ativa
      ? this.contaBancariaService.inativar(c.id)
      : this.contaBancariaService.reativar(c.id);
    obs.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Sucesso',
          detail: `Conta ${c.ativa ? 'inativada' : 'reativada'}.`,
        });
        this.carregar();
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Erro', detail: this.extractError(err, 'Erro ao alterar status.') });
      },
    });
  }

  protected tipoLabel(tipo: TipoConta): string {
    const labels: Record<TipoConta, string> = {
      corrente: 'Corrente',
      poupanca: 'Poupança',
      caixinha: 'Caixinha',
      aplicacao: 'Aplicação',
      cartao_credito: 'Cartão',
    };
    return labels[tipo];
  }

  protected tipoIcon(tipo: TipoConta): string {
    const icons: Record<TipoConta, string> = {
      corrente: 'pi-building-columns',
      poupanca: 'pi-building-columns',
      caixinha: 'pi-wallet',
      aplicacao: 'pi-chart-bar',
      cartao_credito: 'pi-credit-card',
    };
    return icons[tipo];
  }

  protected tipoSeverity(tipo: TipoConta): 'warn' | 'info' {
    return tipo === 'cartao_credito' ? 'warn' : 'info';
  }

  protected bandeiraLabel(bandeira: BandeiraCartao): string {
    const labels: Record<BandeiraCartao, string> = {
      visa: 'Visa', mastercard: 'Mastercard', elo: 'Elo',
      amex: 'American Express', hipercard: 'Hipercard', outro: 'Outra',
    };
    return labels[bandeira];
  }

  protected formatCurrency(value: number): string {
    return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  }

  private extractError(err: unknown, fallback: string): string {
    const e = err as { error?: { detail?: unknown } };
    return typeof e.error?.detail === 'string' ? e.error.detail : fallback;
  }
}
