import { DecimalPipe } from '@angular/common';
import { Component, computed, effect, inject, signal, untracked } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
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
import type { Imovel, ImovelCreate, ImovelUpdate, StatusImovel, TipoImovel } from '../../../core/models';

type FiltroStatus = 'TODOS' | StatusImovel;

@Component({
  selector: 'app-imoveis',
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
  <p class="sem-empresa">Selecione uma empresa para visualizar os imóveis.</p>
} @else {
  <div class="section-header">
    <div class="header-left">
      <h2 class="section-title">Imóveis</h2>
      <span class="count-badge">{{ listaFiltrada().length }}</span>
    </div>
    <p-button label="Novo Imóvel" icon="pi pi-plus" (onClick)="abrirCriar()" />
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
        <th>Tipo</th>
        <th>Descrição</th>
        <th>Cidade / UF</th>
        <th class="col-right">Área Total</th>
        <th class="col-right">Valor Aquisição</th>
        <th class="col-right">Valor Mercado</th>
        <th>Status</th>
        <th style="width:6rem"></th>
      </tr>
    </ng-template>
    <ng-template pTemplate="body" let-im>
      <tr [class.row-inativo]="!im.ativo">
        <td><p-tag [value]="tipoLabel(im.tipo)" severity="secondary" /></td>
        <td>
          <div class="imovel-descricao">{{ im.descricao }}</div>
          @if (im.matricula) { <div class="imovel-detalhe">Mat.: {{ im.matricula }}</div> }
        </td>
        <td>
          @if (im.cidade || im.uf) {
            {{ im.cidade }}{{ im.cidade && im.uf ? ' / ' : '' }}{{ im.uf }}
          } @else {
            —
          }
        </td>
        <td class="col-right">{{ im.area_total != null ? (im.area_total | number:'1.0-2':'pt-BR') + ' m²' : '—' }}</td>
        <td class="col-right">{{ formatMoeda(im.valor_aquisicao) }}</td>
        <td class="col-right">{{ im.valor_mercado ? formatMoeda(im.valor_mercado) : '—' }}</td>
        <td><p-tag [value]="statusLabel(im.status)" [severity]="statusSeverity(im.status)" /></td>
        <td>
          <div class="acoes">
            <p-button icon="pi pi-pencil" [text]="true" [rounded]="true" size="small"
              pTooltip="Editar" tooltipPosition="left" (onClick)="abrirEditar(im)" />
            @if (im.ativo) {
              <p-button icon="pi pi-ban" [text]="true" [rounded]="true" size="small"
                severity="danger" pTooltip="Inativar" tooltipPosition="left"
                (onClick)="confirmarInativar($event, im.id)" />
            } @else {
              <p-button icon="pi pi-check-circle" [text]="true" [rounded]="true" size="small"
                severity="success" pTooltip="Reativar" tooltipPosition="left"
                (onClick)="reativar(im.id)" />
            }
          </div>
        </td>
      </tr>
    </ng-template>
    <ng-template pTemplate="emptymessage">
      <tr><td colspan="8" class="empty-msg">Nenhum imóvel cadastrado.</td></tr>
    </ng-template>
  </p-table>
}

<!-- Dialog -->
<p-dialog
  [header]="editandoId() ? 'Editar Imóvel' : 'Novo Imóvel'"
  [visible]="dialogVisivel()"
  (visibleChange)="dialogVisivel.set($event)"
  [modal]="true" [style]="{width: '760px'}" [closeOnEscape]="true"
>
  <form [formGroup]="form" (ngSubmit)="salvar()">

    <div class="form-section">
      <h4 class="form-section-title">Identificação</h4>
      <div class="form-grid">
        <div class="field">
          <label>Tipo *</label>
          <p-select formControlName="tipo" [options]="tipoOpts"
            optionLabel="label" optionValue="value"
            placeholder="Selecione" class="w-full" />
        </div>
        <div class="field">
          <label>Matrícula</label>
          <input pInputText formControlName="matricula" placeholder="Nº de matrícula no cartório" class="w-full" />
        </div>
        <div class="field full">
          <label>Descrição *</label>
          <input pInputText formControlName="descricao" placeholder="Ex: Apartamento Avenida Paulista" class="w-full" />
        </div>
        <div class="field">
          <label>Inscrição Municipal (IPTU)</label>
          <input pInputText formControlName="inscricao_municipal" class="w-full" />
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
      <h4 class="form-section-title">Endereço</h4>
      <div class="form-grid">
        <div class="field">
          <label>CEP</label>
          <div class="cep-row">
            <input pInputText formControlName="cep" placeholder="00000-000"
              class="w-full" maxlength="9" (blur)="buscarCep()" />
            @if (buscandoCep()) {
              <i class="pi pi-spin pi-spinner cep-spinner"></i>
            }
          </div>
        </div>
        <div class="field">
          <label>UF</label>
          <input pInputText formControlName="uf" maxlength="2" placeholder="SP" class="w-full" />
        </div>
        <div class="field full">
          <label>Logradouro</label>
          <input pInputText formControlName="logradouro" placeholder="Rua / Av. / Praça" class="w-full" />
        </div>
        <div class="field">
          <label>Número</label>
          <input pInputText formControlName="numero" class="w-full" />
        </div>
        <div class="field">
          <label>Complemento</label>
          <input pInputText formControlName="complemento" placeholder="Apto, Bloco..." class="w-full" />
        </div>
        <div class="field">
          <label>Bairro</label>
          <input pInputText formControlName="bairro" class="w-full" />
        </div>
        <div class="field">
          <label>Cidade</label>
          <input pInputText formControlName="cidade" class="w-full" />
        </div>
      </div>
    </div>

    <p-divider />

    <div class="form-section">
      <h4 class="form-section-title">Características / Áreas</h4>
      <div class="form-grid">
        <div class="field">
          <label>Área Total (m²)</label>
          <p-inputNumber formControlName="area_total" [min]="0" suffix=" m²" locale="pt-BR" [maxFractionDigits]="2" class="w-full" />
        </div>
        <div class="field">
          <label>Área Construída (m²)</label>
          <p-inputNumber formControlName="area_construida" [min]="0" suffix=" m²" locale="pt-BR" [maxFractionDigits]="2" class="w-full" />
        </div>
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
        <div class="field">
          <label>Valor de Mercado Atual</label>
          <p-inputNumber formControlName="valor_mercado" mode="currency" currency="BRL" locale="pt-BR" class="w-full" />
        </div>
        <div class="field">
          <label>Valor Venal (IPTU)</label>
          <p-inputNumber formControlName="valor_venal" mode="currency" currency="BRL" locale="pt-BR" class="w-full" />
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
    .imovel-descricao { font-weight: 500; }
    .imovel-detalhe { font-size: 0.8rem; color: var(--p-surface-500); }
    .empty-msg { text-align: center; padding: 2rem; color: var(--p-surface-500); }
    .form-section { margin-bottom: 0.5rem; }
    .form-section-title { margin: 0 0 0.75rem; font-size: 0.85rem; font-weight: 600; color: var(--p-surface-500); text-transform: uppercase; letter-spacing: 0.05em; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.875rem 1.5rem; }
    .field { display: flex; flex-direction: column; gap: 0.25rem; }
    .field.full { grid-column: 1 / -1; }
    label { font-size: 0.875rem; font-weight: 500; }
    .dialog-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--p-surface-200); }
    .cep-row { position: relative; display: flex; align-items: center; }
    .cep-spinner { position: absolute; right: 0.5rem; color: var(--p-surface-400); }
  `],
})
export class ImoveisComponent {
  private readonly fb = inject(FormBuilder);
  private readonly http = inject(HttpClient);
  private readonly svc = inject(PatrimonioService);
  private readonly confirmSvc = inject(ConfirmationService);
  private readonly messageSvc = inject(MessageService);
  protected readonly empresaStore = inject(EmpresaStore);

  protected readonly empresaAtiva = computed(() => this.empresaStore.empresaAtiva());
  protected readonly lista = signal<Imovel[]>([]);
  protected readonly loading = signal(false);
  protected readonly salvando = signal(false);
  protected readonly buscandoCep = signal(false);
  protected readonly filtroStatus = signal<FiltroStatus>('TODOS');
  protected readonly mostrarInativos = signal(false);
  protected readonly dialogVisivel = signal(false);
  protected readonly editandoId = signal<string | null>(null);

  protected readonly listaFiltrada = computed(() => {
    const status = this.filtroStatus();
    const inativos = this.mostrarInativos();
    return this.lista().filter(im => {
      if (!inativos && !im.ativo) return false;
      if (status !== 'TODOS' && im.status !== status) return false;
      return true;
    });
  });

  readonly statusOpts: { label: string; value: FiltroStatus }[] = [
    { label: 'Todos', value: 'TODOS' },
    { label: 'Ativo', value: 'ativo' },
    { label: 'Locado', value: 'locado' },
    { label: 'Vendido', value: 'vendido' },
    { label: 'Em Reforma', value: 'em_reforma' },
    { label: 'Inativo', value: 'inativo' },
  ];

  readonly statusEditOpts = [
    { label: 'Ativo', value: 'ativo' },
    { label: 'Locado', value: 'locado' },
    { label: 'Vendido', value: 'vendido' },
    { label: 'Em Reforma', value: 'em_reforma' },
    { label: 'Inativo', value: 'inativo' },
  ];

  readonly tipoOpts: { label: string; value: TipoImovel }[] = [
    { label: 'Casa', value: 'casa' },
    { label: 'Apartamento', value: 'apartamento' },
    { label: 'Terreno', value: 'terreno' },
    { label: 'Sala Comercial', value: 'sala_comercial' },
    { label: 'Galpão', value: 'galpao' },
    { label: 'Loja', value: 'loja' },
    { label: 'Outro', value: 'outro' },
  ];

  readonly form = this.fb.group({
    tipo: [null as TipoImovel | null, Validators.required],
    descricao: ['', [Validators.required, Validators.minLength(1)]],
    matricula: [null as string | null],
    inscricao_municipal: [null as string | null],
    status: ['ativo' as string | null],
    cep: [null as string | null],
    logradouro: [null as string | null],
    numero: [null as string | null],
    complemento: [null as string | null],
    bairro: [null as string | null],
    cidade: [null as string | null],
    uf: [null as string | null],
    area_total: [null as number | null],
    area_construida: [null as number | null],
    valor_aquisicao: [null as number | null, [Validators.required, Validators.min(0.01)]],
    data_aquisicao: [null as Date | null],
    valor_mercado: [null as number | null],
    valor_venal: [null as number | null],
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
    this.svc.listarImoveis({ empresaId: empresa.id, apenasAtivos: false }).subscribe({
      next: (data) => { this.lista.set(data); this.loading.set(false); },
      error: () => {
        this.loading.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar imóveis.' });
      },
    });
  }

  protected buscarCep(): void {
    const cep = (this.form.value.cep ?? '').replace(/\D/g, '');
    if (cep.length !== 8) return;
    this.buscandoCep.set(true);
    this.http.get<{ logradouro: string; bairro: string; localidade: string; uf: string; erro?: boolean }>(
      `https://viacep.com.br/ws/${cep}/json/`
    ).subscribe({
      next: (res) => {
        this.buscandoCep.set(false);
        if (res.erro) return;
        this.form.patchValue({
          logradouro: res.logradouro || null,
          bairro: res.bairro || null,
          cidade: res.localidade || null,
          uf: res.uf || null,
        });
      },
      error: () => this.buscandoCep.set(false),
    });
  }

  readonly listarAnexos = (id: string) => this.svc.listarAnexosImovel(id);
  readonly uploadAnexo = (id: string, file: File) => this.svc.uploadAnexoImovel(id, file);
  readonly deletarAnexo = (id: string, anexoId: string) => this.svc.deletarAnexoImovel(id, anexoId);
  readonly downloadUrl = (id: string, anexoId: string) => this.svc.downloadUrlImovel(id, anexoId);

  protected fecharDialog(): void {
    this.editandoId.set(null);
    this.dialogVisivel.set(false);
  }

  protected abrirCriar(): void {
    this.editandoId.set(null);
    this.form.reset({ status: 'ativo' });
    this.dialogVisivel.set(true);
  }

  protected abrirEditar(im: Imovel): void {
    this.editandoId.set(im.id);
    this.form.reset({
      tipo: im.tipo,
      descricao: im.descricao,
      matricula: im.matricula,
      inscricao_municipal: im.inscricao_municipal,
      status: im.status,
      cep: im.cep,
      logradouro: im.logradouro,
      numero: im.numero,
      complemento: im.complemento,
      bairro: im.bairro,
      cidade: im.cidade,
      uf: im.uf,
      area_total: im.area_total ? Number(im.area_total) : null,
      area_construida: im.area_construida ? Number(im.area_construida) : null,
      valor_aquisicao: Number(im.valor_aquisicao),
      data_aquisicao: im.data_aquisicao ? new Date(im.data_aquisicao + 'T00:00:00') : null,
      valor_mercado: im.valor_mercado ? Number(im.valor_mercado) : null,
      valor_venal: im.valor_venal ? Number(im.valor_venal) : null,
      observacoes: im.observacoes,
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
      const payload: ImovelUpdate = {
        tipo: fv.tipo as TipoImovel | null ?? undefined,
        descricao: fv.descricao ?? undefined,
        matricula: fv.matricula,
        inscricao_municipal: fv.inscricao_municipal,
        status: fv.status as StatusImovel | null ?? undefined,
        cep: fv.cep,
        logradouro: fv.logradouro,
        numero: fv.numero,
        complemento: fv.complemento,
        bairro: fv.bairro,
        cidade: fv.cidade,
        uf: fv.uf,
        area_total: fv.area_total,
        area_construida: fv.area_construida,
        valor_aquisicao: fv.valor_aquisicao ?? undefined,
        data_aquisicao: fv.data_aquisicao ? this.toISO(fv.data_aquisicao) : null,
        valor_mercado: fv.valor_mercado,
        valor_venal: fv.valor_venal,
        observacoes: fv.observacoes,
      };
      this.salvando.set(true);
      this.svc.atualizarImovel(id, payload).subscribe({
        next: (updated) => {
          this.lista.update(l => l.map(x => x.id === updated.id ? updated : x));
          this.salvando.set(false);
          this.fecharDialog();
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Imóvel atualizado.' });
        },
        error: (err) => {
          this.salvando.set(false);
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao atualizar.' });
        },
      });
    } else {
      if (!fv.tipo || !fv.descricao || !fv.valor_aquisicao) return;
      const payload: ImovelCreate = {
        empresa_id: empresa.id,
        tipo: fv.tipo,
        descricao: fv.descricao,
        matricula: fv.matricula,
        inscricao_municipal: fv.inscricao_municipal,
        cep: fv.cep,
        logradouro: fv.logradouro,
        numero: fv.numero,
        complemento: fv.complemento,
        bairro: fv.bairro,
        cidade: fv.cidade,
        uf: fv.uf,
        area_total: fv.area_total,
        area_construida: fv.area_construida,
        valor_aquisicao: fv.valor_aquisicao,
        data_aquisicao: fv.data_aquisicao ? this.toISO(fv.data_aquisicao) : null,
        valor_mercado: fv.valor_mercado,
        valor_venal: fv.valor_venal,
        observacoes: fv.observacoes,
      };
      this.salvando.set(true);
      this.svc.criarImovel(payload).subscribe({
        next: (created) => {
          this.lista.update(l => [...l, created]);
          this.salvando.set(false);
          this.fecharDialog();
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Imóvel cadastrado.' });
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
      message: 'Inativar este imóvel?',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        this.svc.inativarImovel(id).subscribe({
          next: (updated) => {
            this.lista.update(l => l.map(x => x.id === updated.id ? updated : x));
            this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Imóvel inativado.' });
          },
          error: (err) => this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro.' }),
        });
      },
    });
  }

  protected reativar(id: string): void {
    this.svc.reativarImovel(id).subscribe({
      next: (updated) => {
        this.lista.update(l => l.map(x => x.id === updated.id ? updated : x));
        this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Imóvel reativado.' });
      },
      error: (err) => this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro.' }),
    });
  }

  protected tipoLabel(t: TipoImovel): string {
    return this.tipoOpts.find(o => o.value === t)?.label ?? t;
  }

  protected statusSeverity(s: StatusImovel): 'success' | 'warn' | 'danger' | 'secondary' | 'info' {
    if (s === 'ativo') return 'success';
    if (s === 'locado') return 'info';
    if (s === 'em_reforma') return 'warn';
    if (s === 'vendido') return 'secondary';
    return 'secondary';
  }

  protected statusLabel(s: StatusImovel): string {
    const m: Record<StatusImovel, string> = {
      ativo: 'Ativo', locado: 'Locado', vendido: 'Vendido', em_reforma: 'Em Reforma', inativo: 'Inativo',
    };
    return m[s] ?? s;
  }

  protected formatMoeda(v: number | null): string {
    if (v == null) return '—';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v));
  }

  private toISO(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }
}
