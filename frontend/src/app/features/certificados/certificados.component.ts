import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DatePickerModule } from 'primeng/datepicker';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { MessageModule } from 'primeng/message';
import { PasswordModule } from 'primeng/password';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { TextareaModule } from 'primeng/textarea';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import { firstValueFrom } from 'rxjs';

import {
  Certificado,
  CertificadoManual,
  CertificadoService,
  StatusValidade,
  TipoCertificado,
} from '../../core/services/certificado.service';
import { EmpresaService } from '../../core/services/empresa.service';
import { Pessoa, PessoaService } from '../../core/services/pessoa.service';

interface Opcao {
  label: string;
  value: string | null;
}

interface LinhaImport {
  id: number;
  file: File;
  nome: string;
  senha: string;
  status: 'pendente' | 'ok' | 'erro';
  msg: string;
}

@Component({
  selector: 'app-certificados',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule,
    ButtonModule,
    DatePickerModule,
    DialogModule,
    InputTextModule,
    MessageModule,
    PasswordModule,
    SelectModule,
    TableModule,
    TagModule,
    TextareaModule,
    ToastModule,
    TooltipModule,
  ],
  template: `
    <p-toast />
    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Certificados</h1>
          <p class="page-subtitle">Importação e controle de vencimentos (ICP-Brasil e SSL)</p>
        </div>
        <div class="header-acoes">
          <p-button label="Cadastro manual" icon="pi pi-plus" severity="secondary" (onClick)="abrirManual()" />
          <p-button label="Importar Certificado" icon="pi pi-upload" (onClick)="abrirImportar()" />
        </div>
      </div>

      <!-- Resumo -->
      <div class="resumo">
        <div class="card-resumo"><span class="num">{{ lista().length }}</span><span class="lbl">Total</span></div>
        <div class="card-resumo verde"><span class="num">{{ contar('valido') }}</span><span class="lbl">Válidos</span></div>
        <div class="card-resumo laranja"><span class="num">{{ contar('vencendo') }}</span><span class="lbl">Vencendo (30d)</span></div>
        <div class="card-resumo vermelho"><span class="num">{{ contar('vencido') }}</span><span class="lbl">Vencidos</span></div>
      </div>

      <!-- Filtros -->
      <div class="filtros">
        <input pInputText [(ngModel)]="busca" placeholder="Buscar nome, titular, documento..." />
        <p-select [options]="tipoFiltroOptions" [(ngModel)]="filtroTipo" optionLabel="label" optionValue="value" placeholder="Tipo" [style]="{ 'min-width': '160px' }" />
        <p-select [options]="statusFiltroOptions" [(ngModel)]="filtroStatus" optionLabel="label" optionValue="value" placeholder="Status" [style]="{ 'min-width': '160px' }" />
      </div>

      <p-table [value]="listaFiltrada()" [paginator]="listaFiltrada().length > 12" [rows]="12" styleClass="p-datatable-sm">
        <ng-template pTemplate="header">
          <tr>
            <th>Nome</th>
            <th>Tipo</th>
            <th>Empresa</th>
            <th>Titular / Documento</th>
            <th>Validade</th>
            <th>Situação</th>
            <th style="width:178px">Ações</th>
          </tr>
        </ng-template>
        <ng-template pTemplate="body" let-c>
          <tr>
            <td><strong>{{ c.nome }}</strong></td>
            <td><p-tag [value]="tipoLabel(c.tipo)" severity="secondary" /></td>
            <td>{{ c.nome_empresa || '— Global' }}</td>
            <td>
              <div>{{ c.titular || '—' }}</div>
              @if (c.documento) { <small class="doc">{{ formatDoc(c.documento) }}</small> }
            </td>
            <td>{{ formatDate(c.validade_fim) }}</td>
            <td>
              <p-tag [value]="situacaoTexto(c)" [severity]="situacaoSeveridade(c.status_validade)" />
            </td>
            <td>
              <div class="acoes">
                <p-button icon="pi pi-users" [text]="true" pTooltip="Pessoas com este certificado" (onClick)="abrirPessoas(c)" />
                @if (c.tem_arquivo) {
                  <p-button icon="pi pi-download" [text]="true" pTooltip="Baixar arquivo" (onClick)="baixar(c)" />
                }
                @if (c.tem_senha) {
                  <p-button icon="pi pi-key" [text]="true" pTooltip="Ver senha" (onClick)="verSenha(c)" />
                }
                <p-button icon="pi pi-pencil" [text]="true" pTooltip="Editar" (onClick)="abrirEditar(c)" />
                <p-button icon="pi pi-ban" [text]="true" severity="danger" pTooltip="Inativar" (onClick)="inativar(c)" />
              </div>
            </td>
          </tr>
        </ng-template>
        <ng-template pTemplate="emptymessage">
          <tr><td colspan="7" class="empty-msg">Nenhum certificado cadastrado. Use <strong>Importar Certificado</strong> para começar.</td></tr>
        </ng-template>
      </p-table>
    </div>

    <!-- Dialog: Importar em lote -->
    <p-dialog header="Importar Certificados" [(visible)]="dialogImportar" [modal]="true" [style]="{ width: '760px', 'max-width': '96vw' }">
      <div class="form">
        <div class="field">
          <label>Selecione um ou vários arquivos * <small>(.pfx, .p12, .cer, .crt, .pem)</small></label>
          <input type="file" multiple accept=".pfx,.p12,.cer,.crt,.pem" (change)="onArquivos($event)" />
        </div>
        @if (linhas().length) {
          <div class="field">
            <label>Empresa para todos (opcional)</label>
            <p-select [options]="empresaOptions()" [(ngModel)]="impEmpresaLote" optionLabel="label" optionValue="value" [filter]="true" filterBy="label" placeholder="Vincular automaticamente pelo CNPJ" [style]="{ width: '100%' }" />
            <small class="hint">Em branco: o sistema vincula cada certificado à empresa de mesmo CNPJ e detecta o tipo automaticamente.</small>
          </div>
          <div class="lote">
            <div class="lote-head"><span>Arquivo</span><span>Nome</span><span>Senha (.pfx)</span><span>Status</span></div>
            @for (l of linhas(); track l.id) {
              <div class="lote-row">
                <span class="fn" [pTooltip]="l.file.name">{{ l.file.name }}</span>
                <input pInputText [(ngModel)]="l.nome" placeholder="Nome" />
                <input pInputText type="password" [(ngModel)]="l.senha" placeholder="senha" />
                <span class="st" [class.ok]="l.status === 'ok'" [class.erro]="l.status === 'erro'">{{ statusLabel(l) }}</span>
              </div>
            }
          </div>
        }
      </div>
      <ng-template pTemplate="footer">
        <p-button label="Fechar" severity="secondary" (onClick)="dialogImportar.set(false)" [disabled]="importando()" />
        <p-button [label]="'Importar ' + linhas().length" icon="pi pi-upload" [loading]="importando()" [disabled]="!linhas().length" (onClick)="importarLote()" />
      </ng-template>
    </p-dialog>

    <!-- Dialog: Manual / Editar -->
    <p-dialog [header]="editandoId() ? 'Editar Certificado' : 'Cadastro Manual'" [(visible)]="dialogManual" [modal]="true" [style]="{ width: '560px', 'max-width': '95vw' }">
      <div class="form">
        <div class="form-row">
          <div class="field flex-2">
            <label>Nome / apelido *</label>
            <input pInputText [(ngModel)]="manNome" [style]="{ width: '100%' }" />
          </div>
          <div class="field">
            <label>Tipo *</label>
            <p-select [options]="tipoOptions" [(ngModel)]="manTipo" optionLabel="label" optionValue="value" [style]="{ width: '100%' }" />
          </div>
        </div>
        <div class="field">
          <label>Empresa (opcional)</label>
          <p-select [options]="empresaOptions()" [(ngModel)]="manEmpresa" optionLabel="label" optionValue="value" [filter]="true" filterBy="label" placeholder="Global (todas)" [style]="{ width: '100%' }" />
        </div>
        <div class="form-row">
          <div class="field">
            <label>Validade início</label>
            <p-datepicker [(ngModel)]="manInicio" dateFormat="dd/mm/yy" [showIcon]="true" [disabled]="!!editandoId()" [style]="{ width: '100%' }" appendTo="body" />
          </div>
          <div class="field">
            <label>Validade fim</label>
            <p-datepicker [(ngModel)]="manFim" dateFormat="dd/mm/yy" [showIcon]="true" [disabled]="!!editandoId()" [style]="{ width: '100%' }" appendTo="body" />
          </div>
        </div>
        @if (editandoId()) {
          <small class="hint">As datas de validade não podem ser alteradas após a inclusão (são a referência do controle de vencimento).</small>
        }
        <div class="field"><label>Titular</label><input pInputText [(ngModel)]="manTitular" [style]="{ width: '100%' }" /></div>
        <div class="form-row">
          <div class="field"><label>Documento (CNPJ/CPF)</label><input pInputText [(ngModel)]="manDocumento" [style]="{ width: '100%' }" /></div>
          <div class="field"><label>Emissor</label><input pInputText [(ngModel)]="manEmissor" [style]="{ width: '100%' }" /></div>
        </div>
        <div class="field"><label>Observações</label><textarea pTextarea [(ngModel)]="manObs" rows="2" [style]="{ width: '100%' }"></textarea></div>
      </div>
      <ng-template pTemplate="footer">
        <p-button label="Cancelar" severity="secondary" (onClick)="dialogManual.set(false)" />
        <p-button [label]="editandoId() ? 'Salvar' : 'Cadastrar'" icon="pi pi-check" [loading]="salvando()" (onClick)="salvarManual()" />
      </ng-template>
    </p-dialog>

    <!-- Dialog: Senha -->
    <p-dialog header="Senha do certificado" [(visible)]="dialogSenha" [modal]="true" [style]="{ width: '420px' }">
      <p class="senha-info">Use com cuidado. A senha é exibida apenas para você, que tem acesso a este certificado.</p>
      <div class="senha-box">
        <code>{{ senhaRevelada() }}</code>
        <p-button icon="pi pi-copy" [text]="true" pTooltip="Copiar" (onClick)="copiarSenha()" />
      </div>
      <ng-template pTemplate="footer">
        <p-button label="Fechar" (onClick)="dialogSenha.set(false)" />
      </ng-template>
    </p-dialog>

    <!-- Dialog: Pessoas com o certificado -->
    <p-dialog [header]="'Pessoas — ' + (certPessoas()?.nome || '')" [(visible)]="dialogPessoas" [modal]="true" [style]="{ width: '600px', 'max-width': '95vw' }">
      <div class="add-pessoa">
        <p-select [options]="pessoasDisponiveis()" [(ngModel)]="pessoaParaAdd" optionLabel="nome" optionValue="id"
          [filter]="true" filterBy="nome" placeholder="Adicionar pessoa existente" [style]="{ flex: '1' }" appendTo="body" />
        <p-button label="Adicionar" icon="pi pi-plus" [disabled]="!pessoaParaAdd" (onClick)="adicionarPessoa()" />
      </div>
      <small class="hint">Para cadastrar uma pessoa nova ou associar vários certificados de uma vez, use o menu <strong>Pessoas</strong>.</small>

      @if (pessoasDoCert().length) {
        <div class="pessoas-lista">
          @for (p of pessoasDoCert(); track p.id) {
            <div class="pessoa-item">
              <div class="pi-info">
                <span class="pi-nome">{{ p.nome }}</span>
                <span class="pi-sub">
                  <p-tag [value]="p.tipo === 'interno' ? 'Interno' : 'Externo'" [severity]="p.tipo === 'interno' ? 'info' : 'warn'" />
                  {{ p.tipo === 'interno' ? (p.setor || '') : (p.empresa_externa || '') }}
                  @if (p.email) { · {{ p.email }} }
                  @if (p.telefone) { · {{ p.telefone }} }
                </span>
              </div>
              <p-button icon="pi pi-times" [text]="true" severity="danger" pTooltip="Remover" (onClick)="removerPessoa(p)" />
            </div>
          }
        </div>
      } @else {
        <p class="empty-msg">Nenhuma pessoa associada a este certificado ainda.</p>
      }
      <ng-template pTemplate="footer">
        <p-button label="Fechar" (onClick)="dialogPessoas.set(false)" />
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .page { padding: 1.5rem; }
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
    .page-title { margin: 0; font-size: 1.5rem; }
    .page-subtitle { margin: 0.2rem 0 0; color: var(--p-surface-500); font-size: 0.9rem; }
    .header-acoes { display: flex; gap: 0.5rem; }

    .resumo { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1.25rem; }
    .card-resumo { background: var(--p-surface-0); border: 1px solid var(--p-surface-200); border-left: 4px solid var(--p-surface-300); border-radius: 8px; padding: 0.75rem 1rem; display: flex; flex-direction: column; }
    .card-resumo .num { font-size: 1.5rem; font-weight: 700; }
    .card-resumo .lbl { font-size: 0.75rem; color: var(--p-surface-500); text-transform: uppercase; letter-spacing: 0.03em; }
    .card-resumo.verde { border-left-color: #22c55e; }
    .card-resumo.laranja { border-left-color: #f97316; }
    .card-resumo.vermelho { border-left-color: #ef4444; }

    .filtros { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
    .filtros input { flex: 1; min-width: 220px; }

    .acoes { display: flex; gap: 0.1rem; }
    .doc { color: var(--p-surface-500); }
    .empty-msg { text-align: center; color: var(--p-surface-400); padding: 2.5rem 1rem; }

    .form { display: flex; flex-direction: column; gap: 0.75rem; padding: 0.25rem 0; }
    .form-row { display: flex; gap: 0.75rem; }
    .field { display: flex; flex-direction: column; gap: 0.3rem; flex: 1; }
    .field.flex-2 { flex: 2; }
    .field label { font-size: 0.8rem; font-weight: 600; }
    .field small { font-weight: 400; color: var(--p-surface-500); }
    input[type=file] { font-size: 0.85rem; }
    .hint { color: var(--p-surface-500); font-size: 0.75rem; }

    .lote { border: 1px solid var(--p-surface-200); border-radius: 8px; max-height: 320px; overflow-y: auto; }
    .lote-head, .lote-row {
      display: grid; grid-template-columns: 1.5fr 1.2fr 1fr 1.1fr;
      gap: 0.5rem; align-items: center; padding: 0.4rem 0.6rem;
    }
    .lote-head {
      background: var(--p-surface-100); font-size: 0.7rem; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.03em; color: var(--p-surface-500);
      position: sticky; top: 0; z-index: 1;
    }
    .lote-row { border-top: 1px solid var(--p-surface-100); }
    .lote-row .fn { font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .lote-row input { font-size: 0.84rem; padding: 0.3rem 0.5rem; width: 100%; }
    .st { font-size: 0.78rem; color: var(--p-surface-500); }
    .st.ok { color: #16a34a; font-weight: 600; }
    .st.erro { color: #dc2626; font-weight: 600; }

    .senha-info { font-size: 0.82rem; color: var(--p-surface-500); margin: 0 0 0.75rem; }
    .senha-box { display: flex; align-items: center; gap: 0.5rem; background: var(--p-surface-100); border-radius: 6px; padding: 0.5rem 0.75rem; }
    .senha-box code { flex: 1; font-size: 1rem; word-break: break-all; }

    .add-pessoa { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.4rem; }
    .pessoas-lista { display: flex; flex-direction: column; margin-top: 0.75rem; border: 1px solid var(--p-surface-200); border-radius: 8px; overflow: hidden; }
    .pessoa-item { display: flex; align-items: center; justify-content: space-between; gap: 0.5rem; padding: 0.5rem 0.75rem; border-top: 1px solid var(--p-surface-100); }
    .pessoa-item:first-child { border-top: 0; }
    .pi-info { display: flex; flex-direction: column; gap: 0.2rem; min-width: 0; }
    .pi-nome { font-weight: 600; font-size: 0.9rem; }
    .pi-sub { font-size: 0.78rem; color: var(--p-surface-500); display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap; }
  `],
})
export class CertificadosComponent implements OnInit {
  private readonly service = inject(CertificadoService);
  private readonly empresaService = inject(EmpresaService);
  private readonly pessoaService = inject(PessoaService);
  private readonly messageService = inject(MessageService);

  protected readonly lista = signal<Certificado[]>([]);
  protected readonly empresaOptions = signal<Opcao[]>([{ label: 'Global (todas)', value: null }]);

  protected busca = '';
  protected filtroTipo: TipoCertificado | null = null;
  protected filtroStatus: StatusValidade | null = null;

  protected readonly tipoOptions: Opcao[] = [
    { label: 'e-CNPJ', value: 'e_cnpj' },
    { label: 'e-CPF', value: 'e_cpf' },
    { label: 'SSL / Domínio', value: 'ssl' },
    { label: 'Outro', value: 'outro' },
  ];
  protected readonly tipoFiltroOptions: Opcao[] = [{ label: 'Todos os tipos', value: null }, ...this.tipoOptions];
  protected readonly statusFiltroOptions: Opcao[] = [
    { label: 'Todas as situações', value: null },
    { label: 'Válido', value: 'valido' },
    { label: 'Vencendo', value: 'vencendo' },
    { label: 'Vencido', value: 'vencido' },
  ];

  protected readonly listaFiltrada = computed(() => {
    const b = this.busca.trim().toLowerCase();
    return this.lista().filter((c) => {
      if (this.filtroTipo && c.tipo !== this.filtroTipo) return false;
      if (this.filtroStatus && c.status_validade !== this.filtroStatus) return false;
      if (b) {
        const alvo = `${c.nome} ${c.titular ?? ''} ${c.documento ?? ''} ${c.emissor ?? ''}`.toLowerCase();
        if (!alvo.includes(b)) return false;
      }
      return true;
    });
  });

  // Importar em lote
  protected readonly dialogImportar = signal(false);
  protected readonly linhas = signal<LinhaImport[]>([]);
  protected impEmpresaLote: string | null = null;
  protected readonly importando = signal(false);
  private _seq = 0;

  // Manual / editar
  protected readonly dialogManual = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected manNome = '';
  protected manTipo: TipoCertificado = 'outro';
  protected manEmpresa: string | null = null;
  protected manInicio: Date | null = null;
  protected manFim: Date | null = null;
  protected manTitular = '';
  protected manDocumento = '';
  protected manEmissor = '';
  protected manObs = '';

  // Senha
  protected readonly dialogSenha = signal(false);
  protected readonly senhaRevelada = signal('');
  protected readonly salvando = signal(false);

  // Pessoas do certificado
  protected readonly dialogPessoas = signal(false);
  protected readonly certPessoas = signal<Certificado | null>(null);
  protected readonly pessoasDoCert = signal<Pessoa[]>([]);
  protected readonly todasPessoas = signal<Pessoa[]>([]);
  protected pessoaParaAdd: string | null = null;
  protected readonly pessoasDisponiveis = computed(() => {
    const associadas = new Set(this.pessoasDoCert().map((p) => p.id));
    return this.todasPessoas().filter((p) => !associadas.has(p.id));
  });

  ngOnInit(): void {
    this.carregar();
    this.empresaService.listar().subscribe({
      next: (lista) =>
        this.empresaOptions.set([
          { label: 'Global (todas)', value: null },
          ...lista.map((e: { id: string; nome_principal: string; nome_alternativo?: string | null }) => ({
            label: e.nome_alternativo ?? e.nome_principal,
            value: e.id,
          })),
        ]),
      error: () => {},
    });
  }

  private carregar(): void {
    this.service.listar().subscribe({
      next: (data) => this.lista.set(data),
      error: (err) => this.erro(err, 'Erro ao carregar certificados.'),
    });
  }

  protected contar(status: StatusValidade): number {
    return this.lista().filter((c) => c.status_validade === status).length;
  }

  // ── Importar em lote ──────────────────────────────────────────────────────
  protected abrirImportar(): void {
    this.linhas.set([]);
    this.impEmpresaLote = null;
    this.dialogImportar.set(true);
  }

  protected onArquivos(ev: Event): void {
    const input = ev.target as HTMLInputElement;
    const novos: LinhaImport[] = Array.from(input.files ?? []).map((f) => ({
      id: ++this._seq,
      file: f,
      nome: f.name.replace(/\.[^.]+$/, ''),
      senha: '',
      status: 'pendente',
      msg: '',
    }));
    this.linhas.set([...this.linhas(), ...novos]);
    input.value = ''; // permite reselecionar os mesmos arquivos
  }

  protected statusLabel(l: LinhaImport): string {
    if (l.status === 'ok') return '✓ Importado';
    if (l.status === 'erro') return `✗ ${l.msg || 'erro'}`;
    return 'pendente';
  }

  protected async importarLote(): Promise<void> {
    this.importando.set(true);
    let ok = 0;
    let erro = 0;
    for (const l of this.linhas()) {
      if (l.status === 'ok') continue;
      const form = new FormData();
      form.append('file', l.file);
      form.append('nome', (l.nome || l.file.name).trim());
      if (l.senha) form.append('senha', l.senha);
      if (this.impEmpresaLote) form.append('empresa_id', this.impEmpresaLote);
      try {
        await firstValueFrom(this.service.importar(form));
        l.status = 'ok';
        ok++;
      } catch (e) {
        l.status = 'erro';
        l.msg = this.msgErro(e);
        erro++;
      }
      this.linhas.set([...this.linhas()]);
    }
    this.importando.set(false);
    this.messageService.add({
      severity: erro ? 'warn' : 'success',
      summary: 'Importação concluída',
      detail: `${ok} importado(s), ${erro} com erro.`,
    });
    this.carregar();
  }

  private msgErro(e: unknown): string {
    const x = e as { error?: { detail?: unknown } };
    return typeof x.error?.detail === 'string' ? x.error.detail : 'falhou';
  }

  // ── Manual / Editar ───────────────────────────────────────────────────────
  protected abrirManual(): void {
    this.editandoId.set(null);
    this.manNome = '';
    this.manTipo = 'outro';
    this.manEmpresa = null;
    this.manInicio = null;
    this.manFim = null;
    this.manTitular = '';
    this.manDocumento = '';
    this.manEmissor = '';
    this.manObs = '';
    this.dialogManual.set(true);
  }

  protected abrirEditar(c: Certificado): void {
    this.editandoId.set(c.id);
    this.manNome = c.nome;
    this.manTipo = c.tipo;
    this.manEmpresa = c.empresa_id;
    this.manInicio = c.validade_inicio ? new Date(c.validade_inicio + 'T00:00:00') : null;
    this.manFim = c.validade_fim ? new Date(c.validade_fim + 'T00:00:00') : null;
    this.manTitular = c.titular ?? '';
    this.manDocumento = c.documento ?? '';
    this.manEmissor = c.emissor ?? '';
    this.manObs = c.observacoes ?? '';
    this.dialogManual.set(true);
  }

  protected salvarManual(): void {
    if (this.manNome.trim().length < 2) {
      this.messageService.add({ severity: 'warn', summary: 'Informe um nome (mín. 2 letras).' });
      return;
    }
    const id = this.editandoId();
    const payload: CertificadoManual = {
      nome: this.manNome.trim(),
      tipo: this.manTipo,
      empresa_id: this.manEmpresa,
      titular: this.manTitular || null,
      documento: this.manDocumento || null,
      emissor: this.manEmissor || null,
      observacoes: this.manObs || null,
    };
    // Datas só na criação — após a inclusão são imutáveis.
    if (!id) {
      payload.validade_inicio = this.toISO(this.manInicio);
      payload.validade_fim = this.toISO(this.manFim);
    }
    this.salvando.set(true);
    const obs$ = id ? this.service.atualizar(id, payload) : this.service.criarManual(payload);
    obs$.subscribe({
      next: () => {
        this.salvando.set(false);
        this.dialogManual.set(false);
        this.messageService.add({ severity: 'success', summary: id ? 'Certificado atualizado.' : 'Certificado cadastrado.' });
        this.carregar();
      },
      error: (err) => {
        this.salvando.set(false);
        this.erro(err, 'Erro ao salvar certificado.');
      },
    });
  }

  protected inativar(c: Certificado): void {
    this.service.inativar(c.id).subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Certificado inativado.' });
        this.carregar();
      },
      error: (err) => this.erro(err, 'Erro ao inativar.'),
    });
  }

  protected baixar(c: Certificado): void {
    this.service.download(c.id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = c.arquivo_nome ?? 'certificado';
        a.click();
        URL.revokeObjectURL(url);
      },
      error: async (err: HttpErrorResponse) => {
        if (err.error instanceof Blob) {
          try {
            const text = await err.error.text();
            const json = JSON.parse(text);
            const detail = typeof json.detail === 'string' ? json.detail : 'Erro ao baixar arquivo.';
            this.messageService.add({ severity: 'error', summary: 'Erro', detail });
          } catch {
            this.messageService.add({ severity: 'error', summary: 'Erro', detail: 'Erro ao baixar arquivo.' });
          }
        } else {
          this.erro(err, 'Erro ao baixar arquivo.');
        }
      },
    });
  }

  // ── Pessoas do certificado ────────────────────────────────────────────────
  protected abrirPessoas(c: Certificado): void {
    this.certPessoas.set(c);
    this.pessoaParaAdd = null;
    this.pessoasDoCert.set([]);
    this.dialogPessoas.set(true);
    this.pessoaService.pessoasDoCertificado(c.id).subscribe({
      next: (ps) => this.pessoasDoCert.set(ps),
      error: (err) => this.erro(err, 'Erro ao carregar pessoas.'),
    });
    this.pessoaService.listar().subscribe({
      next: (ps) => this.todasPessoas.set(ps),
      error: () => {},
    });
  }

  protected adicionarPessoa(): void {
    const cert = this.certPessoas();
    if (!cert || !this.pessoaParaAdd) return;
    this.pessoaService.associar(cert.id, this.pessoaParaAdd).subscribe({
      next: () => {
        this.pessoaParaAdd = null;
        this.pessoaService.pessoasDoCertificado(cert.id).subscribe((ps) => this.pessoasDoCert.set(ps));
        this.carregar();
      },
      error: (err) => this.erro(err, 'Erro ao associar pessoa.'),
    });
  }

  protected removerPessoa(p: Pessoa): void {
    const cert = this.certPessoas();
    if (!cert) return;
    this.pessoaService.desassociar(cert.id, p.id).subscribe({
      next: () => {
        this.pessoasDoCert.set(this.pessoasDoCert().filter((x) => x.id !== p.id));
        this.carregar();
      },
      error: (err) => this.erro(err, 'Erro ao remover associação.'),
    });
  }

  protected verSenha(c: Certificado): void {
    this.service.revelarSenha(c.id).subscribe({
      next: (r) => {
        this.senhaRevelada.set(r.senha);
        this.dialogSenha.set(true);
      },
      error: (err) => this.erro(err, 'Erro ao obter a senha.'),
    });
  }

  protected copiarSenha(): void {
    navigator.clipboard?.writeText(this.senhaRevelada()).then(
      () => this.messageService.add({ severity: 'success', summary: 'Senha copiada.' }),
      () => {},
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  protected tipoLabel(t: TipoCertificado): string {
    return this.tipoOptions.find((o) => o.value === t)?.label ?? t;
  }

  protected situacaoTexto(c: Certificado): string {
    if (c.dias_para_vencer === null) return 'Sem data';
    if (c.dias_para_vencer < 0) return `Vencido há ${Math.abs(c.dias_para_vencer)}d`;
    if (c.status_validade === 'vencendo') return `Vence em ${c.dias_para_vencer}d`;
    return `Faltam ${c.dias_para_vencer}d`;
  }

  protected situacaoSeveridade(s: StatusValidade): 'success' | 'warn' | 'danger' | 'secondary' {
    return s === 'valido' ? 'success' : s === 'vencendo' ? 'warn' : s === 'vencido' ? 'danger' : 'secondary';
  }

  protected formatDate(iso: string | null): string {
    if (!iso) return '—';
    const [y, m, d] = iso.split('-');
    return `${d}/${m}/${y}`;
  }

  protected formatDoc(doc: string): string {
    const d = doc.replace(/\D/g, '');
    if (d.length === 14) return d.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    if (d.length === 11) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    return doc;
  }

  private toISO(d: Date | null): string | null {
    if (!d) return null;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  private erro(err: unknown, fallback: string): void {
    const e = err as { error?: { detail?: unknown } };
    const detail = typeof e.error?.detail === 'string' ? e.error.detail : fallback;
    this.messageService.add({ severity: 'error', summary: 'Erro', detail });
  }
}
