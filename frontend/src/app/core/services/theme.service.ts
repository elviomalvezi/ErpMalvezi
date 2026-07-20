import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly darkMode = signal(localStorage.getItem('theme') === 'dark');

  constructor() {
    this.aplicar(this.darkMode());
  }

  toggle(): void {
    const novo = !this.darkMode();
    this.darkMode.set(novo);
    localStorage.setItem('theme', novo ? 'dark' : 'light');
    this.aplicar(novo);
  }

  private aplicar(dark: boolean): void {
    document.documentElement.classList.toggle('dark', dark);
  }
}
