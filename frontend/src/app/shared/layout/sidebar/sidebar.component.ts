import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

interface MenuItem {
  label: string;
  icon: string;
  route: string;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <nav class="app-sidebar">
      <ul class="menu-list">
        @for (item of menuItems; track item.route) {
          <li>
            <a
              [routerLink]="item.route"
              routerLinkActive="active"
              class="menu-item"
            >
              <i [class]="'pi ' + item.icon"></i>
              <span>{{ item.label }}</span>
            </a>
          </li>
        }
      </ul>
    </nav>
  `,
  styles: [`
    .app-sidebar {
      width: 220px;
      flex-shrink: 0;
      background: var(--p-surface-50);
      border-right: 1px solid var(--p-surface-200);
      padding: 1rem 0;
    }
    .menu-list {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .menu-item {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      padding: 0.65rem 1.25rem;
      color: var(--p-surface-700);
      text-decoration: none;
      font-size: 0.9rem;
      border-left: 3px solid transparent;
      transition: background 0.15s, border-color 0.15s;
    }
    .menu-item:hover {
      background: var(--p-surface-100);
    }
    .menu-item.active {
      border-left-color: var(--p-primary-color);
      background: var(--p-primary-50);
      color: var(--p-primary-color);
      font-weight: 600;
    }
    .pi { font-size: 1rem; }
  `],
})
export class SidebarComponent {
  protected readonly menuItems: MenuItem[] = [
    { label: 'Dashboard', icon: 'pi-home', route: '/dashboard' },
    { label: 'Contas a Pagar', icon: 'pi-arrow-circle-up', route: '/contas-pagar' },
    { label: 'Contas a Receber', icon: 'pi-arrow-circle-down', route: '/contas-receber' },
    { label: 'Transferências', icon: 'pi-arrows-h', route: '/transferencias' },
    { label: 'Conciliação', icon: 'pi-check-square', route: '/conciliacao' },
    { label: 'Fluxo de Caixa', icon: 'pi-chart-line', route: '/fluxo-caixa' },
    { label: 'Categorias', icon: 'pi-tags', route: '/categorias' },
    { label: 'Clientes/Fornec.', icon: 'pi-users', route: '/contatos' },
    { label: 'Contas/Cartões', icon: 'pi-credit-card', route: '/contas-bancarias' },
    { label: 'Patrimonial', icon: 'pi-building-columns', route: '/patrimonial' },
    { label: 'Empresas', icon: 'pi-building', route: '/empresas' },
    { label: 'Usuários', icon: 'pi-user-edit', route: '/usuarios' },
    { label: 'Configurações', icon: 'pi-cog', route: '/configuracoes' },
  ];
}
