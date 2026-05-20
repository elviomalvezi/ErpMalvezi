import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { TextareaModule } from 'primeng/textarea';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { MessageModule } from 'primeng/message';
import { TooltipModule } from 'primeng/tooltip';
import { ToggleSwitchModule } from 'primeng/toggleswitch';
import { DividerModule } from 'primeng/divider';
import { MessageService } from 'primeng/api';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { ContatoService } from '../../core/services/contato.service';
import { Contato, ContatoCreate, ContatoUpdate } from '../../core/models';

type FiltroTipo = 'TODOS' | 'CLIENTES' | 'FORNECEDORES';

@Component({
  selector: 'app-contatos',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule,
    ReactiveFormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    TextareaModule,
    SelectModule,
    TagModule,
    ToastModule,
    MessageModule,
    TooltipModule,
    ToggleSwitchModule,
    DividerModule,
  ],
  template: `
    <p-toast />

    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Clientes e Fornecedores</h1>
          <p class="page-subtitle">Cadastro unificado de contatos</p>
        </div>
        <p-button label="Novo Contato" icon="pi pi-plus" (onClick)="abrirNovo()" />
      </div>

      <div class="toolbar">
        <div class="toolbar-left">
          <div class="filtro-tipo">
            <p-button label="Todos" [outlined]="filtroTipo() !== 'TODOS'" size="small" (onClick)="filtroTipo.set('TODOS')" />
            <p-button label="Clientes" [outlined]="filtroTipo() !== 'CLIENTES'" severity="info" size="small" (onClick)="filtroTipo.set('CLIENTES')" />
            <p-button label="Fornecedores" [outlined]="filtroTipo() !== 'FORNECEDORES'" severity="warn" size="small" (onClick)="filtroTipo.set('FORNECEDORES')" />
          </div>
          <input
            pInputText
            [ngModel]="busca()"
            (ngModelChange)="busca.set($event)"
            placeholder="Buscar por nome..."
            class="busca-input"
          />
        </div>
        <div class="toggle-inativos">
          <p-toggleswitch
            [ngModel]="mostrarInativos()"
            (ngModelChange)="mostrarInativos.set($event)"
            inputId="mostrarInativos"
          />
          <label for="mostrarInativos">Mostrar inativos</label>
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
            <th style="width:150px">Documento</th>
            <th style="width:130px">Papel</th>
            <th style="width:130px">Cidade/UF</th>
            <th style="width:90px">Status</th>
            <th style="width:80px">Ações</th>
          </tr>
        </ng-template>

        <ng-template pTemplate="body" let-c>
          <tr [class.row-inativo]="!c.ativa">
            <td>
              <div class="nome-cell">
                <span class="nome-principal">{{ c.nome_principal }}</span>
                @if (c.nome_alternativo) {
                  <span class="nome-alt">{{ c.nome_alternativo }}</span>
                }
              </div>
            </td>
            <td>
              <div class="doc-cell">
                <p-tag [value]="c.tipo" severity="secondary" class="tipo-tag" />
                <span class="doc-valor">{{ formatDoc(c.documento, c.tipo) }}</span>
              </div>
            </td>
            <td>
              <p-tag [value]="papelLabel(c)" [severity]="papelSeverity(c)" />
            </td>
            <td class="cidade-cell">
              @if (c.cidade) {
                {{ c.cidade }}{{ c.uf ? '/' + c.uf : '' }}
              } @else {
                <span class="vazio">—</span>
              }
            </td>
            <td>
              <p-tag [value]="c.ativa ? 'Ativo' : 'Inativo'" [severity]="c.ativa ? 'success' : 'danger'" />
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
            <td colspan="6" class="empty-msg">Nenhum contato encontrado.</td>
          </tr>
        </ng-template>
      </p-table>
    </div>

    <!-- Dialog Nova/Editar -->
    <p-dialog
      [header]="editandoId() ? 'Editar Contato' : 'Novo Contato'"
      [visible]="dialogVisivel()"
      (visibleChange)="$event ? dialogVisivel.set(true) : fecharDialog()"
      [modal]="true"
      [style]="{ width: '640px', 'max-width': '95vw' }"
      [draggable]="false"
      [resizable]="false"
    >
      <form [formGroup]="form" class="dialog-form">

        <div class="section-title">Identificação</div>
        <div class="form-row">
          <div class="field">
            <label>Tipo *</label>
            <p-select
              formControlName="tipo"
              [options]="tipoOptions"
              optionLabel="label"
              optionValue="value"
              [style]="{ width: '100%' }"
            />
          </div>
          <div class="field flex-2">
            <label>{{ form.get('tipo')?.value === 'PJ' ? 'CNPJ' : 'CPF' }} *</label>
            <input pInputText formControlName="documento"
              [placeholder]="form.get('tipo')?.value === 'PJ' ? '00.000.000/0000-00' : '000.000.000-00'"
              [style]="{ width: '100%' }" />
          </div>
        </div>

        <div class="field">
          <label>{{ form.get('tipo')?.value === 'PJ' ? 'Razão Social' : 'Nome Completo' }} *</label>
          <input pInputText formControlName="nome_principal" placeholder="Nome principal" [style]="{ width: '100%' }" />
        </div>

        <div class="field">
          <label>{{ form.get('tipo')?.value === 'PJ' ? 'Nome Fantasia' : 'Apelido' }}</label>
          <input pInputText formControlName="nome_alternativo" placeholder="Nome alternativo (opcional)" [style]="{ width: '100%' }" />
        </div>

        <p-divider />
        <div class="section-title">Papel</div>
        <div class="form-row">
          <div class="field toggle-field">
            <p-toggleswitch formControlName="eh_cliente" inputId="ehCliente" />
            <label for="ehCliente">É cliente</label>
          </div>
          <div class="field toggle-field">
            <p-toggleswitch formControlName="eh_fornecedor" inputId="ehFornecedor" />
            <label for="ehFornecedor">É fornecedor</label>
          </div>
        </div>

        <p-divider />
        <div class="section-title">Contato</div>
        <div class="form-row">
          <div class="field flex-2">
            <label>E-mail</label>
            <input pInputText formControlName="email" type="email" placeholder="email@exemplo.com" [style]="{ width: '100%' }" />
          </div>
          <div class="field">
            <label>Telefone</label>
            <input pInputText formControlName="telefone" placeholder="(00) 0000-0000" [style]="{ width: '100%' }" />
          </div>
        </div>
        <div class="form-row">
          <div class="field">
            <label>Celular</label>
            <input pInputText formControlName="celular" placeholder="(00) 00000-0000" [style]="{ width: '100%' }" />
          </div>
          <div class="field flex-2">
            <label>Site</label>
            <input pInputText formControlName="site" placeholder="https://site.com.br" [style]="{ width: '100%' }" />
          </div>
        </div>

        <p-divider />
        <div class="section-title">Endereço</div>
        <div class="form-row">
          <div class="field">
            <label>CEP</label>
            <input pInputText formControlName="cep" placeholder="00000-000" [style]="{ width: '100%' }" />
          </div>
          <div class="field">
            <label>UF</label>
            <input pInputText formControlName="uf" placeholder="SP" maxlength="2" [style]="{ width: '100%' }" />
          </div>
        </div>
        <div class="form-row">
          <div class="field flex-3">
            <label>Logradouro</label>
            <input pInputText formControlName="logradouro" placeholder="Rua, Avenida..." [style]="{ width: '100%' }" />
          </div>
          <div class="field">
            <label>Número</label>
            <input pInputText formControlName="numero" placeholder="Nº" [style]="{ width: '100%' }" />
          </div>
        </div>
        <div class="form-row">
          <div class="field">
            <label>Complemento</label>
            <input pInputText formControlName="complemento" placeholder="Sala, Apto..." [style]="{ width: '100%' }" />
          </div>
          <div class="field">
            <label>Bairro</label>
            <input pInputText formControlName="bairro" [style]="{ width: '100%' }" />
          </div>
        </div>
        <div class="field">
          <label>Cidade</label>
          <input pInputText formControlName="cidade" [style]="{ width: '100%' }" />
        </div>

        <p-divider />
        <div class="section-title">Configurações</div>
        <div class="field">
          <label>Escopo *</label>
          <p-select
            formControlName="escopo"
            [options]="escopoOptions"
            optionLabel="label"
            optionValue="value"
            [style]="{ width: '100%' }"
          />
        </div>
        <div class="field">
          <label>Observações</label>
          <textarea pTextarea formControlName="observacoes" rows="2"
            placeholder="Observações internas (opcional)"
            [style]="{ width: '100%', resize: 'vertical' }"></textarea>
        </div>

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
    .page { max-width: 1100px; }

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
    .toolbar-left { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .filtro-tipo { display: flex; gap: 0.4rem; }
    .busca-input { width: 200px; font-size: 0.875rem; }
    .toggle-inativos {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      color: var(--p-surface-600);
    }

    .nome-cell { display: flex; flex-direction: column; gap: 0.1rem; }
    .nome-principal { font-weight: 500; }
    .nome-alt { font-size: 0.78rem; color: var(--p-surface-500); }

    .doc-cell { display: flex; align-items: center; gap: 0.4rem; }
    .tipo-tag { font-size: 0.7rem; }
    .doc-valor { font-family: monospace; font-size: 0.82rem; }

    .cidade-cell { font-size: 0.875rem; color: var(--p-surface-600); }
    .vazio { color: var(--p-surface-400); }

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
      max-height: 68vh;
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
    .field.flex-3 { flex: 3; }
    .toggle-field { flex-direction: row !important; align-items: center; gap: 0.5rem; flex: unset; }
    .toggle-field label { font-size: 0.875rem; font-weight: 400; margin-top: 0; }

    .form-row { display: flex; gap: 0.75rem; }

    .footer-acoes {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }
  `],
})
export class ContatosComponent implements OnInit {
  private readonly contatoService = inject(ContatoService);
  private readonly empresaStore = inject(EmpresaStore);
  private readonly messageService = inject(MessageService);
  private readonly fb = inject(FormBuilder);

  protected readonly lista = signal<Contato[]>([]);
  protected readonly carregando = signal(false);
  protected readonly filtroTipo = signal<FiltroTipo>('TODOS');
  protected readonly mostrarInativos = signal(false);
  protected readonly busca = signal('');
  protected readonly dialogVisivel = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected readonly salvando = signal(false);
  protected readonly formErro = signal<string | null>(null);

  protected readonly listaFiltrada = computed(() => {
    const tipo = this.filtroTipo();
    const mostrar = this.mostrarInativos();
    const busca = this.busca();
    return this.lista().filter(c => {
      if (!mostrar && !c.ativa) return false;
      if (tipo === 'CLIENTES' && !c.eh_cliente) return false;
      if (tipo === 'FORNECEDORES' && !c.eh_fornecedor) return false;
      if (busca && !c.nome_principal.toLowerCase().includes(busca.toLowerCase()) &&
          !(c.nome_alternativo ?? '').toLowerCase().includes(busca.toLowerCase())) return false;
      return true;
    });
  });

  protected readonly tipoOptions = [
    { label: 'Pessoa Jurídica (PJ)', value: 'PJ' },
    { label: 'Pessoa Física (PF)', value: 'PF' },
  ];

  protected readonly escopoOptions = [
    { label: 'Global (todas as empresas)', value: 'global' },
    { label: 'Específico (empresa ativa)', value: 'especifico' },
  ];

  protected readonly form = this.fb.group({
    tipo: ['PJ', Validators.required],
    documento: ['', Validators.required],
    nome_principal: ['', [Validators.required, Validators.minLength(2)]],
    nome_alternativo: [null as string | null],
    eh_cliente: [true],
    eh_fornecedor: [false],
    escopo: ['global', Validators.required],
    email: [null as string | null],
    telefone: [null as string | null],
    celular: [null as string | null],
    site: [null as string | null],
    cep: [null as string | null],
    logradouro: [null as string | null],
    numero: [null as string | null],
    complemento: [null as string | null],
    bairro: [null as string | null],
    cidade: [null as string | null],
    uf: [null as string | null],
    observacoes: [null as string | null],
  });

  ngOnInit(): void {
    this.carregar();
  }

  private carregar(): void {
    const empresaId = this.empresaStore.empresaAtiva()?.id;
    this.carregando.set(true);
    this.contatoService.listar({ empresaId, apenasAtivas: false }).subscribe({
      next: (data) => { this.lista.set(data); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  protected abrirNovo(): void {
    this.editandoId.set(null);
    this.formErro.set(null);
    this.form.reset({
      tipo: 'PJ', documento: '', nome_principal: '', nome_alternativo: null,
      eh_cliente: true, eh_fornecedor: false, escopo: 'global',
      email: null, telefone: null, celular: null, site: null,
      cep: null, logradouro: null, numero: null, complemento: null,
      bairro: null, cidade: null, uf: null, observacoes: null,
    });
    this.form.get('tipo')?.enable();
    this.dialogVisivel.set(true);
  }

  protected abrirEditar(c: Contato): void {
    this.editandoId.set(c.id);
    this.formErro.set(null);
    this.form.patchValue({
      tipo: c.tipo,
      documento: c.documento,
      nome_principal: c.nome_principal,
      nome_alternativo: c.nome_alternativo,
      eh_cliente: c.eh_cliente,
      eh_fornecedor: c.eh_fornecedor,
      escopo: c.escopo,
      email: c.email,
      telefone: c.telefone,
      celular: c.celular,
      site: c.site,
      cep: c.cep,
      logradouro: c.logradouro,
      numero: c.numero,
      complemento: c.complemento,
      bairro: c.bairro,
      cidade: c.cidade,
      uf: c.uf,
      observacoes: c.observacoes,
    });
    this.form.get('tipo')?.disable();
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
    if (!v.eh_cliente && !v.eh_fornecedor) {
      this.formErro.set('O contato deve ser cliente, fornecedor ou ambos.');
      return;
    }

    if (this.editandoId()) {
      const payload: ContatoUpdate = {
        documento: v.documento || undefined,
        nome_principal: v.nome_principal || undefined,
        nome_alternativo: v.nome_alternativo || null,
        eh_cliente: v.eh_cliente ?? undefined,
        eh_fornecedor: v.eh_fornecedor ?? undefined,
        escopo: v.escopo as 'global' | 'especifico' | undefined,
        empresa_id: v.escopo === 'especifico' ? (this.empresaStore.empresaAtiva()?.id ?? null) : null,
        email: v.email || null,
        telefone: v.telefone || null,
        celular: v.celular || null,
        site: v.site || null,
        cep: v.cep || null,
        logradouro: v.logradouro || null,
        numero: v.numero || null,
        complemento: v.complemento || null,
        bairro: v.bairro || null,
        cidade: v.cidade || null,
        uf: v.uf || null,
        observacoes: v.observacoes || null,
      };
      this.salvando.set(true);
      this.contatoService.atualizar(this.editandoId()!, payload).subscribe({
        next: () => {
          this.dialogVisivel.set(false);
          this.salvando.set(false);
          this.carregar();
          this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: 'Contato atualizado.' });
        },
        error: (err) => {
          this.formErro.set(this.extractError(err, 'Erro ao atualizar contato.'));
          this.salvando.set(false);
        },
      });
    } else {
      const payload: ContatoCreate = {
        tipo: v.tipo as 'PJ' | 'PF',
        documento: v.documento!,
        nome_principal: v.nome_principal!,
        nome_alternativo: v.nome_alternativo || null,
        eh_cliente: v.eh_cliente ?? true,
        eh_fornecedor: v.eh_fornecedor ?? false,
        escopo: v.escopo as 'global' | 'especifico',
        empresa_id: v.escopo === 'especifico' ? (this.empresaStore.empresaAtiva()?.id ?? null) : null,
        email: v.email || null,
        telefone: v.telefone || null,
        celular: v.celular || null,
        site: v.site || null,
        cep: v.cep || null,
        logradouro: v.logradouro || null,
        numero: v.numero || null,
        complemento: v.complemento || null,
        bairro: v.bairro || null,
        cidade: v.cidade || null,
        uf: v.uf || null,
        observacoes: v.observacoes || null,
      };
      this.salvando.set(true);
      this.contatoService.criar(payload).subscribe({
        next: () => {
          this.dialogVisivel.set(false);
          this.salvando.set(false);
          this.carregar();
          this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: 'Contato criado.' });
        },
        error: (err) => {
          this.formErro.set(this.extractError(err, 'Erro ao criar contato.'));
          this.salvando.set(false);
        },
      });
    }
  }

  protected toggleAtivo(c: Contato): void {
    const obs = c.ativa ? this.contatoService.inativar(c.id) : this.contatoService.reativar(c.id);
    obs.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Sucesso',
          detail: `Contato ${c.ativa ? 'inativado' : 'reativado'}.`,
        });
        this.carregar();
      },
      error: (err) => {
        this.messageService.add({ severity: 'error', summary: 'Erro', detail: this.extractError(err, 'Erro ao alterar status.') });
      },
    });
  }

  protected papelLabel(c: Contato): string {
    if (c.eh_cliente && c.eh_fornecedor) return 'Cliente/Fornecedor';
    if (c.eh_cliente) return 'Cliente';
    return 'Fornecedor';
  }

  protected papelSeverity(c: Contato): 'info' | 'warn' | 'secondary' {
    if (c.eh_cliente && c.eh_fornecedor) return 'secondary';
    if (c.eh_cliente) return 'info';
    return 'warn';
  }

  protected formatDoc(doc: string, tipo: 'PJ' | 'PF'): string {
    if (tipo === 'PJ' && doc.length === 14) {
      return `${doc.slice(0, 2)}.${doc.slice(2, 5)}.${doc.slice(5, 8)}/${doc.slice(8, 12)}-${doc.slice(12)}`;
    }
    if (tipo === 'PF' && doc.length === 11) {
      return `${doc.slice(0, 3)}.${doc.slice(3, 6)}.${doc.slice(6, 9)}-${doc.slice(9)}`;
    }
    return doc;
  }

  private extractError(err: unknown, fallback: string): string {
    const e = err as { error?: { detail?: unknown } };
    return typeof e.error?.detail === 'string' ? e.error.detail : fallback;
  }
}
