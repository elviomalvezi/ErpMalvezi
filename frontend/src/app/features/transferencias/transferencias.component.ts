import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CurrencyPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { DialogModule } from 'primeng/dialog';
import { SelectModule } from 'primeng/select';
import { InputTextModule } from 'primeng/inputtext';
import { InputNumberModule } from 'primeng/inputnumber';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { TooltipModule } from 'primeng/tooltip';
import { TextareaModule } from 'primeng/textarea';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { ContaBancariaService } from '../../core/services/conta-bancaria.service';
import { TransferenciaService } from '../../core/services/transferencia.service';
import { ContaBancaria, Transferencia, TransferenciaCreate } from '../../core/models';

const MESES = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
               'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];

@Component({
  selector: 'app-transferencias',
  standalone: true,
  providers: [ConfirmationService, MessageService],
  imports: [
    FormsModule, CurrencyPipe, DatePipe,
    ButtonModule, TableModule, DialogModule, SelectModule,
    InputTextModule, InputNumberModule, TagModule,
    ToastModule, ConfirmPopupModule, TooltipModule, TextareaModule,
  ],
  template: `
<p-toast />
<p-confirmpopup />

<div class="page">
  <div class="page-header">
    <h1 class="page-title">
      <i class="pi pi-arrows-h title-icon"></i>
      Transferências
    </h1>
    <div class="header-controls">
      <div class="mes-nav">
        <p-button icon="pi pi-chevron-left" [text]="true" [rounded]="true" size="small"
          (onClick)="navegar(-1)" />
        <span class="mes-label">{{ labelMes() }}</span>
        <p-button icon="pi pi-chevron-right" [text]="true" [rounded]="true" size="small"
          (onClick)="navegar(1)" />
      </div>
      <p-select [options]="statusOpts" [(ngModel)]="filtroStatus" optionLabel="label" optionValue="value"
        placeholder="Todos os status" class="filter-select" (onChange)="pesquisar()" />
      <p-button label="Nova Transferência" icon="pi pi-plus" (onClick)="abrirDialog()" />
    </div>
  </div>

  <p-table [value]="transferenciasVisiveis()" [loading]="carregando()" size="small"
    [paginator]="true" [rows]="30" [rowsPerPageOptions]="[15,30,60]"
    styleClass="p-datatable-gridlines">
    <ng-template pTemplate="header">
      <tr>
        <th style="width:110px">Data</th>
        <th>Origem</th>
        <th style="width:36px"></th>
        <th>Destino</th>
        <th style="width:130px;text-align:right">Valor</th>
        <th>Descrição</th>
        <th style="width:110px">Status</th>
        <th style="width:70px"></th>
      </tr>
    </ng-template>
    <ng-template pTemplate="body" let-t>
      <tr>
        <td>{{ t.data_transferencia | date:'dd/MM/yyyy' }}</td>
        <td>
          <div class="conta-cell">
            <span class="empresa-nome">{{ nomeEmpresa(t.empresa_origem_id) }}</span>
            <span class="conta-nome">{{ nomeConta(t.conta_origem_id) }}</span>
          </div>
        </td>
        <td class="seta-col">
          <i class="pi pi-arrow-right seta-icon"></i>
        </td>
        <td>
          <div class="conta-cell">
            <span class="empresa-nome">{{ nomeEmpresa(t.empresa_destino_id) }}</span>
            <span class="conta-nome">{{ nomeConta(t.conta_destino_id) }}</span>
          </div>
        </td>
        <td style="text-align:right">
          {{ t.valor | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
        </td>
        <td class="descricao-cell">{{ t.descricao ?? '—' }}</td>
        <td>
          <p-tag [value]="labelStatus(t.status)" [severity]="severityStatus(t.status)" />
        </td>
        <td style="text-align:center">
          @if (t.status === 'concluida') {
            <p-button icon="pi pi-ban" [text]="true" [rounded]="true" size="small"
              severity="danger" pTooltip="Cancelar" tooltipPosition="left"
              (onClick)="confirmarCancelar($event, t.id)" />
          }
        </td>
      </tr>
    </ng-template>
    <ng-template pTemplate="emptymessage">
      <tr><td colspan="8" style="text-align:center;padding:2rem;color:var(--p-surface-400)">
        Nenhuma transferência encontrada neste período.
      </td></tr>
    </ng-template>
  </p-table>
</div>

<!-- Dialog: Nova Transferência -->
<p-dialog [visible]="dialogVisivel()" (onHide)="fecharDialog()" header="Nova Transferência" [modal]="true"
  [style]="{width:'540px'}" [draggable]="false">
  <div class="form-grid">
    <div class="form-section-title">
      <i class="pi pi-arrow-circle-up"></i> Origem
    </div>

    <div class="form-row">
      <label>Empresa de Origem <span class="req">*</span></label>
      <p-select [options]="empresaStore.empresas()" optionLabel="nome" optionValue="id"
        [(ngModel)]="fEmpresaOrigemId" (onChange)="onEmpresaOrigemChange(fEmpresaOrigemId)"
        placeholder="Selecione..." class="full-width" />
    </div>
    <div class="form-row">
      <label>Conta de Origem <span class="req">*</span></label>
      <p-select [options]="contasOrigem()" optionLabel="nome" optionValue="id"
        [(ngModel)]="fContaOrigemId" [disabled]="!fEmpresaOrigemId"
        placeholder="Selecione a empresa primeiro" class="full-width" />
    </div>

    <div class="transfer-divider">
      <span class="divider-line"></span>
      <i class="pi pi-arrows-h divider-icon"></i>
      <span class="divider-line"></span>
    </div>

    <div class="form-section-title">
      <i class="pi pi-arrow-circle-down"></i> Destino
    </div>

    <div class="form-row">
      <label>Empresa de Destino <span class="req">*</span></label>
      <p-select [options]="empresaStore.empresas()" optionLabel="nome" optionValue="id"
        [(ngModel)]="fEmpresaDestinoId" (onChange)="onEmpresaDestinoChange(fEmpresaDestinoId)"
        placeholder="Selecione..." class="full-width" />
    </div>
    <div class="form-row">
      <label>Conta de Destino <span class="req">*</span></label>
      <p-select [options]="contasDestino()" optionLabel="nome" optionValue="id"
        [(ngModel)]="fContaDestinoId" [disabled]="!fEmpresaDestinoId"
        placeholder="Selecione a empresa primeiro" class="full-width" />
    </div>

    <div class="form-section-title" style="margin-top:0.75rem">
      <i class="pi pi-wallet"></i> Dados da Transferência
    </div>

    <div class="form-row-2col">
      <div class="form-row">
        <label>Valor <span class="req">*</span></label>
        <p-inputnumber [(ngModel)]="fValor" mode="currency" currency="BRL" locale="pt-BR"
          class="full-width" [minFractionDigits]="2" />
      </div>
      <div class="form-row">
        <label>Data <span class="req">*</span></label>
        <input type="date" pInputText [(ngModel)]="fData" class="full-width" />
      </div>
    </div>

    <div class="form-row">
      <label>Descrição</label>
      <input type="text" pInputText [(ngModel)]="fDescricao" maxlength="300" class="full-width"
        placeholder="Opcional" />
    </div>
  </div>

  <ng-template pTemplate="footer">
    <p-button label="Cancelar" [text]="true" severity="secondary" (onClick)="fecharDialog()" />
    <p-button label="Transferir" icon="pi pi-arrows-h" [loading]="salvando()" (onClick)="salvar()" />
  </ng-template>
</p-dialog>
  `,
  styles: [`
    .page { padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
    .page-header { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
    .page-title { margin: 0; font-size: 1.4rem; font-weight: 700; flex: 1;
      display: flex; align-items: center; gap: 0.5rem; }
    .title-icon { font-size: 1.3rem; color: var(--p-primary-color); }
    .header-controls { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .mes-nav { display: flex; align-items: center; gap: 0.25rem; }
    .mes-label { font-size: 0.95rem; font-weight: 600; min-width: 140px; text-align: center; }
    :host ::ng-deep .filter-select { min-width: 160px; }
    .seta-col { text-align: center; padding: 0 !important; }
    .seta-icon { font-size: 0.9rem; color: var(--p-surface-400); }
    .conta-cell { display: flex; flex-direction: column; gap: 0.1rem; }
    .empresa-nome { font-size: 0.8rem; color: var(--p-surface-500); }
    .conta-nome { font-size: 0.875rem; }
    .descricao-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .form-grid { display: flex; flex-direction: column; gap: 0.75rem; padding: 0.25rem 0; }
    .form-section-title { font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.05em; color: var(--p-surface-400); border-bottom: 1px solid var(--p-surface-200);
      padding-bottom: 0.25rem; display: flex; align-items: center; gap: 0.4rem; }
    .transfer-divider { display: flex; align-items: center; gap: 0.5rem; margin: 0.25rem 0; }
    .divider-line { flex: 1; height: 1px; background: var(--p-surface-200); }
    .divider-icon { font-size: 1.1rem; color: var(--p-primary-color); padding: 0.3rem;
      background: var(--p-primary-50, #eff6ff); border-radius: 50%; }
    .form-row { display: flex; flex-direction: column; gap: 0.25rem; }
    .form-row-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
    label { font-size: 0.85rem; font-weight: 500; color: var(--p-surface-600); }
    .req { color: var(--p-red-500); }
    :host ::ng-deep .full-width { width: 100%; }
    input.full-width { width: 100%; }
    input[type="date"] { height: 2.25rem; padding: 0 0.75rem; border: 1px solid var(--p-surface-300);
      border-radius: 6px; font-size: 0.875rem; color: var(--p-surface-700);
      background: var(--p-surface-0); }
  `],
})
export class TransferenciasComponent implements OnInit {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly contaSvc = inject(ContaBancariaService);
  private readonly transferencSvc = inject(TransferenciaService);
  private readonly confirmSvc = inject(ConfirmationService);
  private readonly msgSvc = inject(MessageService);

  protected readonly transferencias = signal<Transferencia[]>([]);
  protected readonly contas = signal<ContaBancaria[]>([]);
  protected readonly carregando = signal(false);
  protected readonly salvando = signal(false);
  protected readonly dialogVisivel = signal(false);

  protected readonly mes = signal(new Date().getMonth());
  protected readonly ano = signal(new Date().getFullYear());

  protected filtroStatus = '';

  protected fEmpresaOrigemId = '';
  protected fContaOrigemId = '';
  protected fEmpresaDestinoId = '';
  protected fContaDestinoId = '';
  protected fValor = 0;
  protected fData = '';
  protected fDescricao = '';

  private readonly _empresaOrigemId = signal('');
  private readonly _empresaDestinoId = signal('');

  protected readonly contasOrigem = computed(() =>
    this.contas().filter(c => c.empresa_id === this._empresaOrigemId() && c.tipo !== 'cartao_credito')
  );
  protected readonly contasDestino = computed(() =>
    this.contas().filter(c => c.empresa_id === this._empresaDestinoId() && c.tipo !== 'cartao_credito')
  );

  protected readonly dataInicio = computed(() => {
    const d = new Date(this.ano(), this.mes(), 1);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
  });
  protected readonly dataFim = computed(() => {
    const d = new Date(this.ano(), this.mes() + 1, 0);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  });
  protected readonly labelMes = computed(() => `${MESES[this.mes()]} ${this.ano()}`);

  private readonly nomeEmpresaMap = computed(() => {
    const map = new Map<string, string>();
    this.empresaStore.empresas().forEach(e => map.set(e.id, e.nome));
    return map;
  });
  private readonly nomeContaMap = computed(() => {
    const map = new Map<string, string>();
    this.contas().forEach(c => map.set(c.id, c.nome));
    return map;
  });

  protected readonly transferenciasVisiveis = computed(() => {
    let list = this.transferencias();
    if (this.filtroStatus) list = list.filter(t => t.status === this.filtroStatus);
    return list;
  });

  protected readonly statusOpts = [
    { label: 'Todos os status', value: '' },
    { label: 'Concluída', value: 'concluida' },
    { label: 'Cancelada', value: 'cancelada' },
  ];

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
    this.transferencSvc.listar({
      dataInicio: this.dataInicio(),
      dataFim: this.dataFim(),
    }).subscribe({
      next: t => { this.transferencias.set(t); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  protected abrirDialog(): void {
    this.resetForm();
    this.dialogVisivel.set(true);
  }

  protected fecharDialog(): void {
    this.dialogVisivel.set(false);
    this.resetForm();
  }

  protected resetForm(): void {
    this.fEmpresaOrigemId = '';
    this.fContaOrigemId = '';
    this.fEmpresaDestinoId = '';
    this.fContaDestinoId = '';
    this.fValor = 0;
    this.fData = '';
    this.fDescricao = '';
    this._empresaOrigemId.set('');
    this._empresaDestinoId.set('');
  }

  protected onEmpresaOrigemChange(id: string): void {
    this._empresaOrigemId.set(id);
    this.fContaOrigemId = '';
  }

  protected onEmpresaDestinoChange(id: string): void {
    this._empresaDestinoId.set(id);
    this.fContaDestinoId = '';
  }

  protected salvar(): void {
    if (!this.fEmpresaOrigemId || !this.fContaOrigemId ||
        !this.fEmpresaDestinoId || !this.fContaDestinoId ||
        !this.fValor || !this.fData) {
      this.msgSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha todos os campos obrigatórios.' });
      return;
    }
    if (this.fContaOrigemId === this.fContaDestinoId) {
      this.msgSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Conta de origem e destino não podem ser a mesma.' });
      return;
    }
    const payload: TransferenciaCreate = {
      empresa_origem_id: this.fEmpresaOrigemId,
      empresa_destino_id: this.fEmpresaDestinoId,
      conta_origem_id: this.fContaOrigemId,
      conta_destino_id: this.fContaDestinoId,
      valor: this.fValor,
      data_transferencia: this.fData,
      descricao: this.fDescricao || null,
    };
    this.salvando.set(true);
    this.transferencSvc.criar(payload).subscribe({
      next: t => {
        this.transferencias.update(list => [t, ...list]);
        this.salvando.set(false);
        this.fecharDialog();
        this.msgSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Transferência realizada.' });
      },
      error: err => {
        this.salvando.set(false);
        this.msgSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao realizar transferência.' });
      },
    });
  }

  protected confirmarCancelar(event: Event, id: string): void {
    this.confirmSvc.confirm({
      target: event.target as EventTarget,
      message: 'Cancelar esta transferência?',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        this.transferencSvc.cancelar(id).subscribe({
          next: t => {
            this.transferencias.update(list => list.map(x => x.id === id ? t : x));
            this.msgSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Transferência cancelada.' });
          },
          error: err => this.msgSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao cancelar.' }),
        });
      },
    });
  }

  protected nomeEmpresa(id: string): string { return this.nomeEmpresaMap().get(id) ?? '—'; }
  protected nomeConta(id: string): string { return this.nomeContaMap().get(id) ?? '—'; }

  protected labelStatus(status: string): string {
    return status === 'concluida' ? 'Concluída' : 'Cancelada';
  }
  protected severityStatus(status: string): 'success' | 'danger' {
    return status === 'concluida' ? 'success' : 'danger';
  }
}
