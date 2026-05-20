import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { SelectModule } from 'primeng/select';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { TooltipModule } from 'primeng/tooltip';
import { FormsModule } from '@angular/forms';
import { EmpresaStore, Empresa } from '../../../core/stores/empresa.store';
import { AuthStore } from '../../../core/stores/auth.store';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [SelectModule, ButtonModule, AvatarModule, TooltipModule, FormsModule],
  template: `
    <header class="app-header">
      <div class="header-brand">
        <span class="brand-name">App Financeiro</span>
      </div>

      <div class="header-empresa">
        <p-select
          [options]="empresaStore.empresas()"
          [(ngModel)]="empresaSelecionada"
          optionLabel="nome"
          placeholder="Selecione a empresa"
          styleClass="empresa-select"
          (onChange)="onEmpresaChange($event.value)"
        >
          <ng-template pTemplate="selectedItem" let-empresa>
            @if (empresa) {
              <div class="empresa-item">
                <span class="empresa-tipo-badge" [class.pj]="empresa.tipo === 'PJ'">{{ empresa.tipo }}</span>
                <span>{{ empresa.nome }}</span>
              </div>
            }
          </ng-template>
          <ng-template pTemplate="item" let-empresa>
            <div class="empresa-item">
              <span class="empresa-tipo-badge" [class.pj]="empresa.tipo === 'PJ'">{{ empresa.tipo }}</span>
              <span>{{ empresa.nome }}</span>
            </div>
          </ng-template>
        </p-select>
      </div>

      <div class="header-actions">
        <p-avatar
          [label]="inicialNome()"
          shape="circle"
          class="cursor-pointer"
        />
        <p-button
          icon="pi pi-sign-out"
          [text]="true"
          severity="secondary"
          pTooltip="Sair"
          tooltipPosition="bottom"
          (onClick)="logout()"
        />
      </div>
    </header>
  `,
  styles: [`
    .app-header {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 0.75rem 1.5rem;
      background: var(--p-surface-0);
      border-bottom: 1px solid var(--p-surface-200);
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-brand {
      flex-shrink: 0;
    }
    .brand-name {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--p-primary-color);
    }
    .header-empresa {
      flex: 1;
      max-width: 380px;
    }
    .header-actions {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .empresa-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .empresa-tipo-badge {
      font-size: 0.65rem;
      font-weight: 700;
      padding: 0.1rem 0.35rem;
      border-radius: 4px;
      background: var(--p-orange-100);
      color: var(--p-orange-700);
    }
    .empresa-tipo-badge.pj {
      background: var(--p-blue-100);
      color: var(--p-blue-700);
    }
    :host ::ng-deep .empresa-select {
      min-width: 280px;
    }
  `],
})
export class HeaderComponent {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly authStore = inject(AuthStore);
  private readonly router = inject(Router);

  protected empresaSelecionada: Empresa | null = this.empresaStore.empresaAtiva();

  protected inicialNome(): string {
    const nome = this.authStore.nome();
    if (!nome) return 'U';
    const partes = nome.trim().split(' ');
    return partes.length >= 2
      ? (partes[0][0] + partes[partes.length - 1][0]).toUpperCase()
      : partes[0][0].toUpperCase();
  }

  protected onEmpresaChange(empresa: Empresa): void {
    this.empresaStore.selecionarEmpresa(empresa);
  }

  protected logout(): void {
    this.authStore.clearAuth();
    void this.router.navigate(['/login']);
  }
}
