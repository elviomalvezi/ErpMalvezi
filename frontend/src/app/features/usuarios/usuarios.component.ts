import { Component, OnInit, inject, signal } from '@angular/core';
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
import { MessageService } from 'primeng/api';

import { AuthStore } from '../../core/stores/auth.store';
import { UsuarioService, UsuarioCreate } from '../../core/services/usuario.service';
import { UsuarioMe } from '../../core/models';

@Component({
  selector: 'app-usuarios',
  standalone: true,
  providers: [MessageService],
  imports: [
    ReactiveFormsModule,
    TableModule,
    ButtonModule,
    DialogModule,
    InputTextModule,
    TagModule,
    ToastModule,
    MessageModule,
    TooltipModule,
    PasswordModule,
  ],
  template: `
    <p-toast />

    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Usuários</h1>
          <p class="page-subtitle">Gerencie os usuários com acesso ao sistema</p>
        </div>
        <p-button label="Novo Usuário" icon="pi pi-plus" (onClick)="abrirNovo()" />
      </div>

      <p-table
        [value]="lista()"
        [loading]="carregando()"
        [rowHover]="true"
        class="p-datatable-sm"
        [tableStyle]="{ 'min-width': '500px' }"
      >
        <ng-template pTemplate="header">
          <tr>
            <th>Nome</th>
            <th>E-mail</th>
            <th style="width:90px">Perfil</th>
            <th style="width:90px">Status</th>
            <th style="width:80px">Ações</th>
          </tr>
        </ng-template>

        <ng-template pTemplate="body" let-u>
          <tr [class.row-inativo]="!u.ativo">
            <td>
              <span class="usuario-nome">{{ u.nome }}</span>
              @if (u.id === authStore.userId()) {
                <span class="voce-badge"> (você)</span>
              }
            </td>
            <td class="email-cell">{{ u.email }}</td>
            <td>
              <p-tag
                [value]="u.admin ? 'Admin' : 'Usuário'"
                [severity]="u.admin ? 'warn' : 'secondary'"
              />
            </td>
            <td>
              <p-tag
                [value]="u.ativo ? 'Ativo' : 'Inativo'"
                [severity]="u.ativo ? 'success' : 'danger'"
              />
            </td>
            <td>
              @if (u.id !== authStore.userId()) {
                <p-button
                  [icon]="u.ativo ? 'pi pi-ban' : 'pi pi-check-circle'"
                  [severity]="u.ativo ? 'danger' : 'success'"
                  [text]="true"
                  size="small"
                  (onClick)="toggleAtivo(u)"
                  [pTooltip]="u.ativo ? 'Inativar' : 'Reativar'"
                  tooltipPosition="top"
                />
              }
            </td>
          </tr>
        </ng-template>

        <ng-template pTemplate="emptymessage">
          <tr>
            <td colspan="5" class="empty-msg">Nenhum usuário encontrado.</td>
          </tr>
        </ng-template>
      </p-table>
    </div>

    <p-dialog
      header="Novo Usuário"
      [visible]="dialogVisivel()"
      (visibleChange)="$event ? dialogVisivel.set(true) : fecharDialog()"
      [modal]="true"
      [style]="{ width: '440px', 'max-width': '95vw' }"
      [draggable]="false"
      [resizable]="false"
    >
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
          <p-password
            formControlName="senha"
            placeholder="Mínimo 8 caracteres"
            [feedback]="false"
            [toggleMask]="true"
            [style]="{ width: '100%' }"
            [inputStyle]="{ width: '100%' }"
          />
        </div>
      </form>

      <ng-template pTemplate="footer">
        @if (formErro()) {
          <p-message severity="error">{{ formErro() }}</p-message>
        }
        <div class="footer-acoes">
          <p-button label="Cancelar" severity="secondary" (onClick)="fecharDialog()" />
          <p-button label="Criar" icon="pi pi-check" (onClick)="salvar()" [loading]="salvando()" />
        </div>
      </ng-template>
    </p-dialog>
  `,
  styles: [`
    .page { max-width: 900px; }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1.5rem;
    }
    .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; }
    .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.875rem; }

    .email-cell { font-size: 0.875rem; color: var(--p-surface-600); }
    .usuario-nome { font-weight: 500; }
    .voce-badge { font-size: 0.75rem; color: var(--p-surface-400); }

    :host ::ng-deep .row-inativo td { opacity: 0.5; }

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
  `],
})
export class UsuariosComponent implements OnInit {
  protected readonly authStore = inject(AuthStore);
  private readonly usuarioService = inject(UsuarioService);
  private readonly messageService = inject(MessageService);
  private readonly fb = inject(FormBuilder);

  protected readonly lista = signal<UsuarioMe[]>([]);
  protected readonly carregando = signal(false);
  protected readonly dialogVisivel = signal(false);
  protected readonly salvando = signal(false);
  protected readonly formErro = signal<string | null>(null);

  protected readonly form = this.fb.group({
    nome: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    senha: ['', [Validators.required, Validators.minLength(8)]],
  });

  ngOnInit(): void {
    this.carregar();
  }

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
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.formErro.set('Preencha todos os campos obrigatórios.');
      return;
    }
    const v = this.form.getRawValue();
    const payload: UsuarioCreate = {
      nome: v.nome!,
      email: v.email!,
      senha: v.senha!,
    };
    this.salvando.set(true);
    this.usuarioService.criar(payload).subscribe({
      next: () => {
        this.dialogVisivel.set(false);
        this.formErro.set(null);
        this.salvando.set(false);
        this.carregar();
        this.messageService.add({ severity: 'success', summary: 'Sucesso', detail: 'Usuário criado com sucesso.' });
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Verifique os dados e tente novamente.';
        this.formErro.set(detail);
        this.salvando.set(false);
      },
    });
  }

  protected toggleAtivo(u: UsuarioMe): void {
    const obs = u.ativo ? this.usuarioService.inativar(u.id) : this.usuarioService.reativar(u.id);
    obs.subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Sucesso',
          detail: `Usuário ${u.ativo ? 'inativado' : 'reativado'} com sucesso.`,
        });
        this.carregar();
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Erro ao alterar status.';
        this.messageService.add({ severity: 'error', summary: 'Erro', detail });
      },
    });
  }
}
