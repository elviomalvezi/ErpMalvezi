import { Component, HostListener, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { DecimalPipe, DatePipe } from '@angular/common';
import { SelectModule } from 'primeng/select';
import { ButtonModule } from 'primeng/button';
import { AvatarModule } from 'primeng/avatar';
import { TooltipModule } from 'primeng/tooltip';
import { DialogModule } from 'primeng/dialog';
import { PasswordModule } from 'primeng/password';
import { BadgeModule } from 'primeng/badge';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { Subject, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, catchError } from 'rxjs/operators';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { EmpresaStore, Empresa } from '../../../core/stores/empresa.store';
import { AuthStore } from '../../../core/stores/auth.store';
import { AuthService } from '../../../core/services/auth.service';
import { DashboardService } from '../../../core/services/dashboard.service';
import { LancamentoService } from '../../../core/services/lancamento.service';
import { RelatorioService } from '../../../core/services/relatorio.service';
import { ThemeService } from '../../../core/services/theme.service';
import type { Lancamento } from '../../../core/models';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [SelectModule, ButtonModule, AvatarModule, TooltipModule, FormsModule,
            ReactiveFormsModule, DialogModule, PasswordModule, ToastModule, BadgeModule,
            DecimalPipe, DatePipe],
  providers: [MessageService],
  template: `
    <p-toast position="top-right" />

    <header class="app-header">
      <div class="header-brand">
        <span class="brand-name">App Financeiro</span>
      </div>

      <div class="header-busca" #buscaContainer>
        <div class="busca-wrap">
          <i class="pi pi-search busca-icon"></i>
          <input
            type="text"
            class="busca-input"
            placeholder="Buscar lançamentos, contatos... (mín. 2 letras)"
            [(ngModel)]="termoBusca"
            (input)="onBuscaInput()"
            (keydown.escape)="fecharResultados()"
            (focus)="onBuscaFocus()"
            autocomplete="off"
          />
          @if (buscando()) {
            <i class="pi pi-spin pi-spinner busca-clear" style="pointer-events:none"></i>
          } @else if (termoBusca) {
            <i class="pi pi-times busca-clear" (click)="fecharResultados()"></i>
          }
        </div>

        @if (mostrarResultados()) {
          <div class="busca-dropdown">
            @if (temResultados()) {
              <!-- Lançamentos -->
              @if (resultadosLanc().length > 0) {
                <div class="busca-grupo-label">
                  <i class="pi pi-list"></i> Lançamentos
                </div>
                @for (r of resultadosLanc(); track r.id) {
                  <div class="busca-item" (click)="irParaLancamento(r)">
                    <div class="busca-item-linha1">
                      <span class="busca-tipo" [class.receita]="r.tipo === 'RECEITA'">
                        {{ r.tipo === 'RECEITA' ? 'Receita' : 'Despesa' }}
                      </span>
                      <span class="busca-empresa">{{ empresaMap().get(r.empresa_id) }}</span>
                      <span class="busca-valor" [class.receita]="r.tipo === 'RECEITA'">
                        R$ {{ r.valor | number:'1.2-2':'pt-BR' }}
                      </span>
                    </div>
                    <div class="busca-descricao" [innerHTML]="destacar(r.descricao, termoBusca.trim())"></div>
                    <div class="busca-item-linha3">
                      <span class="busca-data">Venc. {{ r.data_vencimento | date:'dd/MM/yyyy' }}</span>
                      <span class="busca-status" [class]="'st-' + r.status">{{ statusLabel(r.status) }}</span>
                    </div>
                  </div>
                }
              }
              <!-- Contatos -->
              @if (resultadosCont().length > 0) {
                <div class="busca-grupo-label">
                  <i class="pi pi-users"></i> Contatos
                </div>
                @for (c of resultadosCont(); track c.id) {
                  <div class="busca-item busca-item-contato" (click)="irParaContato(c)">
                    <div class="busca-item-linha1">
                      <span class="busca-tipo" [class.receita]="c.eh_cliente">
                        {{ c.eh_cliente && c.eh_fornecedor ? 'Cliente/Fornec.' : c.eh_cliente ? 'Cliente' : 'Fornecedor' }}
                      </span>
                      <span class="busca-empresa">{{ c.tipo }}</span>
                    </div>
                    <div class="busca-descricao" [innerHTML]="destacar(c.nome_principal, termoBusca.trim())"></div>
                    @if (c.documento) {
                      <div class="busca-data">{{ c.documento }}</div>
                    }
                  </div>
                }
              }
              <!-- Categorias -->
              @if (resultadosCat().length > 0) {
                <div class="busca-grupo-label">
                  <i class="pi pi-tags"></i> Categorias
                </div>
                @for (cat of resultadosCat(); track cat.id) {
                  <div class="busca-item busca-item-cat" (click)="irParaCategorias()">
                    <div class="busca-item-linha1">
                      <span class="busca-tipo" [class.receita]="cat.tipo === 'RECEITA'">{{ cat.tipo }}</span>
                    </div>
                    <div class="busca-descricao" [innerHTML]="destacar(cat.nome, termoBusca.trim())"></div>
                  </div>
                }
              }
            } @else if (!buscando()) {
              <div class="busca-vazio">
                <i class="pi pi-search-minus"></i>
                Nenhum resultado para "{{ termoBusca }}"
              </div>
            }
          </div>
        }
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
        <div class="theme-btn" pTooltip="Alternar tema" tooltipPosition="bottom" (click)="themeSvc.toggle()">
          <i [class]="themeSvc.darkMode() ? 'pi pi-sun' : 'pi pi-moon'"></i>
        </div>
        <div class="sino-wrap" pTooltip="Alertas de vencimento" tooltipPosition="bottom" (click)="irParaVencidos()">
          <i class="pi pi-bell sino-icon"></i>
          @if (alertasCount() > 0) {
            <span class="sino-badge">{{ alertasCount() > 99 ? '99+' : alertasCount() }}</span>
          }
        </div>
        <p-avatar
          [label]="inicialNome()"
          shape="circle"
          class="cursor-pointer"
          pTooltip="Alterar senha"
          tooltipPosition="bottom"
          (click)="abrirAlterarSenha()"
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

    <!-- Dialog Alterar Senha -->
    <p-dialog
      header="Alterar Senha"
      [(visible)]="dialogVisible"
      [modal]="true"
      [style]="{width: '380px'}"
      [closable]="true"
    >
      <form [formGroup]="senhaForm" class="senha-form">
        <div class="field">
          <label>Senha atual *</label>
          <p-password
            formControlName="senhaAtual"
            [feedback]="false"
            [toggleMask]="true"
            styleClass="w-full"
            placeholder="Digite sua senha atual"
          />
        </div>
        <div class="field">
          <label>Nova senha *</label>
          <p-password
            formControlName="novaSenha"
            [feedback]="true"
            [toggleMask]="true"
            styleClass="w-full"
            placeholder="Mínimo 8 caracteres"
          />
        </div>
        <div class="field">
          <label>Confirmar nova senha *</label>
          <p-password
            formControlName="confirmarSenha"
            [feedback]="false"
            [toggleMask]="true"
            styleClass="w-full"
            placeholder="Repita a nova senha"
          />
          @if (senhaForm.hasError('senhaMismatch') && senhaForm.get('confirmarSenha')?.touched) {
            <small class="p-error">As senhas não coincidem.</small>
          }
        </div>
      </form>
      <ng-template pTemplate="footer">
        <p-button label="Cancelar" [text]="true" severity="secondary" (onClick)="dialogVisible.set(false)" />
        <p-button
          label="Alterar Senha"
          icon="pi pi-lock"
          [loading]="salvando()"
          [disabled]="senhaForm.invalid"
          (onClick)="salvarSenha()"
        />
      </ng-template>
    </p-dialog>
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
    .header-brand { flex-shrink: 0; }
    .brand-name {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--p-primary-color);
    }
    .header-empresa { flex: 1; max-width: 380px; }
    .header-actions {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .empresa-item { display: flex; align-items: center; gap: 0.5rem; }
    .empresa-tipo-badge {
      font-size: 0.65rem; font-weight: 700; padding: 0.1rem 0.35rem;
      border-radius: 4px; background: var(--p-orange-100); color: var(--p-orange-700);
    }
    .empresa-tipo-badge.pj { background: var(--p-blue-100); color: var(--p-blue-700); }
    :host ::ng-deep .empresa-select {
      min-width: 280px;
      background: var(--p-primary-color, #16a34a);
      border-color: var(--p-primary-color, #16a34a);
    }
    :host ::ng-deep .empresa-select:not(.p-disabled):hover {
      border-color: var(--p-primary-color, #16a34a);
      filter: brightness(0.95);
    }
    :host ::ng-deep .empresa-select.p-focus,
    :host ::ng-deep .empresa-select:not(.p-disabled).p-focus {
      border-color: var(--p-primary-color, #16a34a);
      box-shadow: 0 0 0 2px color-mix(in srgb, var(--p-primary-color, #16a34a) 35%, transparent);
    }
    :host ::ng-deep .empresa-select .p-select-label,
    :host ::ng-deep .empresa-select .p-placeholder { color: #fff; font-weight: 600; }
    :host ::ng-deep .empresa-select .p-select-dropdown,
    :host ::ng-deep .empresa-select .p-select-dropdown .p-icon,
    :host ::ng-deep .empresa-select .p-select-clear-icon { color: #fff; }

    /* ── Busca ──────────────────────────────────────────────── */
    .header-busca { flex: 1; max-width: 360px; position: relative; }
    .busca-wrap { position: relative; display: flex; align-items: center; }
    .busca-icon { position: absolute; left: 0.6rem; color: var(--p-surface-400); font-size: 0.85rem; }
    .busca-input {
      width: 100%; padding: 0.45rem 2rem 0.45rem 2rem;
      border: 1px solid var(--p-surface-200); border-radius: 6px;
      background: var(--p-surface-50); font-size: 0.875rem;
      color: var(--p-surface-700); outline: none;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    .busca-input:focus {
      border-color: var(--p-primary-color);
      box-shadow: 0 0 0 2px var(--p-primary-100);
      background: white;
    }
    .busca-clear {
      position: absolute; right: 0.6rem; color: var(--p-surface-400);
      cursor: pointer; font-size: 0.85rem;
    }
    .busca-clear:hover { color: var(--p-surface-700); }

    /* Dropdown de resultados */
    .busca-dropdown {
      position: absolute;
      top: calc(100% + 4px);
      left: 0;
      width: 100%;
      min-width: 340px;
      background: var(--p-surface-0);
      border: 1px solid var(--p-surface-200);
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.12);
      z-index: 200;
      max-height: 480px;
      overflow-y: auto;
    }
    .busca-item {
      padding: 0.6rem 0.875rem;
      border-bottom: 1px solid var(--p-surface-100);
      cursor: pointer;
      transition: background 0.1s;
    }
    .busca-item:last-child { border-bottom: none; }
    .busca-item:hover { background: var(--p-surface-50); }
    .busca-item-linha1 {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.25rem;
    }
    .busca-tipo {
      font-size: 0.62rem; font-weight: 700; padding: 0.1rem 0.35rem;
      border-radius: 4px; background: var(--p-red-100); color: var(--p-red-700);
      flex-shrink: 0;
    }
    .busca-tipo.receita { background: var(--p-green-100); color: var(--p-green-700); }
    .busca-empresa {
      font-size: 0.75rem; color: var(--p-surface-500); flex: 1;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .busca-valor {
      font-size: 0.8rem; font-weight: 600; color: var(--p-red-600); flex-shrink: 0;
    }
    .busca-valor.receita { color: var(--p-green-600); }
    .busca-descricao {
      font-size: 0.82rem; color: var(--p-surface-700); margin-bottom: 0.2rem;
      overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    :host ::ng-deep .busca-descricao mark {
      background: #fef08a; color: inherit; border-radius: 2px; padding: 0 1px;
    }
    .busca-item-linha3 {
      display: flex; align-items: center; gap: 0.5rem;
    }
    .busca-data { font-size: 0.72rem; color: var(--p-surface-400); }
    .busca-status {
      font-size: 0.62rem; font-weight: 700; padding: 0.1rem 0.35rem;
      border-radius: 4px; text-transform: uppercase;
    }
    .st-pendente { background: var(--p-yellow-100); color: var(--p-yellow-700); }
    .st-pago { background: var(--p-green-100); color: var(--p-green-700); }
    .st-cancelado { background: var(--p-surface-100); color: var(--p-surface-500); }
    .busca-vazio {
      padding: 1.25rem 1rem; text-align: center;
      color: var(--p-surface-400); font-size: 0.85rem;
      display: flex; align-items: center; justify-content: center; gap: 0.5rem;
    }
    .busca-grupo-label {
      padding: 0.35rem 0.875rem; font-size: 0.68rem; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.06em;
      color: var(--p-surface-400); background: var(--p-surface-50);
      border-bottom: 1px solid var(--p-surface-100);
      display: flex; align-items: center; gap: 0.35rem;
    }
    .busca-item-contato .busca-descricao { font-weight: 600; }
    .busca-item-cat .busca-tipo { background: var(--p-purple-100); color: var(--p-purple-700); }

    /* Ações header */
    .theme-btn {
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      width: 36px; height: 36px; border-radius: 50%; transition: background 0.15s;
      color: var(--p-surface-600); font-size: 1rem;
    }
    .theme-btn:hover { background: var(--p-surface-100); }
    .sino-wrap {
      position: relative; cursor: pointer; display: flex;
      align-items: center; justify-content: center;
      width: 36px; height: 36px; border-radius: 50%; transition: background 0.15s;
    }
    .sino-wrap:hover { background: var(--p-surface-100); }
    .sino-icon { font-size: 1.1rem; color: var(--p-surface-600); }
    .sino-badge {
      position: absolute; top: 2px; right: 2px; background: var(--p-red-500);
      color: white; font-size: 0.6rem; font-weight: 700; border-radius: 10px;
      padding: 1px 4px; min-width: 16px; text-align: center; line-height: 14px;
    }

    /* Dark mode */
    :host-context(.dark) .app-header { background: #0f0f1a; border-bottom-color: #2a2a3d; color: #c4c4dc; }
    :host-context(.dark) .brand-name { color: var(--p-primary-300, #a5b4fc); }
    :host-context(.dark) .busca-input { background: #1a1a2e; border-color: #2a2a3d; color: #c4c4dc; }
    :host-context(.dark) .busca-input:focus { background: #1e1e38; border-color: var(--p-primary-400, #818cf8); }
    :host-context(.dark) .busca-icon, :host-context(.dark) .busca-clear { color: #4a4a6a; }
    :host-context(.dark) .busca-dropdown { background: #1a1a2e; border-color: #2a2a3d; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
    :host-context(.dark) .busca-item { border-bottom-color: #2a2a3d; }
    :host-context(.dark) .busca-item:hover { background: #1e1e38; }
    :host-context(.dark) .busca-descricao { color: #c4c4dc; }
    :host-context(.dark) .busca-empresa { color: #6a6a8a; }
    :host-context(.dark) .theme-btn, :host-context(.dark) .sino-wrap { color: #8888aa; }
    :host-context(.dark) .theme-btn:hover, :host-context(.dark) .sino-wrap:hover { background: #1e1e30; color: var(--p-primary-300, #a5b4fc); }
    :host-context(.dark) ::ng-deep .busca-descricao mark { background: #713f12; color: #fef08a; }
  `],
})
export class HeaderComponent implements OnInit {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly authStore = inject(AuthStore);
  private readonly authService = inject(AuthService);
  private readonly dashboardService = inject(DashboardService);
  private readonly lancamentoSvc = inject(LancamentoService);
  private readonly relatorioSvc = inject(RelatorioService);
  protected readonly themeSvc = inject(ThemeService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly messageService = inject(MessageService);

  protected empresaSelecionada: Empresa | null = this.empresaStore.empresaAtiva();
  protected dialogVisible = signal(false);
  protected salvando = signal(false);
  protected alertasCount = signal(0);
  protected termoBusca = '';

  protected readonly resultadosLanc = signal<Lancamento[]>([]);
  protected readonly resultadosCont = signal<any[]>([]);
  protected readonly resultadosCat = signal<{ id: string; nome: string; tipo: string }[]>([]);
  protected readonly buscando = signal(false);
  protected readonly mostrarResultados = signal(false);

  protected readonly temResultados = computed(
    () => this.resultadosLanc().length > 0 || this.resultadosCont().length > 0 || this.resultadosCat().length > 0
  );

  protected readonly empresaMap = computed(() =>
    new Map(this.empresaStore.empresas().map(e => [e.id, e.nome]))
  );

  private readonly buscaSubject = new Subject<string>();

  protected senhaForm = this.fb.group(
    {
      senhaAtual: ['', Validators.required],
      novaSenha: ['', [Validators.required, Validators.minLength(8)]],
      confirmarSenha: ['', Validators.required],
    },
    { validators: this.senhasIguais },
  );

  constructor() {
    this.buscaSubject.pipe(
      debounceTime(350),
      distinctUntilChanged(),
      switchMap(q => {
        if (!q || q.length < 2) {
          this.resultadosLanc.set([]);
          this.resultadosCont.set([]);
          this.resultadosCat.set([]);
          this.buscando.set(false);
          return of(null);
        }
        this.buscando.set(true);
        this.mostrarResultados.set(true);
        return this.relatorioSvc.buscaGlobal(q).pipe(
          catchError(() => of(null))
        );
      }),
      takeUntilDestroyed(),
    ).subscribe(result => {
      if (result) {
        this.resultadosLanc.set(result.lancamentos ?? []);
        this.resultadosCont.set(result.contatos ?? []);
        this.resultadosCat.set(result.categorias ?? []);
      }
      this.buscando.set(false);
    });
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(e: MouseEvent): void {
    const target = e.target as HTMLElement;
    if (!target.closest('.header-busca')) {
      this.mostrarResultados.set(false);
    }
  }

  protected onBuscaInput(): void {
    const v = this.termoBusca.trim();
    if (!v) {
      this.resultadosLanc.set([]);
      this.resultadosCont.set([]);
      this.resultadosCat.set([]);
      this.mostrarResultados.set(false);
      this.buscando.set(false);
    }
    this.buscaSubject.next(v);
  }

  protected onBuscaFocus(): void {
    if (this.temResultados()) {
      this.mostrarResultados.set(true);
    }
  }

  protected fecharResultados(): void {
    this.termoBusca = '';
    this.resultadosLanc.set([]);
    this.resultadosCont.set([]);
    this.resultadosCat.set([]);
    this.mostrarResultados.set(false);
    this.buscando.set(false);
  }

  protected irParaLancamento(r: Lancamento): void {
    const rota = r.tipo === 'RECEITA' ? '/contas-receber' : '/contas-pagar';
    const empresaAtual = this.empresaStore.empresaAtiva();
    if (empresaAtual?.id !== r.empresa_id) {
      const empresa = this.empresaStore.empresas().find(e => e.id === r.empresa_id);
      if (empresa) {
        this.empresaStore.selecionarEmpresa(empresa);
        this.empresaSelecionada = empresa;
      }
    }
    const [y, m] = r.data_vencimento.split('-');
    void this.router.navigate([rota], { queryParams: { abrir: r.id, mes: `${y}-${m}` } });
    this.fecharResultados();
  }

  protected irParaContato(_c: any): void {
    void this.router.navigate(['/contatos']);
    this.fecharResultados();
  }

  protected irParaCategorias(): void {
    void this.router.navigate(['/categorias']);
    this.fecharResultados();
  }

  protected destacar(texto: string, termo: string): string {
    if (!termo || termo.length < 2) return texto;
    const safe = termo.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return texto.replace(new RegExp(`(${safe})`, 'gi'), '<mark>$1</mark>');
  }

  protected statusLabel(status: string): string {
    const map: Record<string, string> = { pendente: 'Pendente', pago: 'Pago', cancelado: 'Cancelado' };
    return map[status] ?? status;
  }

  private senhasIguais(group: import('@angular/forms').AbstractControl) {
    const nova = group.get('novaSenha')?.value;
    const confirmar = group.get('confirmarSenha')?.value;
    return nova && confirmar && nova !== confirmar ? { senhaMismatch: true } : null;
  }

  protected inicialNome(): string {
    const nome = this.authStore.nome();
    if (!nome) return 'U';
    const partes = nome.trim().split(' ');
    return partes.length >= 2
      ? (partes[0][0] + partes[partes.length - 1][0]).toUpperCase()
      : partes[0][0].toUpperCase();
  }

  protected abrirAlterarSenha(): void {
    this.senhaForm.reset();
    this.dialogVisible.set(true);
  }

  protected salvarSenha(): void {
    if (this.senhaForm.invalid) return;
    const { senhaAtual, novaSenha } = this.senhaForm.value;
    this.salvando.set(true);
    this.authService.alterarSenha(senhaAtual!, novaSenha!).subscribe({
      next: () => {
        this.salvando.set(false);
        this.dialogVisible.set(false);
        this.messageService.add({ severity: 'success', summary: 'Senha alterada com sucesso.' });
      },
      error: (err) => {
        this.salvando.set(false);
        const msg = err?.error?.detail ?? 'Erro ao alterar senha.';
        this.messageService.add({ severity: 'error', summary: msg });
      },
    });
  }

  ngOnInit(): void {
    this.carregarAlertas();
  }

  private carregarAlertas(): void {
    const hoje = new Date();
    const inicio = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}-01`;
    const fim = hoje.toISOString().split('T')[0];
    this.dashboardService.graficos(inicio, fim, fim).subscribe({
      next: (g) => this.alertasCount.set(g.alertas_count),
      error: () => {},
    });
  }

  protected irParaVencidos(): void {
    void this.router.navigate(['/contas-pagar']);
  }

  protected onEmpresaChange(empresa: Empresa): void {
    this.empresaStore.selecionarEmpresa(empresa);
  }

  protected logout(): void {
    this.authStore.clearAuth();
    void this.router.navigate(['/login']);
  }
}
