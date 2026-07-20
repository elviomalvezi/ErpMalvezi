import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from '../header/header.component';
import { SidebarComponent } from '../sidebar/sidebar.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, SidebarComponent],
  template: `
    <div class="layout-wrapper">
      <app-header />
      <div class="layout-body">
        <app-sidebar />
        <main class="layout-content">
          <router-outlet />
        </main>
      </div>
    </div>
  `,
  styles: [`
    .layout-wrapper {
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      background: var(--p-surface-100);
    }
    .layout-body {
      display: flex;
      flex: 1;
      background: var(--p-surface-100);
      align-items: stretch;
    }
    :host ::ng-deep app-sidebar {
      display: flex;
      flex-direction: column;
    }
    .layout-content {
      flex: 1;
      padding: 1.5rem;
      overflow-y: auto;
      background: var(--p-surface-100);
      min-height: 0;
    }
  `],
})
export class ShellComponent {}
