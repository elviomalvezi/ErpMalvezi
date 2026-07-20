import { Injectable } from '@angular/core';
import { Lancamento } from '../models';

@Injectable({ providedIn: 'root' })
export class ExportacaoService {

  private brl(valor: number): string {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
  }

  private formatarData(data: string | null | undefined): string {
    if (!data) return '';
    const [y, m, d] = data.split('-');
    return `${d}/${m}/${y}`;
  }

  exportarExcel(lancamentos: Lancamento[], nomeArquivo = 'lancamentos'): void {
    import('xlsx').then(XLSX => {
      const rows = lancamentos.map(l => ({
        'Descrição': l.descricao,
        'Tipo': l.tipo === 'RECEITA' ? 'Receita' : 'Despesa',
        'Valor': l.valor,
        'Vencimento': this.formatarData(l.data_vencimento),
        'Competência': this.formatarData(l.data_competencia),
        'Status': l.status,
        'Pago em': this.formatarData(l.data_pagamento),
        'Valor Pago': l.valor_pago ?? '',
        'Observações': l.observacoes ?? '',
      }));

      const ws = XLSX.utils.json_to_sheet(rows);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Lançamentos');

      // Ajustar largura das colunas
      ws['!cols'] = [
        { wch: 40 }, { wch: 10 }, { wch: 14 }, { wch: 12 },
        { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 14 }, { wch: 30 },
      ];

      XLSX.writeFile(wb, `${nomeArquivo}.xlsx`);
    });
  }

  exportarPDF(lancamentos: Lancamento[], titulo: string, periodo: string): void {
    import('jspdf').then(({ default: jsPDF }) =>
      import('jspdf-autotable').then(() => {
        const doc = new jsPDF({ orientation: 'landscape' });

        doc.setFontSize(16);
        doc.text(titulo, 14, 18);
        doc.setFontSize(10);
        doc.setTextColor(120);
        doc.text(periodo, 14, 25);
        doc.setTextColor(0);

        const total_receitas = lancamentos
          .filter(l => l.tipo === 'RECEITA' && l.status === 'pago')
          .reduce((s, l) => s + Number(l.valor), 0);
        const total_despesas = lancamentos
          .filter(l => l.tipo === 'DESPESA' && l.status === 'pago')
          .reduce((s, l) => s + Number(l.valor), 0);

        (doc as any).autoTable({
          startY: 30,
          head: [['Descrição', 'Tipo', 'Vencimento', 'Status', 'Valor', 'Pago em', 'Valor Pago']],
          body: lancamentos.map(l => [
            l.descricao,
            l.tipo === 'RECEITA' ? 'Receita' : 'Despesa',
            this.formatarData(l.data_vencimento),
            l.status,
            this.brl(l.valor),
            this.formatarData(l.data_pagamento),
            l.valor_pago ? this.brl(l.valor_pago) : '-',
          ]),
          foot: [[
            { content: 'Totais realizados:', colSpan: 4, styles: { fontStyle: 'bold' } },
            '',
            { content: `Receitas: ${this.brl(total_receitas)}  |  Despesas: ${this.brl(total_despesas)}`, colSpan: 2, styles: { fontStyle: 'bold' } },
          ]],
          styles: { fontSize: 9 },
          headStyles: { fillColor: [99, 102, 241] },
          columnStyles: { 4: { halign: 'right' }, 6: { halign: 'right' } },
        });

        doc.save(`${titulo.toLowerCase().replace(/\s+/g, '_')}.pdf`);
      })
    );
  }
}
