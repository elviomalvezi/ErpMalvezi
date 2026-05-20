import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-patrimonial',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="patrimonial-shell">
      <div class="tab-bar">
        <a
          routerLink="/patrimonial/veiculos"
          routerLinkActive="tab-active"
          class="tab-item"
        >
          <i class="pi pi-car"></i>
          <span>Veículos</span>
        </a>
        <a
          routerLink="/patrimonial/imoveis"
          routerLinkActive="tab-active"
          class="tab-item"
        >
          <i class="pi pi-home"></i>
          <span>Imóveis</span>
        </a>
      </div>
      <div class="tab-content">
        <router-outlet />
      </div>
    </div>
  `,
  styles: [`
    .patrimonial-shell { display: flex; flex-direction: column; height: 100%; }
    .tab-bar {
      display: flex;
      gap: 0;
      border-bottom: 2px solid var(--p-surface-200);
      background: var(--p-surface-0);
      padding: 0 0.5rem;
    }
    .tab-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1.25rem;
      color: var(--p-surface-500);
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
      border-bottom: 2px solid transparent;
      margin-bottom: -2px;
      transition: color 0.15s, border-color 0.15s;
    }
    .tab-item:hover { color: var(--p-surface-700); }
    .tab-item.tab-active {
      color: var(--p-primary-color);
      border-bottom-color: var(--p-primary-color);
    }
    .tab-content { flex: 1; padding: 1.5rem; overflow: auto; }
  `],
})
export class PatrimonialComponent {}
