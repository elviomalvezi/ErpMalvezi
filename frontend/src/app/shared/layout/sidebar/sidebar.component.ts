import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { TooltipModule } from 'primeng/tooltip';
import { AuthStore } from '../../../core/stores/auth.store';
import { CertificadoService } from '../../../core/services/certificado.service';

interface MenuItem {
  label: string;
  icon: string;
  route: string;
  color: string;
  apenasAdmin?: boolean;
  tambemGestor?: boolean;
}

interface MenuGroup {
  grupo: string;
  items: MenuItem[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, TooltipModule],
  template: `
    <nav class="app-sidebar" [class.collapsed]="collapsed()">

      <!-- Botão recolher/expandir -->
      <button class="toggle-btn" (click)="collapsed.set(!collapsed())"
        [title]="collapsed() ? 'Expandir menu' : 'Recolher menu'">
        <i [class]="'pi ' + (collapsed() ? 'pi-chevron-right' : 'pi-chevron-left')"></i>
      </button>

      @for (grupo of menuGroups; track grupo.grupo) {
        <div class="menu-group">
          @if (!collapsed()) {
            <span class="menu-group-label">{{ grupo.grupo }}</span>
          } @else {
            <div class="menu-group-divider"></div>
          }
          <ul class="menu-list">
            @for (item of grupo.items; track item.route) {
              @if (!item.apenasAdmin || authStore.admin() || (item.tambemGestor && authStore.gestor())) {
                <li>
                  <a [routerLink]="item.route" routerLinkActive="active" class="menu-item"
                    [pTooltip]="collapsed() ? item.label : ''"
                    tooltipPosition="right">
                    <i [class]="'pi ' + item.icon" [style.color]="item.color"></i>
                    @if (!collapsed()) {
                      <span>{{ item.label }}</span>
                    }
                    @if (item.route === '/certificados' && certAlertas() > 0) {
                      <span class="menu-badge" [class.danger]="certVencidos() > 0"
                        [pTooltip]="certVencidos() > 0 ? certVencidos() + ' vencido(s), ' + certVencendo() + ' vencendo' : certVencendo() + ' vencendo em 30 dias'"
                        tooltipPosition="right">{{ certAlertas() }}</span>
                    }
                  </a>
                </li>
              }
            }
          </ul>
        </div>
      }
    </nav>
  `,
  styles: [`
    :host {
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }
    .app-sidebar {
      width: 225px;
      flex-shrink: 0;
      background: var(--p-surface-50);
      border-right: 1px solid var(--p-surface-200);
      padding: 0.5rem 0 1rem;
      overflow-y: auto;
      overflow-x: hidden;
      transition: width 0.2s ease;
      position: relative;
      min-height: 100%;
      flex: 1;
    }
    .app-sidebar.collapsed {
      width: 58px;
    }

    .toggle-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: 1px solid var(--p-surface-200);
      background: var(--p-surface-0);
      color: var(--p-surface-500);
      cursor: pointer;
      position: absolute;
      right: -14px;
      top: 1.2rem;
      z-index: 10;
      transition: background 0.15s, color 0.15s;
      box-shadow: 0 1px 4px rgba(0,0,0,0.12);
    }
    .toggle-btn:hover { background: var(--p-primary-50); color: var(--p-primary-color); }
    .toggle-btn .pi { font-size: 0.75rem; }

    .menu-group { margin-top: 0.5rem; }
    .menu-group-label {
      display: block;
      padding: 0.5rem 1.25rem 0.25rem;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--p-surface-400);
      white-space: nowrap;
      overflow: hidden;
    }
    .menu-group-divider {
      height: 1px;
      background: var(--p-surface-200);
      margin: 0.75rem 0.75rem 0.25rem;
    }
    .menu-list { list-style: none; margin: 0; padding: 0; }
    .menu-item {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      padding: 0.55rem 1.25rem;
      color: var(--p-surface-700);
      text-decoration: none;
      font-size: 0.875rem;
      border-left: 3px solid transparent;
      transition: background 0.15s, border-color 0.15s;
      white-space: nowrap;
      overflow: visible;
      position: relative;
    }

    .menu-badge {
      margin-left: auto;
      background: #f97316;
      color: #fff;
      font-size: 0.7rem;
      font-weight: 700;
      line-height: 1;
      min-width: 18px;
      height: 18px;
      padding: 0 5px;
      border-radius: 9px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .menu-badge.danger { background: #ef4444; }
    .collapsed .menu-badge {
      position: absolute;
      top: 2px;
      right: 2px;
      margin-left: 0;
      min-width: 15px;
      height: 15px;
      padding: 0 3px;
      font-size: 0.58rem;
    }
    .collapsed .menu-item {
      padding: 0.6rem;
      justify-content: center;
      border-left: none;
      border-radius: 6px;
      margin: 0 4px;
    }
    .collapsed .menu-item.active {
      border-left: none;
      border-radius: 6px;
    }
    .menu-item:hover { background: var(--p-surface-100); }
    .menu-item.active {
      border-left-color: var(--p-primary-color);
      background: var(--p-primary-50);
      color: var(--p-primary-color);
      font-weight: 600;
    }
    .pi { font-size: 0.95rem; }

    /* Dark mode */
    :host-context(.dark) :host,
    :host-context(.dark) .app-sidebar {
      background: #12121e;
      border-right-color: #2a2a3d;
    }
    :host-context(.dark) .menu-group-label { color: #4a4a6a; }
    :host-context(.dark) .menu-group-divider { background: #2a2a3d; }
    :host-context(.dark) .menu-item { color: #c4c4dc; }
    :host-context(.dark) .menu-item:hover { background: #1e1e30; }
    :host-context(.dark) .menu-item.active {
      background: #1a1a40;
      color: var(--p-primary-300, #a5b4fc);
      border-left-color: var(--p-primary-300, #a5b4fc);
    }
    :host-context(.dark) .toggle-btn {
      background: #1e1e30;
      border-color: #2a2a3d;
      color: #6b6b8f;
    }
    :host-context(.dark) .toggle-btn:hover {
      background: #252540;
      color: var(--p-primary-300, #a5b4fc);
    }
  `],
})
export class SidebarComponent implements OnInit {
  protected readonly authStore = inject(AuthStore);
  private readonly certService = inject(CertificadoService);
  protected readonly collapsed = signal(false);

  // Contagem de certificados que precisam de atenção (badge no menu).
  protected readonly certVencendo = signal(0);
  protected readonly certVencidos = signal(0);
  protected readonly certAlertas = computed(() => this.certVencendo() + this.certVencidos());

  ngOnInit(): void {
    this.certService.resumo().subscribe({
      next: (r) => {
        this.certVencendo.set(r.vencendo);
        this.certVencidos.set(r.vencido);
      },
      error: () => {
        /* sem permissão / sem dados: simplesmente não mostra badge */
      },
    });
  }

  protected readonly menuGroups: MenuGroup[] = [
    {
      grupo: 'Principal',
      items: [
        { label: 'Dashboard', icon: 'pi-home', route: '/dashboard', color: '#6366f1' },
        { label: 'Fluxo de Caixa', icon: 'pi-chart-line', route: '/fluxo-caixa', color: '#0ea5e9' },
      ],
    },
    {
      grupo: 'Financeiro',
      items: [
        { label: 'Contas a Pagar', icon: 'pi-arrow-circle-up', route: '/contas-pagar', color: '#ef4444' },
        { label: 'Contas a Receber', icon: 'pi-arrow-circle-down', route: '/contas-receber', color: '#22c55e' },
        { label: 'Extrato Bancário', icon: 'pi-list', route: '/extrato-bancario', color: '#0891b2' },
        { label: 'Inadimplência', icon: 'pi-exclamation-circle', route: '/inadimplencia', color: '#f97316' },
        { label: 'Transferências', icon: 'pi-arrows-h', route: '/transferencias', color: '#14b8a6' },
        { label: 'Conciliação', icon: 'pi-check-square', route: '/conciliacao', color: '#8b5cf6' },
      ],
    },
    {
      grupo: 'Cadastros',
      items: [
        { label: 'Empresas', icon: 'pi-building', route: '/empresas', color: '#3b82f6' },
        { label: 'Categorias', icon: 'pi-tags', route: '/categorias', color: '#ec4899' },
        { label: 'Clientes / Fornec.', icon: 'pi-users', route: '/contatos', color: '#06b6d4' },
        { label: 'Contas / Cartões', icon: 'pi-credit-card', route: '/contas-bancarias', color: '#a855f7' },
        { label: 'Patrimonial', icon: 'pi-building-columns', route: '/patrimonial', color: '#f59e0b' },
      ],
    },
    {
      grupo: 'Relatórios',
      items: [
        { label: 'DRE / Resultado', icon: 'pi-chart-bar', route: '/relatorios', color: '#10b981' },
      ],
    },
    {
      grupo: 'Administração',
      items: [
        { label: 'Usuários', icon: 'pi-user-edit', route: '/usuarios', color: '#2563eb', apenasAdmin: true, tambemGestor: true },
        { label: 'Certificados', icon: 'pi-id-card', route: '/certificados', color: '#ca8a04' },
        { label: 'Pessoas (Certif.)', icon: 'pi-users', route: '/pessoas', color: '#65a30d' },
        { label: 'Importação', icon: 'pi-upload', route: '/importacao', color: '#0d9488', apenasAdmin: true, tambemGestor: true },
        { label: 'Configurações', icon: 'pi-cog', route: '/configuracoes', color: '#64748b' },
      ],
    },
    {
      grupo: 'Suporte',
      items: [
        { label: 'Ajuda', icon: 'pi-question-circle', route: '/ajuda', color: '#f43f5e' },
      ],
    },
  ];
}
