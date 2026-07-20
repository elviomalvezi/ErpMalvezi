import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { MessageModule } from 'primeng/message';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ConfirmDialogModule } from 'primeng/confirmdialog';

import { AuthStore } from '../../core/stores/auth.store';
import { EmpresaStore } from '../../core/stores/empresa.store';
import { EmpresaService } from '../../core/services/empresa.service';
import { EmpresaCreate, EmpresaListItem, EmpresaUpdate, RegimeTributario, TipoPessoa } from '../../core/models';

@Component({
  selector: 'app-empresas',
  standalone: true,
  providers: [MessageService, ConfirmationService],
  imports: [
    ReactiveFormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    SelectModule,
    TagModule,
    ToastModule,
    MessageModule,
    TooltipModule,
    ConfirmDialogModule,
  ],
  template: `
    <p-toast />
    <p-confirmdialog />

    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Empresas</h1>
          <p class="page-subtitle">Gerencie as empresas vinculadas à sua conta</p>
        </div>
        <p-button label="Nova Empresa" icon="pi pi-plus" (onClick)="abrirNovo()" />
      </div>

      <p-table
        [value]="lista()"
        [loading]="carregando()"
        [rowHover]="true"
        class="p-datatable-sm"
        [tableStyle]="{ 'min-width': '600px' }"
      >
        <ng-template pTemplate="header">
          <tr>
            <th style="width:70px">Tipo</th>
            <th style="width:160px">Documento</th>
            <th>Nome</th>
            <th style="width:90px">Status</th>
            <th style="width:100px">Ações</th>
          </tr>
        </ng-template>

        <ng-template pTemplate="body" let-e>
          <tr [class.row-inativa]="!e.ativa">
            <td>
              <p-tag
                [value]="e.tipo"
                [severity]="e.tipo === 'PJ' ? 'info' : 'secondary'"
              />
            </td>
            <td class="doc-cell">{{ formatarDocumento(e.documento, e.tipo) }}</td>
            <td>
              <span class="nome-principal">{{ e.nome_principal }}</span>
              @if (e.nome_alternativo) {
                <span class="nome-alt"> · {{ e.nome_alternativo }}</span>
              }
            </td>
            <td>
              <p-tag
                [value]="e.ativa ? 'Ativa' : 'Inativa'"
                [severity]="e.ativa ? 'success' : 'danger'"
              />
            </td>
            <td>
              <div class="acoes">
                <p-button
                  icon="pi pi-pencil"
                  severity="secondary"
                  [text]="true"
                  size="small"
                  (onClick)="abrirEditar(e)"
                  pTooltip="Editar"
                  tooltipPosition="top"
                />
                <p-button
                  [icon]="e.ativa ? 'pi pi-ban' : 'pi pi-check-circle'"
                  [severity]="e.ativa ? 'danger' : 'success'"
                  [text]="true"
                  size="small"
                  (onClick)="toggleAtiva(e)"
                  [pTooltip]="e.ativa ? 'Inativar' : 'Reativar'"
                  tooltipPosition="top"
                />
                @if (authStore.admin()) {
                  <p-button
                    icon="pi pi-trash"
                    severity="danger"
                    [text]="true"
                    size="small"
                    (onClick)="confirmarExclusao(e)"
                    pTooltip="Excluir permanentemente"
                    tooltipPosition="top"
                  />
                }
              </div>
            </td>
          </tr>
        </ng-template>

        <ng-template pTemplate="emptymessage">
          <tr>
            <td colspan="5" class="empty-msg">
              Nenhuma empresa cadastrada. Clique em "Nova Empresa" para começar.
            </td>
          </tr>
        </ng-template>
      </p-table>
    </div>

    <p-dialog
      [header]="editandoId() ? 'Editar Empresa' : 'Nova Empresa'"
      [visible]="dialogVisivel()"
      (visibleChange)="$event ? dialogVisivel.set(true) : fecharDialog()"
      [modal]="true"
      [style]="{ width: '640px', 'max-width': '95vw' }"
      [draggable]="true"
      [resizable]="false"
    >
      <form [formGroup]="form" class="dialog-form">

        <div class="section-title">Dados Básicos</div>

        <div class="field-row">
          <div class="field">
            <label>Tipo *</label>
            <p-select
              formControlName="tipo"
              [options]="tiposOpcoes"
              optionLabel="label"
              optionValue="value"
              [style]="{ width: '100%' }"
            />
          </div>
          <div class="field field-grow">
            <label>{{ tipoSelecionado === 'PJ' ? 'CNPJ' : 'CPF' }} *</label>
            <input
              pInputText
              formControlName="documento"
              [placeholder]="tipoSelecionado === 'PJ' ? '00.000.000/0000-00' : '000.000.000-00'"
              [maxlength]="tipoSelecionado === 'PJ' ? 18 : 14"
              (input)="formatarDocumentoInput($event)"
              [style]="{ width: '100%' }"
            />
          </div>
        </div>

        <div class="field-row">
          <div class="field field-grow">
            <label>Razão Social / Nome *</label>
            <input pInputText formControlName="nome_principal" placeholder="Nome oficial" [style]="{ width: '100%' }" />
          </div>
          <div class="field field-grow">
            <label>Nome Fantasia / Apelido</label>
            <input pInputText formControlName="nome_alternativo" placeholder="Opcional" [style]="{ width: '100%' }" />
          </div>
        </div>

        @if (tipoSelecionado === 'PJ') {
          <div class="field">
            <label>Regime Tributário *</label>
            <p-select
              formControlName="regime_tributario"
              [options]="regimesOpcoes"
              optionLabel="label"
              optionValue="value"
              placeholder="Selecione o regime"
              [style]="{ width: '100%' }"
            />
          </div>
        }

        <div class="section-title">Endereço</div>

        <div class="field-row">
          <div class="field" style="flex:0 0 150px">
            <label>CEP</label>
            <input pInputText formControlName="endereco_cep" placeholder="00000-000" maxlength="9" [style]="{ width: '100%' }" />
          </div>
          <div class="field field-grow">
            <label>Logradouro</label>
            <input pInputText formControlName="logradouro" placeholder="Rua, Av..." [style]="{ width: '100%' }" />
          </div>
          <div class="field" style="flex:0 0 100px">
            <label>Número</label>
            <input pInputText formControlName="numero" placeholder="Nº" [style]="{ width: '100%' }" />
          </div>
        </div>

        <div class="field-row">
          <div class="field field-grow">
            <label>Complemento</label>
            <input pInputText formControlName="complemento" placeholder="Sala, andar..." [style]="{ width: '100%' }" />
          </div>
          <div class="field field-grow">
            <label>Bairro</label>
            <input pInputText formControlName="bairro" [style]="{ width: '100%' }" />
          </div>
        </div>

        <div class="field-row">
          <div class="field field-grow">
            <label>Cidade</label>
            <input pInputText formControlName="cidade" [style]="{ width: '100%' }" />
          </div>
          <div class="field" style="flex:0 0 70px">
            <label>UF</label>
            <input pInputText formControlName="uf" maxlength="2" placeholder="SP" [style]="{ width: '100%' }" />
          </div>
          <div class="field field-grow">
            <label>Telefone</label>
            <input pInputText formControlName="telefone" placeholder="(11) 99999-9999" [style]="{ width: '100%' }" />
          </div>
        </div>

        <div class="field">
          <label>E-mail da empresa</label>
          <input pInputText formControlName="email" type="email" placeholder="contato@empresa.com.br" [style]="{ width: '100%' }" />
        </div>

      </form>

      <ng-template pTemplate="footer">
        @if (formErro()) {
          <p-message severity="error">{{ formErro() }}</p-message>
        }
        <div class="footer-acoes">
          <p-button
            label="Cancelar"
            severity="secondary"
            (onClick)="fecharDialog()"
          />
          <p-button
            label="Salvar"
            icon="pi pi-check"
            (onClick)="salvar()"
            [loading]="salvando()"
          />
        </div>
      </ng-template>
    </p-dialog>
  `,
  styles: [
    `
      .page { max-width: 1100px; }

      .page-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1.5rem;
      }
      .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; }
      .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.875rem; }

      .doc-cell { font-family: monospace; font-size: 0.875rem; }
      .nome-principal { font-weight: 500; }
      .nome-alt { font-size: 0.85rem; color: var(--p-surface-400); }

      .acoes { display: flex; gap: 0.25rem; }

      :host ::ng-deep .row-inativa td { opacity: 0.5; }

      .empty-msg {
        text-align: center;
        color: var(--p-surface-400);
        padding: 2.5rem 1rem;
        font-size: 0.9rem;
      }

      .dialog-form {
        display: flex;
        flex-direction: column;
        gap: 0.875rem;
        padding: 0.25rem 0;
      }

      .section-title {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: var(--p-surface-400);
        border-bottom: 1px solid var(--p-surface-100);
        padding-bottom: 0.35rem;
        margin-top: 0.25rem;
      }

      .field {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
      }

      .field label {
        font-size: 0.8rem;
        font-weight: 600;
      }

      .field-row {
        display: flex;
        gap: 0.875rem;
        flex-wrap: wrap;
      }

      .field-grow { flex: 1 1 180px; }

      .footer-acoes {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
      }
    `,
  ],
})
export class EmpresasComponent implements OnInit {
  private readonly empresaStore = inject(EmpresaStore);
  private readonly empresaService = inject(EmpresaService);
  private readonly messageService = inject(MessageService);
  private readonly confirmationService = inject(ConfirmationService);
  private readonly fb = inject(FormBuilder);

  protected readonly authStore = inject(AuthStore);

  protected readonly lista = signal<EmpresaListItem[]>([]);
  protected readonly carregando = signal(false);
  protected readonly dialogVisivel = signal(false);
  protected readonly salvando = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected readonly formErro = signal<string | null>(null);

  protected readonly tiposOpcoes = [
    { label: 'Pessoa Jurídica (PJ)', value: 'PJ' },
    { label: 'Pessoa Física (PF)', value: 'PF' },
  ];

  protected readonly regimesOpcoes = [
    { label: 'Simples Nacional', value: 'Simples' },
    { label: 'Lucro Presumido', value: 'Presumido' },
    { label: 'Lucro Real', value: 'Real' },
    { label: 'MEI', value: 'MEI' },
  ];

  protected readonly form = this.fb.group({
    tipo: ['PJ' as TipoPessoa, Validators.required],
    documento: ['', Validators.required],
    nome_principal: ['', [Validators.required, Validators.minLength(2)]],
    nome_alternativo: [''],
    regime_tributario: [null as RegimeTributario | null],
    endereco_cep: [''],
    logradouro: [''],
    numero: [''],
    complemento: [''],
    bairro: [''],
    cidade: [''],
    uf: [''],
    telefone: [''],
    email: [''],
  });

  protected get tipoSelecionado(): TipoPessoa {
    return (this.form.getRawValue().tipo ?? 'PJ') as TipoPessoa;
  }

  protected get maskDocumento(): string {
    return this.tipoSelecionado === 'PJ' ? '99.999.999/9999-99' : '999.999.999-99';
  }

  protected formatarDocumentoInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    let digits = input.value.replace(/\D/g, '');
    let formatted: string;
    if (this.tipoSelecionado === 'PJ') {
      digits = digits.slice(0, 14);
      formatted = digits
        .replace(/^(\d{2})(\d)/, '$1.$2')
        .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
        .replace(/\.(\d{3})(\d)/, '.$1/$2')
        .replace(/(\d{4})(\d)/, '$1-$2');
    } else {
      digits = digits.slice(0, 11);
      formatted = digits
        .replace(/^(\d{3})(\d)/, '$1.$2')
        .replace(/^(\d{3})\.(\d{3})(\d)/, '$1.$2.$3')
        .replace(/\.(\d{3})(\d)/, '.$1-$2');
    }
    input.value = formatted;
    this.form.get('documento')?.setValue(formatted, { emitEvent: false });
  }

  ngOnInit(): void {
    this.form.get('tipo')!.valueChanges.subscribe(() => {
      this.form.get('documento')?.reset('');
      if (this.tipoSelecionado === 'PF') {
        this.form.get('regime_tributario')?.reset(null);
      }
    });
    this.carregar();
  }

  private carregar(): void {
    this.carregando.set(true);
    this.empresaService.listar().subscribe({
      next: (data) => {
        this.lista.set(data);
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }

  protected fecharDialog(): void {
    this.dialogVisivel.set(false);
    this.formErro.set(null);
  }

  protected abrirNovo(): void {
    this.editandoId.set(null);
    this.formErro.set(null);
    this.form.get('tipo')?.enable();
    this.form.get('documento')?.enable();
    this.form.reset({ tipo: 'PJ', regime_tributario: null });
    this.dialogVisivel.set(true);
  }

  protected abrirEditar(empresa: EmpresaListItem): void {
    this.editandoId.set(empresa.id);
    this.formErro.set(null);
    this.carregando.set(true);
    this.empresaService.obter(empresa.id).subscribe({
      next: (e) => {
        this.form.patchValue({
          tipo: e.tipo,
          documento: e.documento,
          nome_principal: e.nome_principal,
          nome_alternativo: e.nome_alternativo ?? '',
          regime_tributario: e.regime_tributario,
          endereco_cep: e.endereco_cep ?? '',
          logradouro: e.logradouro ?? '',
          numero: e.numero ?? '',
          complemento: e.complemento ?? '',
          bairro: e.bairro ?? '',
          cidade: e.cidade ?? '',
          uf: e.uf ?? '',
          telefone: e.telefone ?? '',
          email: e.email ?? '',
        });
        this.carregando.set(false);
        this.dialogVisivel.set(true);
      },
      error: () => {
        this.carregando.set(false);
        this.editandoId.set(null);
        this.messageService.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível carregar os dados.' });
      },
    });
  }

  protected salvar(): void {
    this.formErro.set(null);
    const v = this.form.getRawValue();

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.formErro.set('Preencha os campos obrigatórios (Nome e Documento são obrigatórios).');
      return;
    }

    if (!this.editandoId() && this.tipoSelecionado === 'PJ' && !v.regime_tributario) {
      this.formErro.set('Regime tributário é obrigatório para Pessoa Jurídica.');
      return;
    }

    const docDigitos = (v.documento ?? '').replace(/\D/g, '');
    const tamanhoEsperado = this.tipoSelecionado === 'PJ' ? 14 : 11;
    if (docDigitos.length !== tamanhoEsperado) {
      this.formErro.set(`${this.tipoSelecionado === 'PJ' ? 'CNPJ' : 'CPF'} incompleto — informe todos os dígitos.`);
      return;
    }

    this.salvando.set(true);

    const id = this.editandoId();
    if (id) {
      const payload: EmpresaUpdate = {
        tipo: v.tipo as TipoPessoa,
        documento: docDigitos,
        nome_principal: v.nome_principal ?? undefined,
        nome_alternativo: v.nome_alternativo || null,
        regime_tributario: (v.regime_tributario as RegimeTributario) || null,
        endereco_cep: v.endereco_cep || null,
        logradouro: v.logradouro || null,
        numero: v.numero || null,
        complemento: v.complemento || null,
        bairro: v.bairro || null,
        cidade: v.cidade || null,
        uf: v.uf || null,
        telefone: v.telefone || null,
        email: v.email || null,
      };
      this.empresaService.atualizar(id, payload).subscribe({
        next: () => this.onSucesso('Empresa atualizada com sucesso.'),
        error: (err) => this.onErro(err),
      });
    } else {
      const payload: EmpresaCreate = {
        tipo: v.tipo as TipoPessoa,
        documento: docDigitos,
        nome_principal: v.nome_principal ?? '',
        nome_alternativo: v.nome_alternativo || null,
        regime_tributario: (v.regime_tributario as RegimeTributario) || null,
        endereco_cep: v.endereco_cep || null,
        logradouro: v.logradouro || null,
        numero: v.numero || null,
        complemento: v.complemento || null,
        bairro: v.bairro || null,
        cidade: v.cidade || null,
        uf: v.uf || null,
        telefone: v.telefone || null,
        email: v.email || null,
      };
      this.empresaService.criar(payload).subscribe({
        next: () => this.onSucesso('Empresa criada com sucesso.'),
        error: (err) => this.onErro(err),
      });
    }
  }

  protected confirmarExclusao(empresa: EmpresaListItem): void {
    this.confirmationService.confirm({
      header: 'Excluir empresa',
      message: `Deseja excluir permanentemente "${empresa.nome_principal}"? Esta ação não pode ser desfeita.`,
      acceptLabel: 'Excluir',
      rejectLabel: 'Cancelar',
      acceptButtonProps: { severity: 'danger' },
      accept: () => {
        this.empresaService.excluir(empresa.id).subscribe({
          next: () => {
            this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: 'Empresa excluída.' });
            this.recarregarListas();
          },
          error: (err) => this.onErro(err),
        });
      },
    });
  }

  protected toggleAtiva(empresa: EmpresaListItem): void {
    const obs = empresa.ativa
      ? this.empresaService.inativar(empresa.id)
      : this.empresaService.reativar(empresa.id);
    obs.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Sucesso',
          detail: `Empresa ${empresa.ativa ? 'inativada' : 'reativada'} com sucesso.`,
        });
        this.recarregarListas();
      },
      error: (err) => this.onErro(err),
    });
  }

  protected formatarDocumento(doc: string | null, tipo: string): string {
    if (!doc) return '—';
    const d = doc.replace(/\D/g, '');
    if (tipo === 'PJ' && d.length === 14) {
      return d.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
    if (tipo === 'PF' && d.length === 11) {
      return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    return doc;
  }

  private onSucesso(msg: string): void {
    this.dialogVisivel.set(false);
    this.formErro.set(null);
    this.salvando.set(false);
    this.recarregarListas();
    this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: msg });
  }

  private onErro(err: { error?: { detail?: unknown } }): void {
    const detail =
      typeof err.error?.detail === 'string'
        ? err.error.detail
        : 'Verifique os dados e tente novamente.';
    this.formErro.set(detail);
    this.salvando.set(false);
  }

  private recarregarListas(): void {
    this.carregar();
    this.empresaStore.carregar();
  }
}
