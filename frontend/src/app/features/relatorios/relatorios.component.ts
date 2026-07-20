import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { SelectModule } from 'primeng/select';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { SkeletonModule } from 'primeng/skeleton';
import { MessageService } from 'primeng/api';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { RelatorioService, DreResponse, DreLinha } from '../../core/services/relatorio.service';

@Component({
  selector: 'app-relatorios',
  standalone: true,
  providers: [MessageService],
  imports: [
    FormsModule, DecimalPipe,
    ButtonModule, SelectModule, CardModule, TagModule,
    MessageModule, ToastModule, SkeletonModule,
  ],
  template: `
    <p-toast />
    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Relatório DRE</h1>
          <p class="page-subtitle">Demonstrativo de Resultado — Regime de Caixa</p>
        </div>
        <div class="header-actions">
          <p-button
            label="Enviar alertas agora"
            icon="pi pi-envelope"
            severity="secondary"
            [outlined]="true"
            size="small"
            [loading]="enviandoNotif()"
            pTooltip="Envia e-mail de vencimentos para todos os usuários"
            (onClick)="enviarNotificacoes()"
          />
          <p-button
            label="Exportar PDF"
            icon="pi pi-file-pdf"
            severity="danger"
            [outlined]="true"
            [disabled]="!dre() || carregando()"
            (onClick)="exportarPdf()"
          />
        </div>
      </div>

      <!-- Filtros -->
      <div class="filtros-bar">
        <div class="filtro-grupo">
          <label>Mês/Ano</label>
          <p-select
            [options]="mesOpts()"
            [(ngModel)]="mesReferencia"
            optionLabel="label"
            optionValue="value"
            [style]="{ width: '200px' }"
            (onChange)="carregar()"
          />
        </div>
        <div class="filtro-grupo">
          <label>Empresa</label>
          <p-select
            [options]="empresaOpts()"
            [(ngModel)]="empresaFiltro"
            optionLabel="label"
            optionValue="value"
            placeholder="Todas as empresas"
            [showClear]="true"
            [style]="{ width: '240px' }"
            (onChange)="carregar()"
          />
        </div>
      </div>

      @if (carregando()) {
        <div class="skeleton-wrap">
          @for (_ of [1,2,3,4,5]; track $index) {
            <p-skeleton height="2rem" styleClass="mb-2" />
          }
        </div>
      } @else if (dre()) {
        <!-- KPIs rápidos -->
        <div class="kpi-row">
          <div class="kpi-card receita">
            <span class="kpi-label">Receitas</span>
            <span class="kpi-valor">{{ dre()!.total_receitas_atual | number:'1.2-2':'pt-BR' }}</span>
            <span class="kpi-ant">Mês ant: {{ dre()!.total_receitas_anterior | number:'1.2-2':'pt-BR' }}</span>
          </div>
          <div class="kpi-card despesa">
            <span class="kpi-label">Despesas</span>
            <span class="kpi-valor">{{ dre()!.total_despesas_atual | number:'1.2-2':'pt-BR' }}</span>
            <span class="kpi-ant">Mês ant: {{ dre()!.total_despesas_anterior | number:'1.2-2':'pt-BR' }}</span>
          </div>
          <div class="kpi-card" [class.positivo]="dre()!.resultado_atual >= 0" [class.negativo]="dre()!.resultado_atual < 0">
            <span class="kpi-label">Resultado Líquido</span>
            <span class="kpi-valor">{{ dre()!.resultado_atual | number:'1.2-2':'pt-BR' }}</span>
            <span class="kpi-ant">Mês ant: {{ dre()!.resultado_anterior | number:'1.2-2':'pt-BR' }}</span>
          </div>
        </div>

        <!-- Tabela DRE -->
        <div class="dre-table" id="dre-tabela">
          <!-- Cabeçalho -->
          <div class="dre-header">
            <span>Categoria</span>
            <span>{{ mesLabel(dre()!.mes_referencia) }}</span>
            <span>{{ mesLabel(dre()!.mes_anterior) }}</span>
            <span>Variação</span>
          </div>

          <!-- RECEITAS -->
          <div class="dre-secao-titulo receita">RECEITAS</div>
          @for (linha of dreReceitas(); track linha.categoria_id) {
            <div class="dre-linha" [class]="'nivel-' + linha.nivel" [class.zero]="linha.total_atual === 0">
              <span class="cat-nome">
                @if (linha.nivel > 1) { <span class="indent">{{ '└ '.repeat(linha.nivel - 1) }}</span> }
                {{ linha.categoria_nome }}
              </span>
              <span class="valor-cel receita">{{ linha.total_atual | number:'1.2-2':'pt-BR' }}</span>
              <span class="valor-cel ant">{{ linha.total_anterior | number:'1.2-2':'pt-BR' }}</span>
              <span class="var-cel" [class.pos]="(linha.variacao_pct ?? 0) >= 0" [class.neg]="(linha.variacao_pct ?? 0) < 0">
                @if (linha.variacao_pct !== null) {
                  {{ linha.variacao_pct >= 0 ? '+' : '' }}{{ linha.variacao_pct | number:'1.1-1':'pt-BR' }}%
                } @else { — }
              </span>
            </div>
          }
          <div class="dre-subtotal receita">
            <span>Total Receitas</span>
            <span>{{ dre()!.total_receitas_atual | number:'1.2-2':'pt-BR' }}</span>
            <span>{{ dre()!.total_receitas_anterior | number:'1.2-2':'pt-BR' }}</span>
            <span>{{ variacaoPct(dre()!.total_receitas_atual, dre()!.total_receitas_anterior) }}</span>
          </div>

          <!-- DESPESAS -->
          <div class="dre-secao-titulo despesa">DESPESAS</div>
          @for (linha of dreDespesas(); track linha.categoria_id) {
            <div class="dre-linha" [class]="'nivel-' + linha.nivel" [class.zero]="linha.total_atual === 0">
              <span class="cat-nome">
                @if (linha.nivel > 1) { <span class="indent">{{ '└ '.repeat(linha.nivel - 1) }}</span> }
                {{ linha.categoria_nome }}
              </span>
              <span class="valor-cel despesa">{{ linha.total_atual | number:'1.2-2':'pt-BR' }}</span>
              <span class="valor-cel ant">{{ linha.total_anterior | number:'1.2-2':'pt-BR' }}</span>
              <span class="var-cel" [class.pos]="(linha.variacao_pct ?? 0) <= 0" [class.neg]="(linha.variacao_pct ?? 0) > 0">
                @if (linha.variacao_pct !== null) {
                  {{ linha.variacao_pct >= 0 ? '+' : '' }}{{ linha.variacao_pct | number:'1.1-1':'pt-BR' }}%
                } @else { — }
              </span>
            </div>
          }
          <div class="dre-subtotal despesa">
            <span>Total Despesas</span>
            <span>{{ dre()!.total_despesas_atual | number:'1.2-2':'pt-BR' }}</span>
            <span>{{ dre()!.total_despesas_anterior | number:'1.2-2':'pt-BR' }}</span>
            <span>{{ variacaoPct(dre()!.total_despesas_atual, dre()!.total_despesas_anterior) }}</span>
          </div>

          <!-- RESULTADO -->
          <div class="dre-resultado" [class.positivo]="dre()!.resultado_atual >= 0" [class.negativo]="dre()!.resultado_atual < 0">
            <span>RESULTADO LÍQUIDO</span>
            <span>{{ dre()!.resultado_atual | number:'1.2-2':'pt-BR' }}</span>
            <span>{{ dre()!.resultado_anterior | number:'1.2-2':'pt-BR' }}</span>
            <span>{{ variacaoPct(dre()!.resultado_atual, dre()!.resultado_anterior) }}</span>
          </div>
        </div>

      } @else if (!carregando()) {
        <div class="empty-state">
          <i class="pi pi-chart-bar"></i>
          <p>Selecione o mês e a empresa para gerar o DRE.</p>
        </div>
      }
    </div>
  `,
  styles: [`
    .page { padding: 1.5rem; max-width: 1100px; }
    .page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.5rem; }
    .page-title { font-size: 1.4rem; font-weight: 700; margin: 0; }
    .page-subtitle { margin: 0.2rem 0 0; color: var(--p-surface-500); font-size: 0.875rem; }
    .header-actions { display: flex; gap: 0.5rem; align-items: center; }

    .filtros-bar { display: flex; gap: 1.5rem; align-items: flex-end; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .filtro-grupo { display: flex; flex-direction: column; gap: 0.3rem; }
    .filtro-grupo label { font-size: 0.75rem; font-weight: 600; color: var(--p-surface-500); text-transform: uppercase; }
    .input-mes {
      padding: 0.45rem 0.75rem; border: 1px solid var(--p-surface-300); border-radius: 6px;
      font-size: 0.875rem; color: var(--p-surface-700); background: var(--p-surface-0);
    }

    .kpi-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    .kpi-card {
      background: var(--p-surface-0); border: 1px solid var(--p-surface-200); border-radius: 10px;
      padding: 1rem 1.25rem; display: flex; flex-direction: column; gap: 0.25rem;
    }
    .kpi-card.receita { border-top: 3px solid var(--p-green-500); }
    .kpi-card.despesa { border-top: 3px solid var(--p-red-500); }
    .kpi-card.positivo { border-top: 3px solid var(--p-blue-500); }
    .kpi-card.negativo { border-top: 3px solid var(--p-orange-500); }
    .kpi-label { font-size: 0.75rem; font-weight: 600; color: var(--p-surface-500); text-transform: uppercase; }
    .kpi-valor { font-size: 1.4rem; font-weight: 700; color: var(--p-surface-800); }
    .kpi-ant { font-size: 0.75rem; color: var(--p-surface-400); }

    .dre-table { border: 1px solid var(--p-surface-200); border-radius: 10px; overflow: hidden; }
    .dre-header {
      display: grid; grid-template-columns: 1fr 160px 160px 100px;
      padding: 0.6rem 1rem; background: var(--p-surface-100);
      font-size: 0.75rem; font-weight: 700; color: var(--p-surface-500); text-transform: uppercase;
    }
    .dre-header span:not(:first-child) { text-align: right; }

    .dre-secao-titulo {
      padding: 0.5rem 1rem; font-size: 0.8rem; font-weight: 800; letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .dre-secao-titulo.receita { background: var(--p-green-50); color: var(--p-green-700); }
    .dre-secao-titulo.despesa { background: var(--p-red-50); color: var(--p-red-700); }

    .dre-linha {
      display: grid; grid-template-columns: 1fr 160px 160px 100px;
      padding: 0.4rem 1rem; border-bottom: 1px solid var(--p-surface-100);
      font-size: 0.875rem; align-items: center; transition: background 0.1s;
    }
    .dre-linha:hover { background: var(--p-surface-50); }
    .dre-linha.zero { opacity: 0.45; }
    .dre-linha.nivel-2 { padding-left: 1.75rem; background: var(--p-surface-0); }
    .dre-linha.nivel-3 { padding-left: 2.5rem; font-size: 0.82rem; background: var(--p-surface-0); }

    .cat-nome { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .indent { color: var(--p-surface-400); }
    .valor-cel { text-align: right; font-variant-numeric: tabular-nums; }
    .valor-cel.receita { color: var(--p-green-700); font-weight: 600; }
    .valor-cel.despesa { color: var(--p-red-700); font-weight: 600; }
    .valor-cel.ant { color: var(--p-surface-400); }
    .var-cel { text-align: right; font-size: 0.8rem; font-weight: 600; }
    .var-cel.pos { color: var(--p-green-600); }
    .var-cel.neg { color: var(--p-red-600); }

    .dre-subtotal {
      display: grid; grid-template-columns: 1fr 160px 160px 100px;
      padding: 0.6rem 1rem; font-weight: 700; font-size: 0.875rem;
    }
    .dre-subtotal.receita { background: var(--p-green-50); color: var(--p-green-800); }
    .dre-subtotal.despesa { background: var(--p-red-50); color: var(--p-red-800); }
    .dre-subtotal span:not(:first-child) { text-align: right; }

    .dre-resultado {
      display: grid; grid-template-columns: 1fr 160px 160px 100px;
      padding: 0.75rem 1rem; font-weight: 800; font-size: 1rem;
      border-top: 2px solid var(--p-surface-300);
    }
    .dre-resultado.positivo { background: var(--p-blue-50); color: var(--p-blue-800); }
    .dre-resultado.negativo { background: var(--p-orange-50); color: var(--p-orange-800); }
    .dre-resultado span:not(:first-child) { text-align: right; }

    .empty-state { display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
      padding: 3rem; color: var(--p-surface-400); }
    .empty-state i { font-size: 3rem; }
    .skeleton-wrap { padding: 0.5rem; }

    @media (max-width: 768px) {
      .kpi-row { grid-template-columns: 1fr; }
      .dre-header, .dre-linha, .dre-subtotal, .dre-resultado {
        grid-template-columns: 1fr 110px 110px 80px;
      }
    }
  `],
})
export class RelatoriosComponent implements OnInit {
  private readonly relatorioSvc = inject(RelatorioService);
  private readonly empresaStore = inject(EmpresaStore);
  private readonly messageSvc = inject(MessageService);

  protected readonly dre = signal<DreResponse | null>(null);
  protected readonly carregando = signal(false);
  protected readonly enviandoNotif = signal(false);

  protected mesReferencia: string = '';
  protected empresaFiltro: string | null = null;

  protected readonly mesMax = signal('');
  protected readonly mesOpts = signal<{ label: string; value: string }[]>([]);

  protected readonly empresaOpts = computed(() =>
    this.empresaStore.empresas().map(e => ({ label: e.nome, value: e.id }))
  );

  protected readonly dreReceitas = computed(() =>
    (this.dre()?.receitas ?? []).filter(l => l.total_atual > 0 || l.total_anterior > 0)
  );

  protected readonly dreDespesas = computed(() =>
    (this.dre()?.despesas ?? []).filter(l => l.total_atual > 0 || l.total_anterior > 0)
  );

  ngOnInit(): void {
    const hoje = new Date();
    this.mesReferencia = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`;
    this.mesMax.set(this.mesReferencia);
    this.gerarMeses();
    this.carregar();
  }

  private gerarMeses(): void {
    const opts: { label: string; value: string }[] = [];
    const hoje = new Date();
    // Últimos 24 meses, do mais recente para o mais antigo.
    for (let i = 0; i < 24; i++) {
      const d = new Date(hoje.getFullYear(), hoje.getMonth() - i, 1);
      const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      const nome = d.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' });
      opts.push({ label: nome.charAt(0).toUpperCase() + nome.slice(1), value });
    }
    this.mesOpts.set(opts);
  }

  protected carregar(): void {
    if (!this.mesReferencia) return;
    this.carregando.set(true);
    this.relatorioSvc.dre(this.mesReferencia, this.empresaFiltro ?? undefined).subscribe({
      next: (data) => {
        this.dre.set(data);
        this.carregando.set(false);
      },
      error: () => {
        this.carregando.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro ao carregar DRE.' });
      },
    });
  }

  protected enviarNotificacoes(): void {
    this.enviandoNotif.set(true);
    this.relatorioSvc.enviarNotificacoes().subscribe({
      next: (r) => {
        this.enviandoNotif.set(false);
        this.messageSvc.add({ severity: 'success', summary: r.mensagem });
      },
      error: () => {
        this.enviandoNotif.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro ao enviar notificações.' });
      },
    });
  }

  protected mesLabel(mes: string): string {
    if (!mes) return '';
    const [y, m] = mes.split('-');
    const d = new Date(Number(y), Number(m) - 1, 1);
    return d.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' }).replace('.', '').replace(' ', '/');
  }

  protected variacaoPct(atual: number, anterior: number): string {
    if (!anterior || anterior === 0) return '—';
    const pct = ((atual - anterior) / anterior) * 100;
    return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`;
  }

  protected exportarPdf(): void {
    const data = this.dre();
    if (!data) return;

    import('jspdf').then(({ jsPDF }) => {
      const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
      const mes = this.mesLabel(data.mes_referencia);
      const empresa = data.empresa_nome ?? 'Todas as empresas';

      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text('Demonstrativo de Resultado (DRE)', 14, 18);
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(`Empresa: ${empresa}   |   Mês: ${mes}   |   Regime de Caixa`, 14, 26);

      let y = 34;
      const col = [14, 140, 200, 255];
      const rowH = 7;

      const header = (title: string, bgR: number, bgG: number, bgB: number) => {
        doc.setFillColor(bgR, bgG, bgB);
        doc.rect(14, y, 269, rowH, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(255, 255, 255);
        doc.text(title, col[0] + 2, y + 5);
        doc.text(mes, col[1], y + 5, { align: 'right' });
        doc.text(this.mesLabel(data.mes_anterior), col[2], y + 5, { align: 'right' });
        doc.text('Variação', col[3], y + 5, { align: 'right' });
        doc.setTextColor(0, 0, 0);
        y += rowH;
      };

      const row = (linha: DreLinha, tipo: 'rec' | 'desp') => {
        if (Number(linha.total_atual) === 0 && Number(linha.total_anterior) === 0) return;
        const indent = '  '.repeat(linha.nivel - 1);
        doc.setFont('helvetica', linha.nivel === 1 ? 'bold' : 'normal');
        doc.setFontSize(8);
        doc.text(indent + linha.categoria_nome, col[0] + 2, y + 4.5);
        const fmt = (v: number) => `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
        doc.text(fmt(linha.total_atual), col[1], y + 4.5, { align: 'right' });
        doc.text(fmt(linha.total_anterior), col[2], y + 4.5, { align: 'right' });
        if (linha.variacao_pct !== null) {
          const pct = linha.variacao_pct;
          doc.setTextColor(pct <= 0 && tipo === 'desp' ? 22 : pct >= 0 && tipo === 'rec' ? 22 : 220, 163, 74);
          doc.text(`${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`, col[3], y + 4.5, { align: 'right' });
          doc.setTextColor(0, 0, 0);
        } else {
          doc.text('—', col[3], y + 4.5, { align: 'right' });
        }
        doc.setDrawColor(220, 220, 220);
        doc.line(14, y + rowH, 283, y + rowH);
        y += rowH;
        if (y > 185) { doc.addPage(); y = 14; }
      };

      const subtotal = (label: string, atual: number, ant: number, bgR: number, bgG: number, bgB: number) => {
        doc.setFillColor(bgR, bgG, bgB);
        doc.rect(14, y, 269, rowH, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(9);
        doc.text(label, col[0] + 2, y + 5);
        const fmt = (v: number) => `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
        doc.text(fmt(atual), col[1], y + 5, { align: 'right' });
        doc.text(fmt(ant), col[2], y + 5, { align: 'right' });
        doc.text(this.variacaoPct(atual, ant), col[3], y + 5, { align: 'right' });
        y += rowH + 2;
      };

      header('RECEITAS', 22, 163, 74);
      data.receitas.forEach(l => row(l, 'rec'));
      subtotal('Total Receitas', data.total_receitas_atual, data.total_receitas_anterior, 187, 247, 208);

      y += 4;
      header('DESPESAS', 220, 38, 38);
      data.despesas.forEach(l => row(l, 'desp'));
      subtotal('Total Despesas', data.total_despesas_atual, data.total_despesas_anterior, 254, 226, 226);

      y += 4;
      const rBg = data.resultado_atual >= 0 ? [219, 234, 254] : [255, 237, 213];
      doc.setFillColor(rBg[0], rBg[1], rBg[2]);
      doc.rect(14, y, 269, 9, 'F');
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.text('RESULTADO LÍQUIDO', col[0] + 2, y + 6);
      const fmt2 = (v: number) => `R$ ${v.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
      doc.text(fmt2(data.resultado_atual), col[1], y + 6, { align: 'right' });
      doc.text(fmt2(data.resultado_anterior), col[2], y + 6, { align: 'right' });
      doc.text(this.variacaoPct(data.resultado_atual, data.resultado_anterior), col[3], y + 6, { align: 'right' });

      doc.save(`DRE_${empresa.replace(/\s/g, '_')}_${data.mes_referencia}.pdf`);
    });
  }
}
