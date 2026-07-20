import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { MessageModule } from 'primeng/message';
import { PasswordModule } from 'primeng/password';
import { SelectModule } from 'primeng/select';

import { AuthService } from '../../../core/services/auth.service';
import { EmpresaService } from '../../../core/services/empresa.service';
import { Empresa, EmpresaStore } from '../../../core/stores/empresa.store';

function toEmpresa(e: { id: string; nome_principal: string; nome_alternativo?: string | null; tipo: 'PJ' | 'PF'; documento?: string | null }): Empresa {
  return {
    id: e.id,
    nome: e.nome_alternativo ?? e.nome_principal,
    tipo: e.tipo,
    documento: e.documento ?? null,
  };
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    FormsModule,
    CardModule,
    InputTextModule,
    PasswordModule,
    ButtonModule,
    MessageModule,
    SelectModule,
  ],
  template: `
    <div class="login-container">
      <p-card styleClass="login-card">
        <div class="login-brand">
          <span class="brand-icon pi pi-wallet"></span>
          <h1>App Financeiro</h1>
          @if (etapa() === 'credenciais') {
            <p>Entre com suas credenciais para acessar o sistema.</p>
          } @else {
            <p>Selecione a empresa para continuar.</p>
          }
        </div>

        @if (etapa() === 'credenciais') {
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
        }

        @if (etapa() === 'empresa') {
          <div class="empresa-select">
            <p-select
              [options]="empresas()"
              [(ngModel)]="empresaEscolhida"
              optionLabel="nome"
              [filter]="true"
              filterBy="nome"
              placeholder="Selecione a empresa"
              styleClass="w-full"
              appendTo="body"
            >
              <ng-template let-emp pTemplate="selectedItem">
                @if (emp) {
                  <div class="emp-opt">
                    <span class="emp-badge" [class.pj]="emp.tipo === 'PJ'" [class.pf]="emp.tipo === 'PF'">{{ emp.tipo }}</span>
                    <span class="emp-nome">{{ emp.nome }}</span>
                  </div>
                }
              </ng-template>
              <ng-template let-emp pTemplate="item">
                <div class="emp-opt">
                  <span class="emp-badge" [class.pj]="emp.tipo === 'PJ'" [class.pf]="emp.tipo === 'PF'">{{ emp.tipo }}</span>
                  <span class="emp-nome">{{ emp.nome }}</span>
                </div>
              </ng-template>
            </p-select>

            <p-button
              label="Continuar"
              icon="pi pi-arrow-right"
              iconPos="right"
              [disabled]="!empresaEscolhida"
              styleClass="empresa-btn mt-3"
              (onClick)="confirmarEmpresa()"
            />

            <p-button
              label="Voltar"
              icon="pi pi-arrow-left"
              [text]="true"
              styleClass="empresa-btn-voltar mt-2"
              (onClick)="voltar()"
            />
          </div>
        }
      </p-card>
    </div>
  `,
  styles: [`
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
    .empresa-select {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    /* Botão principal centralizado e com sombra para se destacar. */
    :host ::ng-deep .empresa-btn {
      min-width: 12rem;
      justify-content: center;
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
      transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    :host ::ng-deep .empresa-btn:not(:disabled):hover {
      box-shadow: 0 6px 18px rgba(16, 185, 129, 0.45);
      transform: translateY(-1px);
    }
    :host ::ng-deep .empresa-btn:disabled {
      box-shadow: none;
    }
    /* Botão secundário (Voltar) também centralizado. */
    :host ::ng-deep .empresa-btn-voltar {
      justify-content: center;
    }
    .emp-opt {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .emp-badge {
      font-size: 0.65rem;
      font-weight: 700;
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      flex-shrink: 0;
    }
    .emp-badge.pj { background: var(--p-blue-100); color: var(--p-blue-700); }
    .emp-badge.pf { background: var(--p-green-100); color: var(--p-green-700); }
    .emp-nome {
      font-weight: 500;
      font-size: 0.95rem;
    }
  `],
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly empresaService = inject(EmpresaService);
  private readonly empresaStore = inject(EmpresaStore);

  protected readonly etapa = signal<'credenciais' | 'empresa'>('credenciais');
  protected readonly carregando = signal(false);
  protected readonly erro = signal<string | null>(null);
  protected readonly empresas = signal<Empresa[]>([]);
  protected empresaEscolhida: Empresa | null = null;

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
        this.empresaService.listar().subscribe({
          next: lista => {
            const empresas = lista.map(toEmpresa);
            this.empresaStore.popular(empresas);
            this.carregando.set(false);

            if (empresas.length === 1) {
              this.empresaStore.selecionarEmpresa(empresas[0]);
            } else {
              this.empresas.set(empresas);
              this.etapa.set('empresa');
            }
          },
          error: () => {
            this.carregando.set(false);
            this.etapa.set('empresa');
          },
        });
      },
      error: (err: Error) => {
        this.erro.set(err.message ?? 'Credenciais inválidas.');
        this.carregando.set(false);
      },
    });
  }

  protected selecionarEmpresa(empresa: Empresa): void {
    this.empresaStore.selecionarEmpresa(empresa);
  }

  protected confirmarEmpresa(): void {
    if (this.empresaEscolhida) {
      this.selecionarEmpresa(this.empresaEscolhida);
    }
  }

  protected voltar(): void {
    this.etapa.set('credenciais');
    this.empresas.set([]);
    this.empresaEscolhida = null;
  }
}
