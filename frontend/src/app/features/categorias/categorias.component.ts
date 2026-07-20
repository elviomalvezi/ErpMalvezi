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
import { CheckboxModule } from 'primeng/checkbox';
import { MessageService } from 'primeng/api';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { CategoriaService } from '../../core/services/categoria.service';
import { Categoria, CategoriaCreate, CategoriaUpdate } from '../../core/models';

type FiltroTipo = 'TODOS' | 'RECEITA' | 'DESPESA';

@Component({
  selector: 'app-categorias',
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
    CheckboxModule,
  ],
  template: `
    <p-toast />

    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Categorias</h1>
          <p class="page-subtitle">Plano de contas para classificação de lançamentos</p>
        </div>
        <div class="header-acoes">
          @if (listaVazia()) {
            <p-button
              label="Inicializar Plano Padrão"
              icon="pi pi-sitemap"
              severity="secondary"
              (onClick)="inicializarPlano()"
              [loading]="inicializando()"
              pTooltip="Cria um conjunto de categorias comuns para começar"
              tooltipPosition="left"
            />
          }
          <p-button label="Nova Categoria" icon="pi pi-plus" (onClick)="abrirNovo()" />
        </div>
      </div>

      <div class="toolbar">
        <div class="filtro-tipo">
          <p-button
            label="Todos"
            [outlined]="filtroTipo() !== 'TODOS'"
            size="small"
            (onClick)="filtroTipo.set('TODOS')"
          />
          <p-button
            label="Receitas"
            [outlined]="filtroTipo() !== 'RECEITA'"
            severity="success"
            size="small"
            (onClick)="filtroTipo.set('RECEITA')"
          />
          <p-button
            label="Despesas"
            [outlined]="filtroTipo() !== 'DESPESA'"
            severity="danger"
            size="small"
            (onClick)="filtroTipo.set('DESPESA')"
          />
        </div>
        <div class="toggle-inativas">
          <p-toggleswitch
            [ngModel]="mostrarInativas()"
            (ngModelChange)="mostrarInativas.set($event)"
            inputId="mostrarInativas"
          />
          <label for="mostrarInativas">Mostrar inativas</label>
        </div>
      </div>

      <p-table
        [value]="listaFiltrada()"
        [loading]="carregando()"
        [rowHover]="true"
        class="p-datatable-sm"
        [tableStyle]="{ 'min-width': '600px' }"
      >
        <ng-template pTemplate="header">
          <tr>
            <th>Nome</th>
            <th style="width:100px">Tipo</th>
            <th style="width:110px">Escopo</th>
            <th style="width:90px">Código</th>
            <th style="width:90px">Status</th>
            <th style="width:80px">Ações</th>
          </tr>
        </ng-template>

        <ng-template pTemplate="body" let-cat>
          <tr [class.row-inativo]="!cat.ativa">
            <td>
              <span class="nome-cell" [style.padding-left]="indentPadding(cat.nivel)">
                @if (cat.nivel > 1) {
                  <span class="tree-prefix">└ </span>
                }
                {{ cat.nome }}
              </span>
            </td>
            <td>
              <p-tag
                [value]="cat.tipo === 'RECEITA' ? 'Receita' : 'Despesa'"
                [severity]="cat.tipo === 'RECEITA' ? 'success' : 'danger'"
              />
            </td>
            <td>
              <p-tag
                [value]="cat.escopo === 'global' ? 'Global' : 'Específica'"
                severity="secondary"
              />
            </td>
            <td class="codigo-cell">{{ cat.codigo ?? '—' }}</td>
            <td>
              <p-tag
                [value]="cat.ativa ? 'Ativa' : 'Inativa'"
                [severity]="cat.ativa ? 'success' : 'danger'"
              />
            </td>
            <td>
              <div class="acoes-cell">
                <p-button
                  icon="pi pi-pencil"
                  [text]="true"
                  size="small"
                  severity="secondary"
                  (onClick)="abrirEditar(cat)"
                  pTooltip="Editar"
                  tooltipPosition="top"
                />
                @if (cat.ativa) {
                  <p-button
                    icon="pi pi-arrows-h"
                    severity="secondary"
                    [text]="true"
                    size="small"
                    (onClick)="abrirMerge(cat)"
                    pTooltip="Unir com outra categoria"
                    tooltipPosition="top"
                  />
                }
                <p-button
                  [icon]="cat.ativa ? 'pi pi-ban' : 'pi pi-check-circle'"
                  [severity]="cat.ativa ? 'danger' : 'success'"
                  [text]="true"
                  size="small"
                  (onClick)="toggleAtivo(cat)"
                  [pTooltip]="cat.ativa ? 'Inativar' : 'Reativar'"
                  tooltipPosition="top"
                />
              </div>
            </td>
          </tr>
        </ng-template>

        <ng-template pTemplate="emptymessage">
          <tr>
            <td colspan="6" class="empty-msg">
              @if (listaVazia()) {
                Nenhuma categoria cadastrada. Use "Inicializar Plano Padrão" para começar rapidamente.
              } @else {
                Nenhuma categoria encontrada com os filtros aplicados.
              }
            </td>
          </tr>
        </ng-template>
      </p-table>
    </div>

    <p-dialog
      [header]="isEditing() ? 'Editar Categoria' : 'Nova Categoria'"
      [visible]="dialogVisivel()"
      (visibleChange)="$event ? dialogVisivel.set(true) : fecharDialog()"
      [modal]="true"
      [style]="{ width: '480px', 'max-width': '95vw' }"
      [draggable]="true"
      [resizable]="false"
    >
      <form [formGroup]="form" class="dialog-form">
        @if (!isEditing()) {
          <div class="field">
            <label>Tipo *</label>
            <p-select
              formControlName="tipo"
              [options]="tipoOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Selecione o tipo"
              [style]="{ width: '100%' }"
            />
          </div>
        }

        <div class="field">
          <label>Nome *</label>
          <input
            pInputText
            formControlName="nome"
            placeholder="Nome da categoria"
            [style]="{ width: '100%' }"
          />
        </div>

        <div class="field">
          <label>Categoria Pai</label>
          <p-select
            formControlName="parent_id"
            [options]="parentOptions()"
            optionLabel="nome"
            optionValue="id"
            placeholder="Sem categoria pai (nível raiz)"
            [showClear]="true"
            [style]="{ width: '100%' }"
          />
        </div>

        @if (!isEditing()) {
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
        }

        <div class="field">
          <label>Código</label>
          <input
            pInputText
            formControlName="codigo"
            placeholder="Ex: 1.1.1 (opcional)"
            [style]="{ width: '100%' }"
          />
        </div>

        <div class="field">
          <label>Descrição</label>
          <textarea
            pTextarea
            formControlName="descricao"
            placeholder="Descrição opcional"
            rows="2"
            [style]="{ width: '100%', resize: 'vertical' }"
          ></textarea>
        </div>

        <div class="field field-full">
          <label style="margin-bottom:0.5rem">Vínculo com Patrimônio</label>
          <div class="patrimonio-checks">
            <div class="check-item">
              <p-checkbox formControlName="exigir_veiculo" [binary]="true" inputId="chk_veiculo" />
              <label for="chk_veiculo">Exigir Veículo</label>
            </div>
            <div class="check-item">
              <p-checkbox formControlName="exigir_imovel" [binary]="true" inputId="chk_imovel" />
              <label for="chk_imovel">Exigir Imóvel</label>
            </div>
          </div>
          <small style="color:var(--p-surface-400)">Quando marcado, o lançamento nessa categoria obrigatoriamente deverá vincular o respectivo patrimônio.</small>
        </div>
      </form>

      <ng-template pTemplate="footer">
        @if (formErro()) {
          <p-message severity="error">{{ formErro() }}</p-message>
        }
        <div class="footer-acoes">
          <p-button label="Cancelar" severity="secondary" (onClick)="fecharDialog()" />
          <p-button
            [label]="isEditing() ? 'Salvar' : 'Criar'"
            icon="pi pi-check"
            (onClick)="salvar()"
            [loading]="salvando()"
          />
        </div>
      </ng-template>
    </p-dialog>

    <!-- Dialog Merge -->
    <p-dialog
      header="Unir Categorias"
      [(visible)]="mergeDialog"
      [modal]="true"
      [style]="{ width: '560px', 'max-width': '95vw' }"
      [contentStyle]="{ 'min-height': '200px', padding: '1.25rem 1.5rem' }"
    >
      <div class="merge-body">
        <p class="merge-info">
          <i class="pi pi-exclamation-triangle" style="color:var(--p-orange-500);flex-shrink:0;margin-top:2px"></i>
          <span>Todos os lançamentos de <strong>{{ mergeOrigem()?.nome }}</strong> serão movidos para a categoria de destino e ela será inativada.</span>
        </p>
        <div class="field">
          <label>Categoria de destino *</label>
          <p-select
            [ngModel]="mergeDestinoId()"
            (ngModelChange)="mergeDestinoId.set($event)"
            [options]="mergeOpcoes()"
            optionLabel="label"
            optionValue="value"
            placeholder="Selecione a categoria de destino"
            [style]="{ width: '100%' }"
            [filter]="true"
            filterPlaceholder="Buscar categoria..."
            appendTo="body"
          />
        </div>
      </div>
      <ng-template pTemplate="footer">
        <p-button label="Cancelar" severity="secondary" [text]="true" (onClick)="mergeDialog.set(false)" />
        <p-button label="Unir" icon="pi pi-arrows-h" severity="danger"
          [disabled]="!mergeDestinoId()" [loading]="mergeLoading()"
          (onClick)="confirmarMerge()" />
      </ng-template>
    </p-dialog>

  `,
  styles: [`
    .page { max-width: 1000px; }
    .patrimonio-checks { display: flex; gap: 2rem; align-items: center; margin-bottom: 0.25rem; }
    .check-item { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }
    .check-item label { font-size: 0.875rem; font-weight: 500; cursor: pointer; margin: 0; }
    .field-full { grid-column: 1 / -1; }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1rem;
    }
    .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; }
    .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.875rem; }

    .header-acoes { display: flex; gap: 0.5rem; align-items: center; }

    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      gap: 1rem;
      flex-wrap: wrap;
    }
    .filtro-tipo { display: flex; gap: 0.5rem; }
    .toggle-inativas {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
      color: var(--p-surface-600);
    }

    .nome-cell { display: inline-flex; align-items: center; }
    .tree-prefix { color: var(--p-surface-400); font-family: monospace; margin-right: 0.15rem; }
    .codigo-cell { font-size: 0.8rem; color: var(--p-surface-500); font-family: monospace; }

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
      gap: 1rem;
      padding: 0.25rem 0;
    }
    .field { display: flex; flex-direction: column; gap: 0.3rem; }
    .field label { font-size: 0.8rem; font-weight: 600; }

    .footer-acoes {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }
    .merge-info {
      display: flex; align-items: flex-start; gap: 0.5rem;
      background: var(--p-orange-50); border-left: 4px solid var(--p-orange-400);
      padding: 0.75rem 1rem; border-radius: 0 6px 6px 0; margin-bottom: 1.25rem;
      font-size: 0.9rem; line-height: 1.5;
    }
    .merge-body { display: flex; flex-direction: column; gap: 1rem; padding: 0.25rem 0; }
  `],
})
export class CategoriasComponent implements OnInit {
  private readonly categoriaService = inject(CategoriaService);
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly messageService = inject(MessageService);
  private readonly fb = inject(FormBuilder);

  protected readonly lista = signal<Categoria[]>([]);
  protected readonly carregando = signal(false);
  protected readonly filtroTipo = signal<FiltroTipo>('TODOS');
  protected readonly mostrarInativas = signal(false);
  protected readonly dialogVisivel = signal(false);
  protected readonly isEditing = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected readonly salvando = signal(false);
  protected readonly formErro = signal<string | null>(null);
  protected readonly inicializando = signal(false);
  protected readonly tipoParentFilter = signal<'RECEITA' | 'DESPESA'>('RECEITA');

  protected readonly listaFiltrada = computed(() => {
    const tipo = this.filtroTipo();
    const lista = this.lista();
    return lista.filter(c =>
      (tipo === 'TODOS' || c.tipo === tipo) &&
      (this.mostrarInativas() || c.ativa)
    );
  });

  protected readonly listaVazia = computed(() =>
    this.lista().filter(c => c.ativa).length === 0
  );

  protected readonly parentOptions = computed(() =>
    this.lista().filter(c =>
      c.ativa &&
      c.tipo === this.tipoParentFilter() &&
      c.nivel < 3 &&
      c.id !== this.editandoId()
    )
  );

  protected readonly tipoOptions = [
    { label: 'Receita', value: 'RECEITA' },
    { label: 'Despesa', value: 'DESPESA' },
  ];

  protected readonly escopoOptions = [
    { label: 'Global (todas as empresas)', value: 'global' },
    { label: 'Específica (empresa ativa)', value: 'especifico' },
  ];

  protected readonly form = this.fb.group({
    tipo: ['RECEITA', Validators.required],
    nome: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(200)]],
    parent_id: [null as string | null],
    escopo: ['global', Validators.required],
    codigo: [null as string | null],
    descricao: [null as string | null],
    exigir_veiculo: [false],
    exigir_imovel: [false],
  });

  ngOnInit(): void {
    this.form.get('tipo')!.valueChanges.subscribe(v => {
      if (v === 'RECEITA' || v === 'DESPESA') {
        this.tipoParentFilter.set(v);
        this.form.get('parent_id')?.setValue(null);
      }
    });
    this.carregar();
  }

  private carregar(): void {
    const empresaId = this.empresaStore.empresaAtiva()?.id;
    this.carregando.set(true);
    this.categoriaService.listar(empresaId, false).subscribe({
      next: (data) => { this.lista.set(data); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  protected abrirNovo(): void {
    this.isEditing.set(false);
    this.editandoId.set(null);
    this.formErro.set(null);
    this.form.reset({ tipo: 'RECEITA', escopo: 'global', nome: '', parent_id: null, codigo: null, descricao: null, exigir_veiculo: false, exigir_imovel: false });
    this.form.get('tipo')?.enable();
    this.form.get('escopo')?.enable();
    this.tipoParentFilter.set('RECEITA');
    this.dialogVisivel.set(true);
  }

  protected abrirEditar(cat: Categoria): void {
    this.isEditing.set(true);
    this.editandoId.set(cat.id);
    this.formErro.set(null);
    this.tipoParentFilter.set(cat.tipo as 'RECEITA' | 'DESPESA');
    this.form.patchValue({
      tipo: cat.tipo,
      nome: cat.nome,
      parent_id: cat.parent_id,
      escopo: cat.escopo,
      codigo: cat.codigo,
      descricao: cat.descricao,
      exigir_veiculo: cat.exigir_veiculo ?? false,
      exigir_imovel: cat.exigir_imovel ?? false,
    });
    this.form.get('tipo')?.disable();
    this.form.get('escopo')?.disable();
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
    if (this.isEditing()) {
      this.salvarEdicao();
    } else {
      this.salvarNovo();
    }
  }

  private salvarNovo(): void {
    const v = this.form.getRawValue();
    const escopo = v.escopo as 'global' | 'especifico';
    const empresaId = escopo === 'especifico' ? (this.empresaStore.empresaAtiva()?.id ?? null) : null;
    const payload: CategoriaCreate = {
      nome: v.nome!,
      tipo: v.tipo as 'RECEITA' | 'DESPESA',
      escopo,
      parent_id: v.parent_id || null,
      empresa_id: empresaId,
      codigo: v.codigo || null,
      descricao: v.descricao || null,
      exigir_veiculo: v.exigir_veiculo ?? false,
      exigir_imovel: v.exigir_imovel ?? false,
    };
    this.salvando.set(true);
    this.categoriaService.criar(payload).subscribe({
      next: () => {
        this.dialogVisivel.set(false);
        this.salvando.set(false);
        this.carregar();
        this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: 'Categoria criada.' });
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Erro ao criar categoria.';
        this.formErro.set(detail);
        this.salvando.set(false);
      },
    });
  }

  private salvarEdicao(): void {
    const v = this.form.getRawValue();
    const payload: CategoriaUpdate = {
      nome: v.nome ?? undefined,
      parent_id: v.parent_id ?? null,
      codigo: v.codigo || null,
      descricao: v.descricao || null,
      exigir_veiculo: v.exigir_veiculo ?? false,
      exigir_imovel: v.exigir_imovel ?? false,
    };
    this.salvando.set(true);
    this.categoriaService.atualizar(this.editandoId()!, payload).subscribe({
      next: () => {
        this.dialogVisivel.set(false);
        this.salvando.set(false);
        this.carregar();
        this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: 'Categoria atualizada.' });
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Erro ao atualizar categoria.';
        this.formErro.set(detail);
        this.salvando.set(false);
      },
    });
  }

  protected toggleAtivo(cat: Categoria): void {
    const obs = cat.ativa
      ? this.categoriaService.inativar(cat.id)
      : this.categoriaService.reativar(cat.id);
    obs.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Sucesso',
          detail: `Categoria ${cat.ativa ? 'inativada' : 'reativada'}.`,
        });
        this.carregar();
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Erro ao alterar status.';
        this.messageService.add({ severity: 'error', summary: 'Erro', detail });
      },
    });
  }

  protected inicializarPlano(): void {
    this.inicializando.set(true);
    this.categoriaService.inicializarPlanoPadrao().subscribe({
      next: (res) => {
        this.inicializando.set(false);
        this.carregar();
        this.messageService.add({
          severity: 'success',
          summary: 'Plano padrão inicializado',
          detail: `${res.criadas} categorias criadas com sucesso.`,
        });
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Erro ao inicializar plano padrão.';
        this.messageService.add({ severity: 'error', summary: 'Erro', detail });
        this.inicializando.set(false);
      },
    });
  }

  protected indentPadding(nivel: number): string {
    return `${(nivel - 1) * 1.5}rem`;
  }

  // ── Merge ─────────────────────────────────────────────────────────────────
  protected mergeDialog = signal(false);
  protected mergeOrigem = signal<Categoria | null>(null);
  protected mergeDestinoId = signal<string | null>(null);
  protected mergeLoading = signal(false);

  protected mergeOpcoes = computed(() => {
    const origem = this.mergeOrigem();
    if (!origem) return [];
    return this.lista()
      .filter(c => c.ativa && c.id !== origem.id && c.tipo === origem.tipo)
      .map(c => ({ label: c.nome, value: c.id }));
  });

  protected abrirMerge(cat: Categoria): void {
    this.mergeOrigem.set(cat);
    this.mergeDestinoId.set(null);
    this.mergeDialog.set(true);
  }

  protected confirmarMerge(): void {
    const origem = this.mergeOrigem();
    const destinoId = this.mergeDestinoId();
    if (!origem || !destinoId) return;
    this.mergeLoading.set(true);
    this.categoriaService.merge(origem.id, destinoId).subscribe({
      next: () => {
        this.mergeLoading.set(false);
        this.mergeDialog.set(false);
        this.messageService.add({ severity: 'success', summary: 'Categorias unidas com sucesso.' });
        this.carregar();
      },
      error: (err) => {
        this.mergeLoading.set(false);
        const detail = err?.error?.detail ?? 'Erro ao unir categorias.';
        this.messageService.add({ severity: 'error', summary: detail });
      },
    });
  }
}
