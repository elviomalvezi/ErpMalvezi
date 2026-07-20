import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AccordionModule } from 'primeng/accordion';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { MessageModule } from 'primeng/message';
import { MultiSelectModule } from 'primeng/multiselect';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { TextareaModule } from 'primeng/textarea';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import { forkJoin } from 'rxjs';

import { CertificadoService } from '../../core/services/certificado.service';
import {
  CertificadoResumoItem,
  Pessoa,
  PessoaPayload,
  PessoaService,
  TipoPessoa,
} from '../../core/services/pessoa.service';
import { StatusValidade } from '../../core/services/certificado.service';

interface CertOpcao {
  label: string;
  value: string;
}

interface GrupoEmpresa {
  empresa: string;
  certs: CertificadoResumoItem[];
}

@Component({
  selector: 'app-pessoas',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule,
    AccordionModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    MessageModule,
    MultiSelectModule,
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
          <h1 class="page-title">Pessoas dos Certificados</h1>
          <p class="page-subtitle">Quem possui cada certificado instalado — para consulta</p>
        </div>
        <p-button label="Nova Pessoa" icon="pi pi-user-plus" (onClick)="abrirNovo()" />
      </div>

      <div class="filtros">
        <input pInputText [(ngModel)]="busca" placeholder="Buscar nome, e-mail, setor, empresa..." />
        <p-select [options]="tipoFiltroOptions" [(ngModel)]="filtroTipo" optionLabel="label" optionValue="value" placeholder="Tipo" [style]="{ 'min-width': '160px' }" />
      </div>

      <p-table [value]="listaFiltrada()" [paginator]="listaFiltrada().length > 12" [rows]="12" styleClass="p-datatable-sm">
        <ng-template pTemplate="header">
          <tr>
            <th style="width:3rem"></th>
            <th>Nome</th><th>Tipo</th><th>Setor / Empresa</th><th>E-mail</th><th>Telefone</th>
            <th style="width:110px;text-align:center">Certificados</th><th style="width:90px">Ações</th>
          </tr>
        </ng-template>
        <ng-template pTemplate="body" let-p>
          <tr [class.linha-aberta]="expandedKeys()[p.id]">
            <td>
              <p-button [text]="true" [rounded]="true" [disabled]="!p.total_certificados"
                [icon]="expandedKeys()[p.id] ? 'pi pi-chevron-down' : 'pi pi-chevron-right'"
                pTooltip="Ver certificados por empresa" (onClick)="toggle(p)" />
            </td>
            <td><strong>{{ p.nome }}</strong></td>
            <td><p-tag [value]="p.tipo === 'interno' ? 'Interno' : 'Externo'" [severity]="p.tipo === 'interno' ? 'info' : 'warn'" /></td>
            <td>{{ p.tipo === 'interno' ? (p.setor || '—') : (p.empresa_externa || '—') }}</td>
            <td>{{ p.email || '—' }}</td>
            <td>{{ p.telefone || '—' }}</td>
            <td style="text-align:center"><p-tag [value]="p.total_certificados" severity="secondary" /></td>
            <td>
              <p-button icon="pi pi-pencil" [text]="true" pTooltip="Editar / associar certificados" (onClick)="abrirEditar(p)" />
              <p-button icon="pi pi-ban" [text]="true" severity="danger" pTooltip="Inativar" (onClick)="inativar(p)" />
            </td>
          </tr>
          @if (expandedKeys()[p.id]) {
            <tr class="exp-row">
              <td colspan="8" class="exp-cell">
                @if (detalhes()[p.id]; as grupos) {
                  @if (grupos.length) {
                    <p-accordion [multiple]="true" [value]="[grupos[0].empresa]">
                      @for (g of grupos; track g.empresa) {
                        <p-accordion-panel [value]="g.empresa">
                          <p-accordion-header>
                            <span class="acc-emp"><i class="pi pi-building"></i> {{ g.empresa }}
                              <span class="acc-count">{{ g.certs.length }}</span></span>
                          </p-accordion-header>
                          <p-accordion-content>
                            @for (c of g.certs; track c.id) {
                              <div class="cert-linha">
                                <span class="cl-nome">{{ c.nome }}</span>
                                <span class="cl-val">{{ formatDate(c.validade_fim) }}</span>
                                <p-tag [value]="statusTexto(c.status_validade)" [severity]="statusSev(c.status_validade)" />
                              </div>
                            }
                          </p-accordion-content>
                        </p-accordion-panel>
                      }
                    </p-accordion>
                  } @else {
                    <div class="sem-certs">Nenhum certificado associado.</div>
                  }
                } @else {
                  <div class="sem-certs"><i class="pi pi-spin pi-spinner"></i> Carregando...</div>
                }
              </td>
            </tr>
          }
        </ng-template>
        <ng-template pTemplate="emptymessage">
          <tr><td colspan="8" class="empty-msg">Nenhuma pessoa cadastrada.</td></tr>
        </ng-template>
      </p-table>
    </div>

    <p-dialog [header]="editandoId() ? 'Editar Pessoa' : 'Nova Pessoa'" [(visible)]="dialog" [modal]="true" [style]="{ width: '560px', 'max-width': '95vw' }">
      <div class="form">
        <div class="form-row">
          <div class="field flex-2"><label>Nome *</label><input pInputText [(ngModel)]="fNome" [style]="{ width: '100%' }" /></div>
          <div class="field"><label>Tipo *</label>
            <p-select [options]="tipoOptions" [(ngModel)]="fTipo" optionLabel="label" optionValue="value" [style]="{ width: '100%' }" />
          </div>
        </div>
        <div class="form-row">
          @if (fTipo === 'interno') {
            <div class="field"><label>Setor</label><input pInputText [(ngModel)]="fSetor" placeholder="Ex: Fiscal, Financeiro" [style]="{ width: '100%' }" /></div>
          } @else {
            <div class="field"><label>Empresa (externa)</label><input pInputText [(ngModel)]="fEmpresa" placeholder="Nome da empresa/contabilidade" [style]="{ width: '100%' }" /></div>
          }
          <div class="field"><label>Telefone</label><input pInputText [(ngModel)]="fTelefone" placeholder="(00) 00000-0000" [style]="{ width: '100%' }" /></div>
        </div>
        <div class="field"><label>E-mail</label><input pInputText [(ngModel)]="fEmail" type="email" [style]="{ width: '100%' }" /></div>
        <div class="field">
          <label>Certificados que esta pessoa possui</label>
          <p-multiselect [options]="certOptions()" [(ngModel)]="fCertIds" optionLabel="label" optionValue="value"
            [filter]="true" filterBy="label" placeholder="Selecione os certificados" display="chip"
            [style]="{ width: '100%' }" appendTo="body" />
        </div>
        <div class="field"><label>Observações</label><textarea pTextarea [(ngModel)]="fObs" rows="2" [style]="{ width: '100%' }"></textarea></div>
      </div>
      <ng-template pTemplate="footer">
        <p-button label="Cancelar" severity="secondary" (onClick)="dialog.set(false)" />
        <p-button [label]="editandoId() ? 'Salvar' : 'Cadastrar'" icon="pi pi-check" [loading]="salvando()" (onClick)="salvar()" />
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .page { padding: 1.5rem; }
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1.25rem; }
    .page-title { margin: 0; font-size: 1.5rem; }
    .page-subtitle { margin: 0.2rem 0 0; color: var(--p-surface-500); font-size: 0.9rem; }
    .filtros { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
    .filtros input { flex: 1; min-width: 240px; }
    .empty-msg { text-align: center; color: var(--p-surface-400); padding: 2.5rem 1rem; }
    .form { display: flex; flex-direction: column; gap: 0.75rem; padding: 0.25rem 0; }
    .form-row { display: flex; gap: 0.75rem; }
    .field { display: flex; flex-direction: column; gap: 0.3rem; flex: 1; }
    .field.flex-2 { flex: 2; }
    .field label { font-size: 0.8rem; font-weight: 600; }

    .exp-cell { background: var(--p-surface-50); padding: 0.75rem 1.25rem; }
    .acc-emp { display: inline-flex; align-items: center; gap: 0.5rem; font-weight: 600; }
    .acc-emp i { color: var(--p-primary-color); }
    .acc-count { background: var(--p-surface-200); color: var(--p-surface-700); font-size: 0.7rem; font-weight: 700; padding: 0.05rem 0.45rem; border-radius: 10px; }
    .cert-linha { display: flex; align-items: center; gap: 0.75rem; padding: 0.4rem 0; border-bottom: 1px dashed var(--p-surface-200); }
    .cert-linha:last-child { border-bottom: 0; }
    .cl-nome { flex: 1; font-size: 0.88rem; }
    .cl-val { font-size: 0.82rem; color: var(--p-surface-500); white-space: nowrap; }
    .sem-certs { color: var(--p-surface-500); font-size: 0.85rem; padding: 0.5rem 0; }
  `],
})
export class PessoasComponent implements OnInit {
  private readonly service = inject(PessoaService);
  private readonly certService = inject(CertificadoService);
  private readonly messageService = inject(MessageService);

  protected readonly lista = signal<Pessoa[]>([]);
  protected readonly certOptions = signal<CertOpcao[]>([]);
  protected busca = '';
  protected filtroTipo: TipoPessoa | null = null;

  protected readonly tipoOptions = [
    { label: 'Interno', value: 'interno' },
    { label: 'Externo', value: 'externo' },
  ];
  protected readonly tipoFiltroOptions = [{ label: 'Todos', value: null }, ...this.tipoOptions];

  protected readonly listaFiltrada = computed(() => {
    const b = this.busca.trim().toLowerCase();
    return this.lista().filter((p) => {
      if (this.filtroTipo && p.tipo !== this.filtroTipo) return false;
      if (b) {
        const alvo = `${p.nome} ${p.email ?? ''} ${p.setor ?? ''} ${p.empresa_externa ?? ''}`.toLowerCase();
        if (!alvo.includes(b)) return false;
      }
      return true;
    });
  });

  protected readonly dialog = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected readonly salvando = signal(false);
  protected fNome = '';
  protected fEmail = '';
  protected fTipo: TipoPessoa = 'interno';
  protected fSetor = '';
  protected fEmpresa = '';
  protected fTelefone = '';
  protected fObs = '';
  protected fCertIds: string[] = [];

  // Expansão de linha: certificados agrupados por empresa
  protected readonly expandedKeys = signal<Record<string, boolean>>({});
  protected readonly detalhes = signal<Record<string, GrupoEmpresa[]>>({});

  protected toggle(p: Pessoa): void {
    const atual = { ...this.expandedKeys() };
    if (atual[p.id]) {
      delete atual[p.id];
    } else {
      atual[p.id] = true;
      if (!this.detalhes()[p.id]) this.carregarDetalhe(p.id);
    }
    this.expandedKeys.set(atual);
  }

  private carregarDetalhe(id: string): void {
    this.service.obter(id).subscribe({
      next: (det) => {
        const mapa = new Map<string, CertificadoResumoItem[]>();
        for (const c of det.certificados) {
          const emp = c.nome_empresa || 'Global (todas as empresas)';
          (mapa.get(emp) ?? mapa.set(emp, []).get(emp)!).push(c);
        }
        const grupos: GrupoEmpresa[] = Array.from(mapa.entries())
          .map(([empresa, certs]) => ({ empresa, certs }))
          .sort((a, b) => a.empresa.localeCompare(b.empresa));
        this.detalhes.set({ ...this.detalhes(), [id]: grupos });
      },
      error: (err) => this.erro(err, 'Erro ao carregar certificados da pessoa.'),
    });
  }

  protected formatDate(iso: string | null): string {
    if (!iso) return '—';
    const [y, m, d] = iso.split('-');
    return `${d}/${m}/${y}`;
  }

  protected statusTexto(s: StatusValidade): string {
    return s === 'valido' ? 'Válido' : s === 'vencendo' ? 'Vencendo' : s === 'vencido' ? 'Vencido' : '—';
  }

  protected statusSev(s: StatusValidade): 'success' | 'warn' | 'danger' | 'secondary' {
    return s === 'valido' ? 'success' : s === 'vencendo' ? 'warn' : s === 'vencido' ? 'danger' : 'secondary';
  }

  ngOnInit(): void {
    this.carregar();
    this.certService.listar().subscribe({
      next: (certs) => this.certOptions.set(certs.map((c) => ({ label: c.nome, value: c.id }))),
      error: () => {},
    });
  }

  private carregar(): void {
    // Reseta expansões/detalhes para refletir eventuais mudanças de associação.
    this.expandedKeys.set({});
    this.detalhes.set({});
    this.service.listar().subscribe({
      next: (d) => this.lista.set(d),
      error: (err) => this.erro(err, 'Erro ao carregar pessoas.'),
    });
  }

  protected abrirNovo(): void {
    this.editandoId.set(null);
    this.fNome = ''; this.fEmail = ''; this.fTipo = 'interno';
    this.fSetor = ''; this.fEmpresa = ''; this.fTelefone = ''; this.fObs = '';
    this.fCertIds = [];
    this.dialog.set(true);
  }

  protected abrirEditar(p: Pessoa): void {
    this.editandoId.set(p.id);
    this.fNome = p.nome; this.fEmail = p.email ?? ''; this.fTipo = p.tipo;
    this.fSetor = p.setor ?? ''; this.fEmpresa = p.empresa_externa ?? '';
    this.fTelefone = p.telefone ?? ''; this.fObs = p.observacoes ?? '';
    this.fCertIds = [];
    this.dialog.set(true);
    // carrega os certificados já associados para pré-selecionar
    this.service.obter(p.id).subscribe({
      next: (det) => (this.fCertIds = det.certificados.map((c) => c.id)),
      error: () => {},
    });
  }

  protected salvar(): void {
    if (this.fNome.trim().length < 2) {
      this.messageService.add({ severity: 'warn', summary: 'Informe o nome (mín. 2 letras).' });
      return;
    }
    const payload: PessoaPayload = {
      nome: this.fNome.trim(),
      email: this.fEmail || null,
      tipo: this.fTipo,
      setor: this.fTipo === 'interno' ? this.fSetor || null : null,
      empresa_externa: this.fTipo === 'externo' ? this.fEmpresa || null : null,
      telefone: this.fTelefone || null,
      observacoes: this.fObs || null,
    };
    this.salvando.set(true);
    const id = this.editandoId();
    if (id) {
      forkJoin([
        this.service.atualizar(id, payload),
        this.service.definirCertificados(id, this.fCertIds),
      ]).subscribe({
        next: () => this.aposSalvar('Pessoa atualizada.'),
        error: (err) => this.erroSalvar(err),
      });
    } else {
      this.service.criar({ ...payload, certificado_ids: this.fCertIds }).subscribe({
        next: () => this.aposSalvar('Pessoa cadastrada.'),
        error: (err) => this.erroSalvar(err),
      });
    }
  }

  private aposSalvar(msg: string): void {
    this.salvando.set(false);
    this.dialog.set(false);
    this.messageService.add({ severity: 'success', summary: msg });
    this.carregar();
  }

  private erroSalvar(err: unknown): void {
    this.salvando.set(false);
    this.erro(err, 'Erro ao salvar pessoa.');
  }

  protected inativar(p: Pessoa): void {
    this.service.inativar(p.id).subscribe({
      next: () => { this.messageService.add({ severity: 'success', summary: 'Pessoa inativada.' }); this.carregar(); },
      error: (err) => this.erro(err, 'Erro ao inativar.'),
    });
  }

  private erro(err: unknown, fallback: string): void {
    const e = err as { error?: { detail?: unknown } };
    const detail = typeof e.error?.detail === 'string' ? e.error.detail : fallback;
    this.messageService.add({ severity: 'error', summary: 'Erro', detail });
  }
}
