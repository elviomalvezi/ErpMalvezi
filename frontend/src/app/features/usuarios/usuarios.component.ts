import { Component, OnInit, inject, signal, computed, ChangeDetectorRef } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { MessageModule } from 'primeng/message';
import { TooltipModule } from 'primeng/tooltip';
import { PasswordModule } from 'primeng/password';
import { CheckboxModule } from 'primeng/checkbox';
import { DividerModule } from 'primeng/divider';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageService } from 'primeng/api';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { AuthStore } from '../../core/stores/auth.store';
import { UsuarioService, UsuarioCreate } from '../../core/services/usuario.service';
import { PermissaoService, MenuPermissao, AcaoPermissao, PermissaoItem } from '../../core/services/permissao.service';
import { EmpresaService } from '../../core/services/empresa.service';
import { UsuarioMe, EmpresaListItem } from '../../core/models';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  providers: [MessageService],
  imports: [
    ReactiveFormsModule, FormsModule,
    TableModule, ButtonModule, DialogModule, InputTextModule,
    TagModule, ToastModule, MessageModule, TooltipModule,
    PasswordModule, CheckboxModule, DividerModule, ProgressSpinnerModule,
  ],
  template: `
    <p-toast />

    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title"><i class="pi pi-user-edit"></i> Usuários</h1>
          <p class="page-subtitle">Gerencie os usuários e suas permissões de acesso</p>
        </div>
        <p-button label="Novo Usuário" icon="pi pi-plus" (onClick)="abrirNovo()" />
      </div>

      <p-table [value]="lista()" [loading]="carregando()" [rowHover]="true"
               class="p-datatable-sm" [tableStyle]="{ 'min-width': '640px' }">
        <ng-template pTemplate="header">
          <tr>
            <th style="width:220px">Nome</th>
            <th>E-mail</th>
            <th style="width:100px;text-align:center">Perfil</th>
            <th style="width:90px;text-align:center">Status</th>
            <th style="width:200px;text-align:center">Ações</th>
          </tr>
        </ng-template>

        <ng-template pTemplate="body" let-u>
          <tr [class.row-inativo]="!u.ativo">
            <td>
              <div class="usuario-cell">
                <div class="usuario-avatar" [class.admin]="u.admin" [class.gestor]="u.gestor && !u.admin">
                  {{ inicialUsuario(u.nome) }}
                </div>
                <div class="usuario-info">
                  <span class="usuario-nome">{{ u.nome }}</span>
                  @if (u.id === authStore.userId()) {
                    <span class="voce-badge">você</span>
                  }
                </div>
              </div>
            </td>
            <td class="email-cell">{{ u.email }}</td>
            <td style="text-align:center">
              @if (u.admin) {
                <span class="perfil-badge admin">Admin</span>
              } @else if (u.gestor) {
                <span class="perfil-badge gestor">Gestor</span>
              } @else {
                <span class="perfil-badge usuario">Usuário</span>
              }
            </td>
            <td style="text-align:center">
              <span class="status-dot" [class.ativo]="u.ativo"></span>
              <span class="status-label">{{ u.ativo ? 'Ativo' : 'Inativo' }}</span>
            </td>
            <td>
              <div class="acoes">
                @if (!u.admin) {
                  <p-button icon="pi pi-shield" [text]="true" size="small"
                    pTooltip="Permissões de telas" tooltipPosition="top"
                    (onClick)="abrirPermissoes(u)" />
                  <p-button icon="pi pi-building" [text]="true" size="small"
                    pTooltip="Acesso a empresas" tooltipPosition="top"
                    (onClick)="abrirEmpresasAccess(u)" />
                  @if (authStore.admin()) {
                    <p-button
                      [icon]="u.gestor ? 'pi pi-user-minus' : 'pi pi-user-plus'"
                      [severity]="u.gestor ? 'warn' : 'secondary'"
                      [text]="true" size="small"
                      [pTooltip]="u.gestor ? 'Remover perfil Gestor' : 'Promover a Gestor'"
                      tooltipPosition="top"
                      (onClick)="toggleGestor(u)"
                    />
                  }
                  <span class="acoes-sep"></span>
                }
                @if (u.id !== authStore.userId()) {
                  <p-button
                    [icon]="u.ativo ? 'pi pi-ban' : 'pi pi-check-circle'"
                    [severity]="u.ativo ? 'danger' : 'success'"
                    [text]="true" size="small"
                    (onClick)="toggleAtivo(u)"
                    [pTooltip]="u.ativo ? 'Inativar' : 'Reativar'"
                    tooltipPosition="top" />
                }
              </div>
            </td>
          </tr>
        </ng-template>

        <ng-template pTemplate="emptymessage">
          <tr><td colspan="5" class="empty-msg">Nenhum usuário encontrado.</td></tr>
        </ng-template>
      </p-table>
    </div>

    <!-- Dialog: Novo Usuário -->
    <p-dialog header="Novo Usuário"
      [visible]="dialogVisivel()"
      (visibleChange)="$event ? null : fecharDialog()"
      [modal]="true" [style]="{ width: '440px', 'max-width': '95vw' }"
      [draggable]="true" [resizable]="false">
      <form [formGroup]="form" class="dialog-form">
        <div class="field">
          <label>Nome completo *</label>
          <input pInputText formControlName="nome" placeholder="Nome do usuário" [style]="{ width: '100%' }" />
        </div>
        <div class="field">
          <label>E-mail *</label>
          <input pInputText formControlName="email" type="email" placeholder="usuario@email.com" [style]="{ width: '100%' }" />
        </div>
        <div class="field">
          <label>Senha inicial *</label>
          <p-password formControlName="senha" placeholder="Mínimo 8 caracteres"
            [feedback]="false" [toggleMask]="true"
            [style]="{ width: '100%' }" [inputStyle]="{ width: '100%' }" />
        </div>
        @if (authStore.admin()) {
          <div class="field-check">
            <p-checkbox formControlName="gestor" [binary]="true" inputId="gestor" />
            <label for="gestor">
              <strong>Gestor</strong>
              <small> — pode criar usuários e configurar permissões, sem acesso de Admin</small>
            </label>
          </div>
        }
      </form>
      <ng-template pTemplate="footer">
        @if (formErro()) { <p-message severity="error">{{ formErro() }}</p-message> }
        <div class="footer-acoes">
          <p-button label="Cancelar" severity="secondary" (onClick)="fecharDialog()" />
          <p-button label="Criar" icon="pi pi-check" (onClick)="salvar()" [loading]="salvando()" />
        </div>
      </ng-template>
    </p-dialog>

    <!-- Dialog: Permissões -->
    <p-dialog
      [header]="'Permissões — ' + (usuarioPermissao()?.nome ?? '')"
      [visible]="dialogPermissoes()"
      (visibleChange)="$event ? null : fecharPermissoes()"
      [modal]="true" [style]="{ width: '720px', 'max-width': '95vw' }"
      [draggable]="true" [resizable]="false">

      @if (carregandoPermissoes()) {
        <div class="spinner-center"><p-progress-spinner strokeWidth="4" [style]="{ width: '40px' }" /></div>
      } @else {
        <p class="perm-info">
          <i class="pi pi-info-circle"></i>
          Selecione quais rotinas o usuário pode acessar. Administradores têm acesso total.
        </p>

        <div class="perm-table-wrap">
          <table class="perm-table">
            <thead>
              <tr>
                <th class="th-menu">Módulo / Rotina</th>
                @for (acao of acoes(); track acao.chave) {
                  <th class="th-acao">{{ acao.nome }}</th>
                }
                <th class="th-acao">Todos</th>
              </tr>
            </thead>
            <tbody>
              @for (menu of menus(); track menu.chave) {
                <tr>
                  <td class="td-menu">{{ menu.nome }}</td>
                  @for (acao of acoes(); track acao.chave) {
                    <td class="td-check">
                      <p-checkbox
                        [binary]="true"
                        [(ngModel)]="matriz[menu.chave + '|' + acao.chave]"
                      />
                    </td>
                  }
                  <td class="td-check">
                    <p-checkbox
                      [binary]="true"
                      [ngModel]="todosMenuSelecionado(menu.chave)"
                      (ngModelChange)="toggleTodosMenu(menu.chave, $event)"
                    />
                  </td>
                </tr>
              }
            </tbody>
            <tfoot>
              <tr>
                <td class="td-menu td-footer"><strong>Selecionar coluna</strong></td>
                @for (acao of acoes(); track acao.chave) {
                  <td class="td-check td-footer">
                    <p-checkbox
                      [binary]="true"
                      [ngModel]="todosAcaoSelecionado(acao.chave)"
                      (ngModelChange)="toggleTodosAcao(acao.chave, $event)"
                    />
                  </td>
                }
                <td class="td-check td-footer">
                  <p-checkbox [binary]="true"
                    [ngModel]="todosSelecionado()"
                    (ngModelChange)="toggleTodos($event)" />
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      }

      <ng-template pTemplate="footer">
        <p-button label="Cancelar" severity="secondary" (onClick)="fecharPermissoes()" />
        <p-button label="Salvar Permissões" icon="pi pi-shield"
          (onClick)="salvarPermissoes()" [loading]="salvandoPermissoes()" />
      </ng-template>
    </p-dialog>

    <!-- Dialog: Acesso a Empresas -->
    <p-dialog
      [header]="'Acesso a Empresas — ' + (usuarioPermissao()?.nome ?? '')"
      [visible]="dialogEmpresas()"
      (visibleChange)="$event ? null : dialogEmpresas.set(false)"
      [modal]="true" [style]="{ width: '480px' }"
      [draggable]="true" [resizable]="false">

      <p class="perm-info">
        <i class="pi pi-info-circle"></i>
        Selecione quais empresas este usuário pode acessar. Administradores acessam todas.
      </p>
      @if (carregandoEmpresas()) {
        <div class="spinner-center"><p-progress-spinner strokeWidth="4" [style]="{ width: '40px' }" /></div>
      } @else {
        <div class="empresa-lista">
          @for (emp of todasEmpresas(); track emp.id) {
            <div class="empresa-linha">
              <p-checkbox [binary]="true" [(ngModel)]="empresasAccess[emp.id]" />
              <div class="empresa-info">
                <span class="empresa-tipo-badge" [class.pj]="emp.tipo === 'PJ'">{{ emp.tipo }}</span>
                <span>{{ emp.nome_principal }}</span>
              </div>
            </div>
          }
        </div>
      }

      <ng-template pTemplate="footer">
        <p-button label="Cancelar" severity="secondary" (onClick)="dialogEmpresas.set(false)" />
        <p-button label="Salvar Acesso" icon="pi pi-building"
          (onClick)="salvarEmpresasAccess()" [loading]="salvandoEmpresas()" />
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .page { max-width: 1100px; }
    .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
    .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; }
    .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.875rem; }
    .email-cell { font-size: 0.875rem; color: var(--p-surface-500); }
    :host ::ng-deep .row-inativo td { opacity: 0.45; }
    .empty-msg { text-align: center; color: var(--p-surface-400); padding: 2.5rem 1rem; font-size: 0.9rem; }
    .dialog-form { display: flex; flex-direction: column; gap: 1rem; padding: 0.25rem 0; }
    .field { display: flex; flex-direction: column; gap: 0.3rem; }
    .field label { font-size: 0.8rem; font-weight: 600; }
    .footer-acoes { display: flex; justify-content: flex-end; gap: 0.5rem; }

    /* Célula nome com avatar */
    .usuario-cell { display: flex; align-items: center; gap: 0.6rem; }
    .usuario-avatar {
      width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center;
      font-size: 0.7rem; font-weight: 700; letter-spacing: 0.02em;
      background: var(--p-surface-200); color: var(--p-surface-600);
    }
    .usuario-avatar.admin { background: #fef3c7; color: #92400e; }
    .usuario-avatar.gestor { background: #dbeafe; color: #1e40af; }
    .usuario-info { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
    .usuario-nome { font-weight: 500; font-size: 0.875rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .voce-badge {
      font-size: 0.65rem; font-weight: 600; color: var(--p-primary-color);
      background: var(--p-primary-50, #eef2ff); border-radius: 3px;
      padding: 0.05rem 0.3rem; align-self: flex-start;
    }

    /* Perfil badge */
    .perfil-badge {
      display: inline-block; font-size: 0.7rem; font-weight: 700;
      padding: 0.2rem 0.55rem; border-radius: 4px; letter-spacing: 0.02em;
    }
    .perfil-badge.admin { background: #fef3c7; color: #92400e; }
    .perfil-badge.gestor { background: #dbeafe; color: #1e40af; }
    .perfil-badge.usuario { background: var(--p-surface-100); color: var(--p-surface-600); }

    /* Status */
    .status-dot {
      display: inline-block; width: 7px; height: 7px; border-radius: 50%;
      background: var(--p-red-400); margin-right: 0.35rem; vertical-align: middle;
    }
    .status-dot.ativo { background: var(--p-green-500); }
    .status-label { font-size: 0.8rem; color: var(--p-surface-600); vertical-align: middle; }

    /* Ações */
    .acoes {
      display: flex; align-items: center; gap: 2px;
      flex-wrap: nowrap; justify-content: center;
    }
    .acoes-sep {
      width: 1px; height: 18px; background: var(--p-surface-200);
      margin: 0 4px; flex-shrink: 0;
    }

    .spinner-center { display: flex; justify-content: center; padding: 2rem; }
    .perm-info { color: var(--p-surface-500); font-size: 0.85rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.4rem; }

    .perm-table-wrap { overflow-x: auto; }
    .perm-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    .perm-table thead { background: var(--p-surface-100); }
    .th-menu { text-align: left; padding: 0.6rem 1rem; font-weight: 600; min-width: 180px; }
    .th-acao { text-align: center; padding: 0.6rem 0.5rem; font-weight: 600; min-width: 70px; color: var(--p-surface-600); }
    .td-menu { padding: 0.5rem 1rem; border-bottom: 1px solid var(--p-surface-100); }
    .td-check { text-align: center; padding: 0.5rem; border-bottom: 1px solid var(--p-surface-100); }
    .td-footer { background: var(--p-surface-50); font-size: 0.8rem; }
    .perm-table tbody tr:hover { background: var(--p-surface-50); }
    .empresa-lista { display: flex; flex-direction: column; gap: 0.5rem; }
    .empresa-linha { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; border-radius: 6px; }
    .empresa-linha:hover { background: var(--p-surface-50); }
    .empresa-info { display: flex; align-items: center; gap: 0.5rem; }
    .empresa-tipo-badge { font-size: 0.65rem; font-weight: 700; padding: 0.1rem 0.35rem; border-radius: 4px; background: var(--p-orange-100); color: var(--p-orange-700); }
    .empresa-tipo-badge.pj { background: var(--p-blue-100); color: var(--p-blue-700); }
    .field-check { display: flex; align-items: flex-start; gap: 0.6rem; padding: 0.5rem 0; }
    .field-check label { cursor: pointer; font-size: 0.875rem; }
    .field-check small { color: var(--p-surface-500); }
  `],
})
export class UsuariosComponent implements OnInit {
  protected readonly authStore = inject(AuthStore);
  private readonly usuarioService = inject(UsuarioService);
  private readonly permissaoService = inject(PermissaoService);
  private readonly messageService = inject(MessageService);
  private readonly fb = inject(FormBuilder);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly empresaService = inject(EmpresaService);

  protected readonly lista = signal<UsuarioMe[]>([]);
  protected readonly carregando = signal(false);
  protected readonly dialogVisivel = signal(false);
  protected readonly salvando = signal(false);
  protected readonly formErro = signal<string | null>(null);

  // Permissões
  protected readonly dialogPermissoes = signal(false);
  protected readonly carregandoPermissoes = signal(false);
  protected readonly salvandoPermissoes = signal(false);
  protected readonly usuarioPermissao = signal<UsuarioMe | null>(null);
  protected readonly menus = signal<MenuPermissao[]>([]);
  protected readonly acoes = signal<AcaoPermissao[]>([]);
  protected matriz: Record<string, boolean> = {};

  protected readonly form = this.fb.group({
    nome: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    senha: ['', [Validators.required, Validators.minLength(8)]],
    gestor: [false],
  });

  protected inicialUsuario(nome: string): string {
    const partes = (nome ?? '').trim().split(' ').filter(Boolean);
    if (partes.length >= 2) return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
    return partes[0]?.[0]?.toUpperCase() ?? '?';
  }

  ngOnInit(): void { this.carregar(); }

  private carregar(): void {
    this.carregando.set(true);
    this.usuarioService.listar().subscribe({
      next: (data) => { this.lista.set(data); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  protected abrirNovo(): void {
    this.formErro.set(null);
    this.form.reset();
    this.dialogVisivel.set(true);
  }

  protected fecharDialog(): void {
    this.dialogVisivel.set(false);
    this.formErro.set(null);
  }

  protected salvar(): void {
    this.formErro.set(null);
    if (this.form.invalid) { this.form.markAllAsTouched(); this.formErro.set('Preencha todos os campos.'); return; }
    const v = this.form.getRawValue();
    const payload: UsuarioCreate = { nome: v.nome!, email: v.email!, senha: v.senha!, gestor: v.gestor ?? false };
    this.salvando.set(true);
    this.usuarioService.criar(payload).subscribe({
      next: () => {
        this.dialogVisivel.set(false); this.salvando.set(false); this.carregar();
        this.messageService.add({ severity: 'success', summary: 'Usuário criado com sucesso.' });
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Verifique os dados.';
        this.formErro.set(detail); this.salvando.set(false);
      },
    });
  }

  protected toggleAtivo(u: UsuarioMe): void {
    const obs = u.ativo ? this.usuarioService.inativar(u.id) : this.usuarioService.reativar(u.id);
    obs.subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: `Usuário ${u.ativo ? 'inativado' : 'reativado'}.` });
        this.carregar();
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Erro ao alterar status.';
        this.messageService.add({ severity: 'error', summary: detail });
      },
    });
  }

  // ── Permissões ────────────────────────────────────────────────────────────

  protected abrirPermissoes(u: UsuarioMe): void {
    this.usuarioPermissao.set(u);
    this.dialogPermissoes.set(true);
    this.carregandoPermissoes.set(true);
    this.matriz = {};

    forkJoin({
      menus: this.permissaoService.listarMenus(),
      acoes: this.permissaoService.listarAcoes(),
      permissoes: this.permissaoService.listarPermissoesUsuario(u.id),
    }).subscribe({
      next: ({ menus, acoes, permissoes }) => {
        this.menus.set(menus.sort((a, b) => a.ordem - b.ordem));
        this.acoes.set(acoes);
        // Cria novo objeto para forçar detecção de mudanças
        const novaMatriz: Record<string, boolean> = {};
        menus.forEach(m => acoes.forEach(a => { novaMatriz[m.chave + '|' + a.chave] = false; }));
        permissoes.permissoes.forEach(p => { novaMatriz[p.menu_chave + '|' + p.acao_chave] = true; });
        this.matriz = novaMatriz;
        this.carregandoPermissoes.set(false);
        this.cdr.detectChanges();
      },
      error: () => { this.carregandoPermissoes.set(false); this.dialogPermissoes.set(false); },
    });
  }

  protected fecharPermissoes(): void {
    this.dialogPermissoes.set(false);
    this.usuarioPermissao.set(null);
  }

  protected todosMenuSelecionado(menuChave: string): boolean {
    return this.acoes().every(a => this.matriz[menuChave + '|' + a.chave]);
  }

  protected todosAcaoSelecionado(acaoChave: string): boolean {
    return this.menus().every(m => this.matriz[m.chave + '|' + acaoChave]);
  }

  protected todosSelecionado(): boolean {
    return this.menus().every(m => this.acoes().every(a => this.matriz[m.chave + '|' + a.chave]));
  }

  protected toggleTodosMenu(menuChave: string, valor: boolean): void {
    const m = { ...this.matriz };
    this.acoes().forEach(a => { m[menuChave + '|' + a.chave] = valor; });
    this.matriz = m;
    this.cdr.detectChanges();
  }

  protected toggleTodosAcao(acaoChave: string, valor: boolean): void {
    const m = { ...this.matriz };
    this.menus().forEach(mn => { m[mn.chave + '|' + acaoChave] = valor; });
    this.matriz = m;
    this.cdr.detectChanges();
  }

  protected toggleTodos(valor: boolean): void {
    const m = { ...this.matriz };
    this.menus().forEach(mn => this.acoes().forEach(a => { m[mn.chave + '|' + a.chave] = valor; }));
    this.matriz = m;
    this.cdr.detectChanges();
  }

  // ── Acesso a Empresas ────────────────────────────────────────────────────

  protected dialogEmpresas = signal(false);
  protected carregandoEmpresas = signal(false);
  protected salvandoEmpresas = signal(false);
  protected todasEmpresas = signal<EmpresaListItem[]>([]);
  protected empresasAccess: Record<string, boolean> = {};

  protected toggleGestor(u: UsuarioMe): void {
    this.usuarioService.toggleGestor(u.id).subscribe({
      next: (updated) => {
        const msg = updated.gestor ? 'Usuário promovido a Gestor.' : 'Perfil Gestor removido.';
        this.messageService.add({ severity: 'success', summary: msg });
        this.carregar();
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Erro ao alterar perfil.';
        this.messageService.add({ severity: 'error', summary: detail });
      },
    });
  }

  protected abrirEmpresasAccess(u: UsuarioMe): void {
    this.usuarioPermissao.set(u);
    this.empresasAccess = {};
    this.dialogEmpresas.set(true);
    this.carregandoEmpresas.set(true);

    forkJoin({
      empresas: this.empresaService.listar(),
      acesso: this.empresaService.listarEmpresasUsuario(u.id),
    }).subscribe({
      next: ({ empresas, acesso }) => {
        this.todasEmpresas.set(empresas);
        const acessoSet = new Set(acesso);
        const novo: Record<string, boolean> = {};
        empresas.forEach(e => { novo[e.id] = acessoSet.has(e.id); });
        this.empresasAccess = novo;
        this.carregandoEmpresas.set(false);
        this.cdr.detectChanges();
      },
      error: () => { this.carregandoEmpresas.set(false); this.dialogEmpresas.set(false); },
    });
  }

  protected salvarEmpresasAccess(): void {
    const u = this.usuarioPermissao();
    if (!u) return;
    const ids = Object.entries(this.empresasAccess).filter(([, v]) => v).map(([k]) => k);
    this.salvandoEmpresas.set(true);
    this.empresaService.definirEmpresasUsuario(u.id, ids).subscribe({
      next: () => {
        this.salvandoEmpresas.set(false);
        this.dialogEmpresas.set(false);
        this.messageService.add({ severity: 'success', summary: 'Acesso a empresas salvo.' });
      },
      error: () => {
        this.salvandoEmpresas.set(false);
        this.messageService.add({ severity: 'error', summary: 'Erro ao salvar acesso.' });
      },
    });
  }

  protected salvarPermissoes(): void {
    const usuario = this.usuarioPermissao();
    if (!usuario) return;

    const permissoes: PermissaoItem[] = [];
    this.menus().forEach(m => this.acoes().forEach(a => {
      if (this.matriz[m.chave + '|' + a.chave]) permissoes.push({ menu_chave: m.chave, acao_chave: a.chave });
    }));

    this.salvandoPermissoes.set(true);
    this.permissaoService.substituirPermissoes(usuario.id, permissoes).subscribe({
      next: () => {
        this.salvandoPermissoes.set(false);
        this.fecharPermissoes();
        this.messageService.add({ severity: 'success', summary: 'Permissões salvas com sucesso.' });
      },
      error: () => {
        this.salvandoPermissoes.set(false);
        this.messageService.add({ severity: 'error', summary: 'Erro ao salvar permissões.' });
      },
    });
  }
}
