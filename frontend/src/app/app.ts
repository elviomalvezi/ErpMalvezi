import { Component, inject, effect } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthStore } from './core/stores/auth.store';
import { EmpresaStore } from './core/stores/empresa.store';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet />`,
})
export class App {
  private readonly authStore = inject(AuthStore);
  private readonly empresaStore = inject(EmpresaStore);

  constructor() {
    effect(() => {
      if (this.authStore.isAuthenticated()) {
        this.empresaStore.carregar();
      } else {
        this.empresaStore.limpar();
      }
    });
  }
}
