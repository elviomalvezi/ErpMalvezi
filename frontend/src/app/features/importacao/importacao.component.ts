import { Component, inject, signal, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CurrencyPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { CardModule } from 'primeng/card';
import { DividerModule } from 'primeng/divider';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { LancamentoService } from '../../core/services/lancamento.service';
import {
  ImportacaoAnaliseResponse,
  ImportacaoPreviewResponse,
  ImportacaoResultadoResponse,
  ImportacaoLinhaPreview,
} from '../../core/models';

interface CampoSistema {
  chave: string;
  label: string;
  obrigatorio: boolean;
  descricao: string;
}

const CAMPOS_SISTEMA: CampoSistema[] = [
  { chave: 'descricao',        label: 'Descrição *',           obrigatorio: true,  descricao: 'Título do lançamento' },
  { chave: 'valor',            label: 'Valor *',               obrigatorio: true,  descricao: 'Valor numérico (ex: 1500.00)' },
  { chave: 'data_vencimento',  label: 'Data de Vencimento *',  obrigatorio: true,  descricao: 'Data no formato DD/MM/AAAA' },
  { chave: 'data_competencia', label: 'Data de Competência',   obrigatorio: false, descricao: 'Se não mapeada, usa a mesma data de vencimento' },
  { chave: 'col_tipo',         label: 'Tipo (Receita/Despesa)', obrigatorio: false, descricao: 'CAP / Despesas / D = Despesa  |  CAR / Receitas / R = Receita' },
  { chave: 'col_empresa',      label: 'Empresa (Titular)',     obrigatorio: false, descricao: 'Nome da empresa para identificar' },
  { chave: 'categoria_nome',   label: 'Categoria',             obrigatorio: false, descricao: 'Nome da categoria (criada se não existir)' },
  { chave: 'contato_nome',     label: 'Cliente / Fornecedor',  obrigatorio: false, descricao: 'Nome do contato (criado se não existir)' },
  { chave: 'observacoes',      label: 'Observações',           obrigatorio: false, descricao: 'Texto livre' },
  { chave: 'conta_banco',      label: 'Banco',                 obrigatorio: false, descricao: 'Nome do banco (ex: SICOOB). Conta criada automaticamente se não existir.' },
  { chave: 'conta_agencia',    label: 'Agência',               obrigatorio: false, descricao: 'Número da agência (ex: 51420)' },
  { chave: 'conta_numero',     label: 'Número da Conta',       obrigatorio: false, descricao: 'Número da conta corrente (ex: 75744)' },
];

@Component({
  selector: 'app-importacao',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule, CurrencyPipe, RouterLink,
    ButtonModule, SelectModule, TableModule, TagModule,
    ToastModule, CardModule, DividerModule,
  ],
  template: `
    <p-toast />

    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title"><i class="pi pi-upload"></i> Importação de Dados</h1>
          <p class="page-subtitle">Importe lançamentos de planilhas Excel com criação automática de categorias e contatos</p>
        </div>
      </div>

      <!-- Passos -->
      <div class="passos">
        @for (p of [1,2,3,4]; track p) {
          <div class="passo" [class.ativo]="etapa() === p" [class.feito]="etapa() > p">
            <div class="passo-num">{{ etapa() > p ? '✓' : p }}</div>
            <span>{{ ['Upload', 'Mapeamento', 'Pré-visualização', 'Resultado'][p-1] }}</span>
          </div>
          @if (p < 4) { <div class="passo-linha" [class.feito]="etapa() > p"></div> }
        }
      </div>

      <!-- ── ETAPA 1: Upload ─────────────────────────────────────────── -->
      @if (etapa() === 1) {
        <div class="etapa-container">
          <div class="upload-area">

            <div class="campo-grupo">
              <label>Arquivo Excel *</label>
              <div class="dropzone" (click)="fileInput.click()"
                (dragover)="$event.preventDefault()" (drop)="onDrop($event)"
                [class.tem-arquivo]="arquivo()">
                @if (!arquivo()) {
                  <i class="pi pi-cloud-upload dropzone-icon"></i>
                  <p>Clique ou arraste um arquivo <strong>.xlsx</strong> aqui</p>
                  <small>Máximo 100.000 linhas</small>
                } @else {
                  <i class="pi pi-file-excel dropzone-icon cor-verde"></i>
                  <p><strong>{{ arquivo()!.name }}</strong></p>
                  <small>{{ (arquivo()!.size / 1024).toFixed(1) }} KB — clique para trocar</small>
                }
              </div>
              <input #fileInput type="file" accept=".xlsx,.xls,.csv"
                style="display:none" (change)="onFileSelect($event)" />
            </div>
          </div>

          <div class="etapa-footer">
            <p-button label="Analisar Planilha" icon="pi pi-search"
              [disabled]="!arquivo()"
              [loading]="analisando()" (onClick)="analisar()" />
          </div>
        </div>
      }

      <!-- ── ETAPA 2: Mapeamento ─────────────────────────────────────── -->
      @if (etapa() === 2 && analise()) {
        <div class="etapa-container">

          <div class="preview-box">
            <h3 class="preview-title">
              <i class="pi pi-table"></i>
              Amostra da planilha — {{ analise()!.total_linhas }} linhas detectadas
            </h3>
            <div class="table-scroll">
              <table class="preview-table">
                <thead>
                  <tr>@for (col of analise()!.colunas; track col) { <th>{{ col }}</th> }</tr>
                </thead>
                <tbody>
                  @for (row of analise()!.amostras; track $index) {
                    <tr>@for (col of analise()!.colunas; track col) { <td>{{ row[col] ?? '' }}</td> }</tr>
                  }
                </tbody>
              </table>
            </div>
          </div>

          <p-divider />

          <h3 class="mapa-title">Relacionamento: Coluna da Planilha → Campo do Sistema</h3>
          <p class="mapa-info">
            <i class="pi pi-info-circle"></i>
            Campos com <strong>*</strong> são obrigatórios.
            Categorias e contatos inexistentes serão <strong>criados automaticamente</strong>.
          </p>

          <div class="mapa-grid">
            @for (campo of camposSistema; track campo.chave) {
              <div class="mapa-linha" [class.obrigatorio]="campo.obrigatorio">
                <div class="campo-info">
                  <span class="campo-label">{{ campo.label }}</span>
                  <small class="campo-desc">{{ campo.descricao }}</small>
                </div>
                <div class="campo-arrow"><i class="pi pi-arrow-left"></i></div>
                <div class="campo-select">
                  <p-select
                    [(ngModel)]="mapeamento[campo.chave]"
                    [options]="colunaOpts()"
                    optionLabel="label" optionValue="value"
                    [placeholder]="campo.obrigatorio ? 'Selecionar coluna *' : 'Não importar'"
                    [showClear]="!campo.obrigatorio"
                    [style]="{ width: '100%' }"
                  />
                </div>
              </div>
            }
          </div>

          @if (alertasMapeamento.length > 0) {
            <div class="alerta-mapeamento">
              <i class="pi pi-exclamation-triangle"></i>
              <strong>Campos opcionais não mapeados:</strong>
              <ul style="margin:0.25rem 0 0 1rem;padding:0">
                @for (a of alertasMapeamento; track a) { <li>{{ a }}</li> }
              </ul>
              <small>Você pode continuar, mas esses dados não serão importados.</small>
            </div>
          }

          <div class="etapa-footer">
            <p-button label="Voltar" severity="secondary" [text]="true" (onClick)="etapa.set(1)" />
            <p-button label="Pré-visualizar" icon="pi pi-eye"
              [disabled]="!mapeamentoValido" [loading]="previewing()"
              (onClick)="preVisualizar()" />
          </div>
        </div>
      }

      <!-- ── ETAPA 3: Pré-visualização ──────────────────────────────── -->
      @if (etapa() === 3 && preview()) {
        <div class="etapa-container">

          <!-- Botões no topo para não precisar rolar -->
          <div class="etapa-footer" style="margin-top:0;padding-top:0;border-top:none;margin-bottom:1.5rem">
            <p-button label="Voltar" severity="secondary" [text]="true" (onClick)="etapa.set(2)" />
            <p-button label="Confirmar Importação" icon="pi pi-check" severity="success"
              [disabled]="preview()!.linhas_validas === 0" [loading]="importando()"
              (onClick)="confirmar()" />
          </div>

          <div class="resumo-grid">
            <div class="resumo-card">
              <i class="pi pi-check-circle cor-verde"></i>
              <div class="resumo-valor">{{ preview()!.linhas_validas }}</div>
              <div class="resumo-label">Linhas válidas</div>
            </div>
            <div class="resumo-card">
              <i class="pi pi-times-circle cor-vermelho"></i>
              <div class="resumo-valor">{{ preview()!.linhas_invalidas }}</div>
              <div class="resumo-label">Linhas com erro</div>
            </div>
            <div class="resumo-card">
              <i class="pi pi-file-import cor-azul"></i>
              <div class="resumo-valor">{{ preview()!.total_linhas }}</div>
              <div class="resumo-label">Total de linhas</div>
            </div>
          </div>

          <!-- Erros -->
          @if (linhasComErro().length > 0) {
            <div class="erros-box">
              <strong><i class="pi pi-exclamation-triangle"></i> Linhas com erro (serão ignoradas):</strong>
              <ul class="erros-lista">
                @for (e of linhasComErro().slice(0, 10); track e.numero_linha) {
                  <li>Linha {{ e.numero_linha }}: {{ e.erros.join(', ') }}</li>
                }
                @if (linhasComErro().length > 10) {
                  <li>... e mais {{ linhasComErro().length - 10 }} linhas com erro</li>
                }
              </ul>
            </div>
          }

          <!-- Preview das linhas válidas -->
          <p-table [value]="linhasValidas().slice(0, 20)" size="small" class="preview-lancamentos">
            <ng-template pTemplate="header">
              <tr>
                <th>Descrição</th><th>Tipo</th><th>Vencimento</th>
                <th>Categoria</th><th>Contato</th><th class="text-right">Valor</th>
              </tr>
            </ng-template>
            <ng-template pTemplate="body" let-item>
              <tr>
                <td>{{ item.payload['descricao'] }}</td>
                <td>
                  <p-tag
                    [value]="item.payload['tipo'] === 'RECEITA' ? 'Receita' : 'Despesa'"
                    [severity]="item.payload['tipo'] === 'RECEITA' ? 'success' : 'danger'" />
                </td>
                <td>{{ item.payload['data_vencimento'] }}</td>
                <td>{{ item.payload['categoria_nome'] ?? '—' }}</td>
                <td>{{ item.payload['contato_nome'] ?? '—' }}</td>
                <td class="text-right">{{ item.payload['valor'] | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td>
              </tr>
            </ng-template>
          </p-table>
          @if (linhasValidas().length > 20) {
            <p class="mais-linhas">... e mais {{ linhasValidas().length - 20 }} linhas válidas</p>
          }

          <div class="etapa-footer">
            <p-button label="Voltar" severity="secondary" [text]="true" (onClick)="etapa.set(2)" />
            <p-button label="Confirmar Importação" icon="pi pi-check" severity="success"
              [disabled]="preview()!.linhas_validas === 0" [loading]="importando()"
              (onClick)="confirmar()" />
          </div>
        </div>
      }

      <!-- ── ETAPA 4: Resultado ─────────────────────────────────────── -->
      @if (etapa() === 4 && resultado()) {
        <div class="etapa-container">
          <div class="resultado-destaque">
            <i class="pi pi-check-circle resultado-icon"></i>
            <div class="resultado-numero">{{ resultado()!.importadas }}</div>
            <div class="resultado-label">lançamentos importados com sucesso</div>
          </div>

          <div class="resumo-grid" style="max-width:400px;margin:0 auto 2rem">
            <div class="resumo-card">
              <i class="pi pi-file-import cor-azul"></i>
              <div class="resumo-valor">{{ resultado()!.total_linhas }}</div>
              <div class="resumo-label">Total processado</div>
            </div>
            <div class="resumo-card">
              <i class="pi pi-times-circle cor-vermelho"></i>
              <div class="resumo-valor">{{ resultado()!.ignoradas }}</div>
              <div class="resumo-label">Ignoradas (erros)</div>
            </div>
          </div>

          @if (resultado()!.empresas_criadas_importacao.length) {
            <div class="aviso-titulares info">
              <i class="pi pi-info-circle"></i>
              <div>
                <strong>Empresas criadas automaticamente:</strong>
                <p>Os titulares abaixo não existiam no cadastro e foram criados como Pessoa Física sem documento.
                  Acesse <strong>Empresas</strong> para preencher o CPF de cada um:</p>
                <ul>
                  @for (t of resultado()!.empresas_criadas_importacao; track t) {
                    <li>{{ t }}</li>
                  }
                </ul>
              </div>
            </div>
          }

          <div class="etapa-footer" style="justify-content:center">
            <p-button label="Nova Importação" icon="pi pi-refresh" severity="secondary" (onClick)="reiniciar()" />
            <p-button label="Ver Contas a Pagar" icon="pi pi-arrow-circle-up" routerLink="/contas-pagar" />
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .page { max-width: 1000px; }
    .page-header { margin-bottom: 1.5rem; }
    .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; }
    .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.875rem; }

    .passos { display: flex; align-items: center; margin-bottom: 2rem; }
    .passo { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--p-surface-400); }
    .passo.ativo { color: var(--p-primary-color); font-weight: 700; }
    .passo.feito { color: var(--p-green-600); }
    .passo-num { width: 28px; height: 28px; border-radius: 50%; border: 2px solid currentColor; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.8rem; flex-shrink: 0; }
    .passo.ativo .passo-num { background: var(--p-primary-color); color: white; border-color: var(--p-primary-color); }
    .passo.feito .passo-num { background: var(--p-green-500); color: white; border-color: var(--p-green-500); }
    .passo-linha { flex: 1; height: 2px; background: var(--p-surface-200); margin: 0 0.5rem; }
    .passo-linha.feito { background: var(--p-green-400); }

    .etapa-container { background: var(--p-surface-0); border: 1px solid var(--p-surface-200); border-radius: 12px; padding: 2rem; }
    .etapa-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--p-surface-200); }

    .upload-area { display: flex; flex-direction: column; gap: 1.5rem; max-width: 560px; }
    .campo-grupo { display: flex; flex-direction: column; gap: 0.4rem; }
    .campo-grupo label { font-weight: 600; font-size: 0.875rem; }

    .empresa-ativa-badge {
      display: flex; align-items: center; gap: 0.5rem;
      padding: 0.6rem 0.9rem; background: var(--p-primary-50);
      border: 1px solid var(--p-primary-200); border-radius: 8px; font-weight: 600;
    }
    .empresa-ativa-badge i { color: var(--p-primary-color); }
    .empresa-ativa-badge span { flex: 1; }
    .trocar-empresa {
      background: none; border: none; color: var(--p-primary-color);
      cursor: pointer; font-size: 0.8rem; text-decoration: underline; padding: 0;
    }
    .dropzone {
      border: 2px dashed var(--p-surface-300); border-radius: 10px;
      padding: 2.5rem 1rem; text-align: center; cursor: pointer;
      transition: border-color 0.2s, background 0.2s;
    }
    .dropzone:hover, .dropzone.tem-arquivo { border-color: var(--p-primary-color); background: var(--p-primary-50); }
    .dropzone-icon { font-size: 2.5rem; color: var(--p-surface-400); display: block; margin-bottom: 0.75rem; }
    .dropzone p { margin: 0 0 0.3rem; font-size: 0.9rem; }
    .dropzone small { color: var(--p-surface-400); }

    .preview-box { background: var(--p-surface-50); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }
    .preview-title { margin: 0 0 0.75rem; font-size: 0.9rem; font-weight: 600; color: var(--p-surface-600); display: flex; align-items: center; gap: 0.4rem; }
    .table-scroll { overflow-x: auto; }
    .preview-table { border-collapse: collapse; font-size: 0.8rem; min-width: 100%; }
    .preview-table th { background: var(--p-surface-200); padding: 0.4rem 0.75rem; text-align: left; white-space: nowrap; font-weight: 600; }
    .preview-table td { padding: 0.3rem 0.75rem; border-bottom: 1px solid var(--p-surface-100); white-space: nowrap; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }

    .mapa-title { margin: 0 0 0.5rem; font-size: 1rem; font-weight: 700; }
    .mapa-info { color: var(--p-surface-500); font-size: 0.875rem; margin-bottom: 1.25rem; display: flex; gap: 0.4rem; }
    .alerta-mapeamento { background: #fff8e1; border: 1px solid #f9a825; border-radius: 8px; padding: 0.875rem 1rem; margin-top: 1.25rem; font-size: 0.875rem; color: #5d4037; }
    .alerta-mapeamento i { color: #f9a825; margin-right: 0.35rem; }
    .mapa-grid { display: flex; flex-direction: column; gap: 0.75rem; }
    .mapa-linha { display: grid; grid-template-columns: 1fr 28px 1fr; gap: 0.75rem; align-items: center; }
    .campo-info { display: flex; flex-direction: column; }
    .campo-label { font-weight: 600; font-size: 0.875rem; }
    .mapa-linha.obrigatorio .campo-label { color: var(--p-surface-900); }
    .campo-desc { color: var(--p-surface-400); font-size: 0.75rem; }
    .campo-arrow { text-align: center; color: var(--p-primary-color); }

    .resumo-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    .resumo-card { background: var(--p-surface-50); border: 1px solid var(--p-surface-200); border-radius: 10px; padding: 1.2rem; text-align: center; }
    .resumo-card i { font-size: 1.6rem; display: block; margin-bottom: 0.5rem; }
    .resumo-valor { font-size: 2rem; font-weight: 700; }
    .resumo-label { font-size: 0.8rem; color: var(--p-surface-500); }

    .erros-box { background: var(--p-red-50); border-left: 4px solid var(--p-red-400); padding: 0.75rem 1rem; border-radius: 0 6px 6px 0; margin-bottom: 1rem; }
    .erros-box strong { font-size: 0.875rem; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.4rem; color: var(--p-red-700); }
    .erros-lista { margin: 0; padding-left: 1.2rem; font-size: 0.8rem; color: var(--p-red-700); }

    :host ::ng-deep .preview-lancamentos { margin-top: 1rem; }
    .text-right { text-align: right !important; }
    .mais-linhas { color: var(--p-surface-400); font-size: 0.8rem; text-align: center; margin-top: 0.5rem; }

    .resultado-destaque { text-align: center; padding: 2rem 0; }
    .resultado-icon { font-size: 3.5rem; color: var(--p-green-500); display: block; margin-bottom: 0.75rem; }
    .resultado-numero { font-size: 3rem; font-weight: 700; color: var(--p-green-600); }
    .resultado-label { font-size: 1rem; color: var(--p-surface-500); margin-bottom: 2rem; }

    .cor-verde { color: var(--p-green-500); }
    .cor-vermelho { color: var(--p-red-500); }
    .cor-azul { color: var(--p-blue-500); }

    .aviso-titulares {
      display: flex; gap: 0.75rem; align-items: flex-start;
      background: var(--p-yellow-50); border: 1px solid var(--p-yellow-300);
      border-radius: 8px; padding: 1rem 1.25rem; margin: 0 auto 1.5rem; max-width: 560px;
    }
    .aviso-titulares.info { background: var(--p-blue-50); border-color: var(--p-blue-300); }
    .aviso-titulares .pi { color: var(--p-yellow-600); font-size: 1.25rem; flex-shrink: 0; margin-top: 0.1rem; }
    .aviso-titulares.info .pi { color: var(--p-blue-600); }
    .aviso-titulares strong { display: block; margin-bottom: 0.25rem; color: var(--p-yellow-800); }
    .aviso-titulares.info strong { color: var(--p-blue-800); }
    .aviso-titulares p { margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--p-surface-600); }
    .aviso-titulares ul { margin: 0; padding-left: 1.25rem; font-size: 0.875rem; color: var(--p-surface-700); }
    .aviso-titulares ul li { margin-bottom: 0.2rem; }

    @media (max-width: 768px) {
      .resumo-grid { grid-template-columns: repeat(2, 1fr); }
      .mapa-linha { grid-template-columns: 1fr; }
      .campo-arrow { display: none; }
    }
  `],
})
export class ImportacaoComponent {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly lancamentoSvc = inject(LancamentoService);
  private readonly messageSvc = inject(MessageService);

  protected readonly etapa = signal(1);
  protected readonly arquivo = signal<File | null>(null);
  protected get empresaId(): string | null {
    return this._empresaId ?? this.empresaStore.empresaAtiva()?.id ?? null;
  }
  protected set empresaId(v: string | null) { this._empresaId = v; }
  private _empresaId: string | null = null;
  protected tipoDefault: 'DESPESA' | 'RECEITA' = 'DESPESA';
  protected trocarEmpresa = false;

  protected readonly analise = signal<ImportacaoAnaliseResponse | null>(null);
  protected readonly preview = signal<ImportacaoPreviewResponse | null>(null);
  protected readonly resultado = signal<ImportacaoResultadoResponse | null>(null);

  protected readonly analisando = signal(false);
  protected readonly previewing = signal(false);
  protected readonly importando = signal(false);

  protected readonly camposSistema = CAMPOS_SISTEMA;
  protected mapeamento: Record<string, string | null> = {};

  protected readonly colunaOpts = computed(() => {
    const a = this.analise();
    if (!a) return [];
    return [
      { label: '— Não importar —', value: null },
      ...a.colunas.map(c => ({ label: c, value: c })),
    ];
  });

  protected get mapeamentoValido(): boolean {
    return CAMPOS_SISTEMA.filter(c => c.obrigatorio).every(c => !!this.mapeamento[c.chave]);
  }

  protected get alertasMapeamento(): string[] {
    const avisos: string[] = [];
    if (!this.mapeamento['col_tipo'])       avisos.push('Tipo (Receita/Despesa) — sem este campo, tudo entra como Despesa');
    if (!this.mapeamento['categoria_nome']) avisos.push('Categoria — categorias não serão criadas automaticamente');
    if (!this.mapeamento['contato_nome'])   avisos.push('Cliente / Fornecedor — contatos não serão criados automaticamente');
    if (!this.mapeamento['col_empresa'])    avisos.push('Empresa (Titular) — todos os lançamentos irão para a empresa selecionada no cabeçalho');
    return avisos;
  }

  protected readonly linhasValidas = computed<ImportacaoLinhaPreview[]>(() =>
    this.preview()?.itens.filter(i => i.valida) ?? []
  );

  protected readonly linhasComErro = computed<ImportacaoLinhaPreview[]>(() =>
    this.preview()?.itens.filter(i => !i.valida) ?? []
  );

  protected onFileSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) this.arquivo.set(input.files[0]);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    const file = event.dataTransfer?.files[0];
    if (file) this.arquivo.set(file);
  }

  protected analisar(): void {
    const file = this.arquivo();
    if (!file) return;
    this.analisando.set(true);
    this.lancamentoSvc.analisarImportacao(file).subscribe({
      next: (resp) => {
        this.analise.set(resp);
        this.mapeamento = {};
        this.sugerirMapeamento(resp.colunas);
        this.analisando.set(false);
        this.etapa.set(2);
      },
      error: () => {
        this.analisando.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro ao analisar a planilha.' });
      },
    });
  }

  private sugerirMapeamento(colunas: string[]): void {
    // Nomes exatos das colunas desta planilha + aliases genéricos
    const aliases: Record<string, string[]> = {
      descricao:        ['Histórico', 'descricao', 'descrição', 'historico', 'histórico', 'titulo', 'nome', 'lancamento', 'memo'],
      valor:            ['Valor', 'valor', 'value', 'montante', 'quantia', 'vl', 'vlr'],
      data_vencimento:  ['DATA', 'Data', 'vencimento', 'data_vencimento', 'dt_vencimento', 'venc', 'datavencimento'],
      data_competencia: ['DATA', 'Data', 'competencia', 'competência', 'data_competencia', 'emissao', 'emissão'],
      col_tipo:         ['CAP/CAR', 'Receitas/Despesas', 'cap/car', 'capcar', 'cap_car', 'tipo', 'natureza', 'receitas/despes', 'receitasdespesas', 'tipomovimento'],
      col_empresa:      ['Titular', 'empresa', 'titular', 'entidade', 'razaosocial', 'razão social', 'cnpj'],
      conta_banco:      ['Banco', 'banco', 'banc', 'instituicao', 'instituição', 'nomebanco'],
      conta_agencia:    ['Agencia', 'agencia', 'agenci', 'ag', 'agência', 'numagencia', 'numeroagencia'],
      conta_numero:     ['Conta', 'conta', 'contacorrente', 'numeroconta', 'numconta', 'cc', 'contabancaria'],
      categoria_nome:   ['Categoria', 'categoria', 'category', 'classificacao', 'classificação', 'planocontas', 'plano'],
      contato_nome:     ['Fornecedor / Cliente', 'fornecedor', 'cliente', 'contato', 'parceiro', 'favorecido', 'beneficiario', 'beneficiário', 'pagador'],
      observacoes:      ['observacoes', 'observações', 'obs', 'notas', 'complemento', 'detalhe'],
    };
    // Normaliza removendo acentos, espaços, separadores — e tenta match exato primeiro, depois "contém"
    const norm = (s: string) => s.toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[\s_\-\/\(\)\.&]/g, '');
    for (const [campo, possibilidades] of Object.entries(aliases)) {
      // 1. Match exato (após normalização)
      let match = colunas.find(c => possibilidades.some(p => norm(c) === norm(p)));
      // 2. Fallback: coluna contém o alias ou alias contém a coluna
      if (!match) {
        match = colunas.find(c => possibilidades.some(p => {
          const nc = norm(c), np = norm(p);
          return nc.length > 2 && np.length > 2 && (nc.includes(np) || np.includes(nc));
        }));
      }
      if (match) this.mapeamento[campo] = match;
    }
  }

  protected preVisualizar(): void {
    const file = this.arquivo();
    if (!file || !this.empresaId) return;
    this.previewing.set(true);
    this.lancamentoSvc.preVisualizarImportacao({
      file,
      empresaId: this.empresaId,
      tipo: this.tipoDefault,
      mapeamento: this.mapeamento as Record<string, string>,
    }).subscribe({
      next: (resp) => {
        this.preview.set(resp);
        this.previewing.set(false);
        this.etapa.set(3);
      },
      error: () => {
        this.previewing.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro na pré-visualização.' });
      },
    });
  }

  protected confirmar(): void {
    const file = this.arquivo();
    if (!file || !this.empresaId) return;
    this.importando.set(true);
    this.lancamentoSvc.confirmarImportacao({
      file,
      empresaId: this.empresaId,
      tipo: this.tipoDefault,
      mapeamento: this.mapeamento as Record<string, string>,
    }).subscribe({
      next: (resp) => {
        this.resultado.set(resp);
        this.importando.set(false);
        this.etapa.set(4);
        this.messageSvc.add({ severity: 'success', summary: `${resp.importadas} lançamentos importados!` });
      },
      error: () => {
        this.importando.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro ao importar.' });
      },
    });
  }

  protected reiniciar(): void {
    this.etapa.set(1);
    this.arquivo.set(null);
    this.analise.set(null);
    this.preview.set(null);
    this.resultado.set(null);
    this.mapeamento = {};
    this._empresaId = null;
    this.trocarEmpresa = false;
  }
}
