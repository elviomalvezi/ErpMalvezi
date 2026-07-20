import { Component, computed, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { MessageModule } from 'primeng/message';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { MessageService } from 'primeng/api';

import { LancamentoService } from '../../core/services/lancamento.service';
import type {
  ImportacaoAnaliseResponse,
  ImportacaoLinhaPreview,
  ImportacaoPreviewResponse,
} from '../../core/models';

type CampoImportacao =
  | 'descricao'
  | 'valor'
  | 'data_competencia'
  | 'data_vencimento'
  | 'observacoes'
  | 'col_tipo'
  | 'col_empresa'
  | 'categoria_nome'
  | 'contato_nome'
  | 'conta_bancaria_id';

interface CampoOpcao {
  campo: CampoImportacao;
  label: string;
  obrigatorio: boolean;
  ajuda: string;
}

const CAMPOS: CampoOpcao[] = [
  { campo: 'descricao', label: 'Descrição', obrigatorio: true, ajuda: 'Texto principal do lançamento.' },
  { campo: 'valor', label: 'Valor', obrigatorio: true, ajuda: 'Aceita 1200,50 ou 1200.50. Negativos são convertidos.' },
  { campo: 'data_competencia', label: 'Data Competência', obrigatorio: true, ajuda: 'Aceita dd/mm/aaaa ou aaaa-mm-dd.' },
  { campo: 'data_vencimento', label: 'Data Vencimento', obrigatorio: true, ajuda: 'Aceita dd/mm/aaaa ou aaaa-mm-dd.' },
  { campo: 'col_tipo', label: 'Tipo (Receita/Despesa)', obrigatorio: false, ajuda: 'CAP/Despesas/D = Despesa  |  CAR/Receitas/R = Receita. Define o tipo por linha.' },
  { campo: 'col_empresa', label: 'Empresa (Titular)', obrigatorio: false, ajuda: 'Nome da empresa cadastrada. Identifica a empresa por linha.' },
  { campo: 'categoria_nome', label: 'Categoria (nome)', obrigatorio: false, ajuda: 'Nome da categoria. Criada automaticamente se não existir.' },
  { campo: 'contato_nome', label: 'Fornecedor/Cliente (nome)', obrigatorio: false, ajuda: 'Nome do fornecedor ou cliente. Criado automaticamente se não existir.' },
  { campo: 'observacoes', label: 'Observações', obrigatorio: false, ajuda: 'Campo livre opcional.' },
  { campo: 'conta_bancaria_id', label: 'Conta Bancária ID', obrigatorio: false, ajuda: 'UUID da conta bancária.' },
];

@Component({
  selector: 'app-lancamento-importacao',
  standalone: true,
  imports: [FormsModule, ButtonModule, DialogModule, MessageModule, SelectModule, TableModule, TagModule],
  template: `
    <p-button label="Importar Planilha" icon="pi pi-upload" severity="secondary" (onClick)="abrir()" />

    <p-dialog
      header="Importar Lançamentos"
      [visible]="visivel()"
      (visibleChange)="visivel.set($event)"
      [modal]="true"
      [style]="{ width: '980px', 'max-width': '96vw' }"
      [draggable]="true"
      [resizable]="false"
    >
      <div class="wrapper">
        <div class="upload-box">
          <input #fileInput type="file" accept=".csv,.xlsx" hidden (change)="onFileSelecionado($event)" />
          <p-button label="Selecionar Arquivo" icon="pi pi-file-import" (onClick)="fileInput.click()" />
          <span class="arquivo-nome">{{ arquivo()?.name ?? 'Nenhum arquivo selecionado' }}</span>
        </div>

        @if (erro()) {
          <p-message severity="error">{{ erro() }}</p-message>
        }

        @if (analisando()) {
          <div class="estado">Lendo cabeçalho da planilha...</div>
        }

        @if (analise()) {
          <section class="bloco">
            <div class="bloco-header">
              <div>
                <h3 class="bloco-titulo">Mapeamento</h3>
                <p class="bloco-subtitulo">{{ analise()!.total_linhas }} linhas encontradas</p>
              </div>
              <p-button
                label="Pré-visualizar"
                icon="pi pi-search"
                (onClick)="preVisualizar()"
                [loading]="carregandoPreview()"
              />
            </div>

            <p-table [value]="campos" size="small" [tableStyle]="{ 'min-width': '720px' }">
              <ng-template pTemplate="header">
                <tr>
                  <th>Campo do sistema</th>
                  <th>Coluna da planilha</th>
                  <th>Regra</th>
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-item>
                <tr>
                  <td>
                    <div class="campo-label">
                      <span>{{ item.label }}</span>
                      @if (item.obrigatorio) {
                        <p-tag value="Obrigatório" severity="danger" />
                      }
                    </div>
                  </td>
                  <td>
                    <p-select
                      [options]="colunaOpcoes()"
                      optionLabel="label"
                      optionValue="value"
                      [ngModel]="mapeamento()[item.campo] ?? null"
                      (ngModelChange)="atualizarMapeamento(item.campo, $event)"
                      [showClear]="true"
                      placeholder="Selecione a coluna"
                      class="coluna-select"
                    />
                  </td>
                  <td class="regra">{{ item.ajuda }}</td>
                </tr>
              </ng-template>
            </p-table>
          </section>

          <section class="bloco">
            <h3 class="bloco-titulo">Amostra da planilha</h3>
            <p-table [value]="analise()!.amostras" size="small" [scrollable]="true" scrollHeight="220px">
              <ng-template pTemplate="header">
                <tr>
                  @for (coluna of analise()!.colunas; track coluna) {
                    <th>{{ coluna }}</th>
                  }
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-linha>
                <tr>
                  @for (coluna of analise()!.colunas; track coluna) {
                    <td>{{ linha[coluna] || '—' }}</td>
                  }
                </tr>
              </ng-template>
            </p-table>
          </section>
        }

        @if (preview()) {
          <section class="bloco">
            <div class="bloco-header resumo">
              <div class="kpi ok">
                <span class="kpi-label">Válidas</span>
                <strong>{{ preview()!.linhas_validas }}</strong>
              </div>
              <div class="kpi erro">
                <span class="kpi-label">Inválidas</span>
                <strong>{{ preview()!.linhas_invalidas }}</strong>
              </div>
            </div>

            <p-table [value]="previewItens()" size="small" [scrollable]="true" scrollHeight="280px">
              <ng-template pTemplate="header">
                <tr>
                  <th>Linha</th>
                  <th>Status</th>
                  <th>Descrição</th>
                  <th>Valor</th>
                  <th>Competência</th>
                  <th>Vencimento</th>
                  <th>Erros</th>
                </tr>
              </ng-template>
              <ng-template pTemplate="body" let-item>
                <tr>
                  <td>{{ item.numero_linha }}</td>
                  <td>
                    <p-tag
                      [value]="item.valida ? 'OK' : 'Erro'"
                      [severity]="item.valida ? 'success' : 'danger'"
                    />
                  </td>
                  <td>{{ item.payload['descricao'] || '—' }}</td>
                  <td>{{ item.payload['valor'] || '—' }}</td>
                  <td>{{ item.payload['data_competencia'] || '—' }}</td>
                  <td>{{ item.payload['data_vencimento'] || '—' }}</td>
                  <td>{{ item.erros.join(' | ') || '—' }}</td>
                </tr>
              </ng-template>
            </p-table>
          </section>
        }

        <div class="footer">
          <p-button label="Fechar" severity="secondary" (onClick)="fechar()" />
          <p-button
            label="Confirmar Importação"
            icon="pi pi-check"
            (onClick)="confirmar()"
            [disabled]="!preview() || preview()!.linhas_validas === 0"
            [loading]="importando()"
          />
        </div>
      </div>
    </p-dialog>
  `,
  styles: [`
    .wrapper { display: flex; flex-direction: column; gap: 1rem; }
    .upload-box { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .arquivo-nome { color: var(--p-surface-500); font-size: 0.9rem; }
    .estado { color: var(--p-surface-500); font-size: 0.92rem; }
    .bloco { display: flex; flex-direction: column; gap: 0.75rem; }
    .bloco-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
    .bloco-titulo { margin: 0; font-size: 1rem; font-weight: 700; }
    .bloco-subtitulo { margin: 0.15rem 0 0; color: var(--p-surface-500); font-size: 0.85rem; }
    .campo-label { display: flex; align-items: center; gap: 0.5rem; }
    .regra { color: var(--p-surface-500); font-size: 0.83rem; }
    .coluna-select { width: 100%; min-width: 220px; }
    .resumo { justify-content: flex-start; }
    .kpi {
      min-width: 140px; padding: 0.75rem 0.9rem; border-radius: 10px; border: 1px solid var(--p-surface-200);
      display: flex; flex-direction: column; gap: 0.2rem;
    }
    .kpi.ok { background: #f0fdf4; border-color: #bbf7d0; }
    .kpi.erro { background: #fef2f2; border-color: #fecaca; }
    .kpi-label { font-size: 0.78rem; color: var(--p-surface-500); text-transform: uppercase; letter-spacing: 0.04em; }
    .footer { display: flex; justify-content: flex-end; gap: 0.75rem; padding-top: 0.5rem; }
    :host ::ng-deep .coluna-select .p-select { width: 100%; }
  `],
})
export class LancamentoImportacaoComponent {
  private readonly svc = inject(LancamentoService);
  private readonly messageSvc = inject(MessageService);

  readonly empresaId = input.required<string>();
  readonly tipo = input.required<'RECEITA' | 'DESPESA'>();
  readonly importado = output<void>();

  protected readonly visivel = signal(false);
  protected readonly analisando = signal(false);
  protected readonly carregandoPreview = signal(false);
  protected readonly importando = signal(false);
  protected readonly erro = signal<string | null>(null);
  protected readonly arquivo = signal<File | null>(null);
  protected readonly analise = signal<ImportacaoAnaliseResponse | null>(null);
  protected readonly preview = signal<ImportacaoPreviewResponse | null>(null);
  protected readonly mapeamento = signal<Record<string, string | null>>({});
  protected readonly campos = CAMPOS;

  protected readonly colunaOpcoes = computed(() =>
    (this.analise()?.colunas ?? []).map((coluna) => ({ label: coluna, value: coluna })),
  );

  protected readonly previewItens = computed(() => this.preview()?.itens ?? []);

  protected abrir(): void {
    this.visivel.set(true);
  }

  protected fechar(): void {
    this.visivel.set(false);
    this.erro.set(null);
    this.preview.set(null);
  }

  protected onFileSelecionado(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    input.value = '';
    if (!file) return;

    this.arquivo.set(file);
    this.preview.set(null);
    this.erro.set(null);
    this.analisando.set(true);

    this.svc.analisarImportacao(file).subscribe({
      next: (analise) => {
        this.analise.set(analise);
        this.mapeamento.set(this.sugerirMapeamento(analise.colunas));
        this.analisando.set(false);
      },
      error: (err) => {
        this.erro.set(err?.error?.detail ?? 'Não foi possível ler a planilha.');
        this.analisando.set(false);
      },
    });
  }

  protected atualizarMapeamento(campo: CampoImportacao, coluna: string | null): void {
    this.preview.set(null);
    this.mapeamento.update((atual) => ({ ...atual, [campo]: coluna }));
  }

  protected preVisualizar(): void {
    const file = this.arquivo();
    if (!file) {
      this.erro.set('Selecione uma planilha antes de continuar.');
      return;
    }
    this.erro.set(null);
    this.carregandoPreview.set(true);
    this.svc.preVisualizarImportacao({
      file,
      empresaId: this.empresaId(),
      tipo: this.tipo(),
      mapeamento: this.mapeamento(),
    }).subscribe({
      next: (preview) => {
        this.preview.set(preview);
        this.carregandoPreview.set(false);
      },
      error: (err) => {
        this.erro.set(err?.error?.detail ?? 'Não foi possível montar a pré-visualização.');
        this.carregandoPreview.set(false);
      },
    });
  }

  protected confirmar(): void {
    const file = this.arquivo();
    const preview = this.preview();
    if (!file || !preview || preview.linhas_validas === 0) {
      return;
    }
    this.importando.set(true);
    this.erro.set(null);
    this.svc.confirmarImportacao({
      file,
      empresaId: this.empresaId(),
      tipo: this.tipo(),
      mapeamento: this.mapeamento(),
    }).subscribe({
      next: (resultado) => {
        this.importando.set(false);
        this.messageSvc.add({
          severity: 'success',
          summary: 'Importação concluída',
          detail: `${resultado.importadas} lançamentos importados e ${resultado.ignoradas} linhas ignoradas.`,
        });
        this.importado.emit();
        this.resetar();
      },
      error: (err) => {
        this.importando.set(false);
        this.erro.set(err?.error?.detail ?? 'Falha ao confirmar a importação.');
      },
    });
  }

  private sugerirMapeamento(colunas: string[]): Record<string, string | null> {
    const colunasNormalizadas = colunas.map((coluna) => ({
      original: coluna,
      chave: coluna.trim().toLowerCase().replace(/\s+/g, '_'),
    }));
    const aliases: Record<CampoImportacao, string[]> = {
      descricao: ['descricao', 'descrição', 'historico', 'histórico', 'titulo', 'histórico/descrição'],
      valor: ['valor', 'valor_total', 'vlr', 'amount'],
      data_competencia: ['data_competencia', 'competencia', 'data_comp', 'data_lancamento', 'emissao', 'emissão'],
      data_vencimento: ['data_vencimento', 'vencimento', 'data_vencto', 'vencto'],
      col_tipo: ['cap/car', 'tipo', 'cap_car', 'natureza', 'receitas/despes', 'receitas/despesas', 'tipolancamento'],
      col_empresa: ['titular', 'empresa', 'cnpj_empresa', 'empresa_titular'],
      categoria_nome: ['categoria', 'categoria_nome', 'categoria nome', 'plano_contas'],
      contato_nome: ['fornecedor', 'cliente', 'contato', 'fornecedor_cliente', 'nome_fornecedor', 'favorecido'],
      observacoes: ['observacoes', 'observação', 'obs', 'observacao', 'complemento'],
      conta_bancaria_id: ['conta_bancaria_id', 'id_conta_bancaria', 'conta_id'],
    };

    const mapeamento: Record<string, string | null> = {};
    for (const campo of CAMPOS) {
      const match = colunasNormalizadas.find((coluna) => aliases[campo.campo].includes(coluna.chave));
      mapeamento[campo.campo] = match?.original ?? null;
    }
    return mapeamento;
  }

  private resetar(): void {
    this.visivel.set(false);
    this.analisando.set(false);
    this.carregandoPreview.set(false);
    this.importando.set(false);
    this.erro.set(null);
    this.arquivo.set(null);
    this.analise.set(null);
    this.preview.set(null);
    this.mapeamento.set({});
  }
}
