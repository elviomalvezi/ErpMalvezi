import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { MessageModule } from 'primeng/message';
import { PasswordModule } from 'primeng/password';

import { AuthService } from '../../../core/services/auth.service';
import { EmpresaStore } from '../../../core/stores/empresa.store';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    CardModule,
    InputTextModule,
    PasswordModule,
    ButtonModule,
    MessageModule,
  ],
  template: `
    <div class="login-container">
      <p-card styleClass="login-card">
        <div class="login-brand">
          <span class="brand-icon pi pi-wallet"></span>
          <h1>App Financeiro</h1>
          <p>Entre com suas credenciais para acessar o sistema.</p>
        </div>

        <form [formGroup]="form" (ngSubmit)="onSubmit()" class="login-form">
          <div class="field">
            <label for="email">E-mail</label>
            <input
              id="email"
              type="email"
              pInputText
              formControlName="email"
              placeholder="seu@email.com"
              class="w-full"
              autocomplete="email"
            />
          </div>

          <div class="field">
            <label for="senha">Senha</label>
            <p-password
              inputId="senha"
              formControlName="senha"
              [feedback]="false"
              [toggleMask]="true"
              styleClass="w-full"
              inputStyleClass="w-full"
              placeholder="••••••••"
            />
          </div>

          @if (erro()) {
            <p-message severity="error" [text]="erro()!" styleClass="w-full" />
          }

          <p-button
            type="submit"
            label="Entrar"
            icon="pi pi-sign-in"
            [loading]="carregando()"
            [disabled]="form.invalid"
            styleClass="w-full mt-2"
          />
        </form>
      </p-card>
    </div>
  `,
  styles: [
    `
      .login-container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--p-surface-100);
        padding: 1rem;
      }
      :host ::ng-deep .login-card {
        width: 100%;
        max-width: 420px;
      }
      .login-brand {
        text-align: center;
        margin-bottom: 1.5rem;
      }
      .brand-icon {
        font-size: 2.5rem;
        color: var(--p-primary-color);
      }
      .login-brand h1 {
        margin: 0.5rem 0 0.25rem;
        font-size: 1.6rem;
        font-weight: 700;
      }
      .login-brand p {
        margin: 0;
        font-size: 0.875rem;
        color: var(--p-surface-500);
      }
      .login-form .field {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        margin-bottom: 1rem;
      }
      .login-form label {
        font-weight: 500;
        font-size: 0.875rem;
      }
    `,
  ],
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly empresaStore = inject(EmpresaStore);
  private readonly router = inject(Router);

  protected readonly carregando = signal(false);
  protected readonly erro = signal<string | null>(null);

  protected readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    senha: ['', Validators.required],
  });

  protected onSubmit(): void {
    if (this.form.invalid) return;

    const { email, senha } = this.form.getRawValue();
    this.carregando.set(true);
    this.erro.set(null);

    this.authService.login(email, senha).subscribe({
      next: () => {
        this.empresaStore.carregar();
        void this.router.navigate(['/dashboard']);
      },
      error: (err: Error) => {
        this.erro.set(err.message ?? 'Credenciais inválidas.');
        this.carregando.set(false);
      },
    });
  }
}
