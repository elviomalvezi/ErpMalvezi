import { Routes } from '@angular/router';
import { ShellComponent } from './shared/layout/shell/shell.component';
import { authGuard, guestGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'contas-pagar',
        loadComponent: () =>
          import('./features/lancamentos/lancamentos.component').then(
            (m) => m.LancamentosComponent,
          ),
        data: { tipo: 'despesa' },
      },
      {
        path: 'contas-receber',
        loadComponent: () =>
          import('./features/lancamentos/lancamentos.component').then(
            (m) => m.LancamentosComponent,
          ),
        data: { tipo: 'receita' },
      },
      {
        path: 'transferencias',
        loadComponent: () =>
          import('./features/transferencias/transferencias.component').then(
            (m) => m.TransferenciasComponent,
          ),
      },
      {
        path: 'conciliacao',
        loadComponent: () =>
          import('./features/conciliacao/conciliacao.component').then(
            (m) => m.ConciliacaoComponent,
          ),
      },
      {
        path: 'fluxo-caixa',
        loadComponent: () =>
          import('./features/fluxo-caixa/fluxo-caixa.component').then(
            (m) => m.FluxoCaixaComponent,
          ),
      },
      {
        path: 'categorias',
        loadComponent: () =>
          import('./features/categorias/categorias.component').then((m) => m.CategoriasComponent),
      },
      {
        path: 'contatos',
        loadComponent: () =>
          import('./features/contatos/contatos.component').then((m) => m.ContatosComponent),
      },
      {
        path: 'contas-bancarias',
        loadComponent: () =>
          import('./features/contas-bancarias/contas-bancarias.component').then(
            (m) => m.ContasBancariasComponent,
          ),
      },
      {
        path: 'empresas',
        loadComponent: () =>
          import('./features/empresas/empresas.component').then((m) => m.EmpresasComponent),
      },
      {
        path: 'usuarios',
        loadComponent: () =>
          import('./features/usuarios/usuarios.component').then((m) => m.UsuariosComponent),
      },
      {
        path: 'patrimonial',
        loadComponent: () =>
          import('./features/patrimonial/patrimonial.component').then(
            (m) => m.PatrimonialComponent,
          ),
        children: [
          { path: '', redirectTo: 'veiculos', pathMatch: 'full' },
          {
            path: 'veiculos',
            loadComponent: () =>
              import('./features/patrimonial/veiculos/veiculos.component').then(
                (m) => m.VeiculosComponent,
              ),
          },
          {
            path: 'imoveis',
            loadComponent: () =>
              import('./features/patrimonial/imoveis/imoveis.component').then(
                (m) => m.ImoveisComponent,
              ),
          },
        ],
      },
      {
        path: 'configuracoes',
        loadComponent: () =>
          import('./features/configuracoes/configuracoes.component').then(
            (m) => m.ConfiguracoesComponent,
          ),
      },
    ],
  },
  { path: '**', redirectTo: 'dashboard' },
];
