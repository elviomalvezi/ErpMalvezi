import { Component, Input, OnChanges, SimpleChanges, inject, signal } from '@angular/core';
import { Observable } from 'rxjs';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';

import type { PatrimonioAnexo } from '../../../core/models';

@Component({
  selector: 'app-anexos-panel',
  standalone: true,
  providers: [ConfirmationService, MessageService],
  imports: [ButtonModule, ConfirmPopupModule, ToastModule, TooltipModule],
  template: `
<p-toast />
<p-confirmpopup />

<div class="anexos-header">
  <span class="anexos-title">Anexos</span>
  @if (carregando()) {
    <i class="pi pi-spin pi-spinner" style="font-size:0.85rem;color:var(--p-surface-400)"></i>
  }
</div>

<div
  class="drop-zone"
  [class.drag-over]="dragOver()"
  (dragover)="$event.preventDefault(); dragOver.set(true)"
  (dragleave)="dragOver.set(false)"
  (drop)="onDrop($event)"
  (click)="fileInput.click()"
>
  <i class="pi pi-upload drop-icon"></i>
  <span class="drop-text">Arraste arquivos ou clique para selecionar</span>
  <span class="drop-hint">PDF, imagens, Word, Excel, CSV — máx. 10 MB</span>
</div>
<input #fileInput type="file" hidden multiple
  accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.doc,.docx,.xls,.xlsx,.csv,.txt"
  (change)="onFileInputChange($event)" />

@if (uploadando()) {
  <div class="upload-progress">
    <i class="pi pi-spin pi-spinner"></i>
    <span>Enviando...</span>
  </div>
}

<div class="anexos-list">
  @for (anexo of anexos(); track anexo.id) {
    <div class="anexo-item">
      <i [class]="'pi ' + mimeIcon(anexo.mime_type) + ' anexo-icon'"></i>
      <span class="anexo-nome" [title]="anexo.nome_original">{{ anexo.nome_original }}</span>
      <span class="anexo-tamanho">{{ formatBytes(anexo.tamanho) }}</span>
      <a [href]="downloadUrlFn(registroId!, anexo.id)" target="_blank" rel="noopener"
        class="p-button p-button-text p-button-sm p-button-rounded"
        pTooltip="Baixar" tooltipPosition="left">
        <i class="pi pi-download"></i>
      </a>
      <p-button icon="pi pi-trash" [text]="true" [rounded]="true" size="small"
        severity="danger" pTooltip="Excluir" tooltipPosition="left"
        (onClick)="confirmarExcluir($event, anexo.id)" />
    </div>
  } @empty {
    @if (!carregando()) {
      <span class="anexos-empty">Nenhum arquivo anexado.</span>
    }
  }
</div>
  `,
  styles: [`
    .anexos-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
    .anexos-title { font-size: 0.85rem; font-weight: 600; color: var(--p-surface-500); text-transform: uppercase; letter-spacing: 0.05em; }
    .drop-zone {
      border: 2px dashed var(--p-surface-300); border-radius: 8px;
      padding: 1.25rem 1rem; display: flex; flex-direction: column;
      align-items: center; gap: 0.2rem; cursor: pointer;
      transition: border-color 0.15s, background 0.15s; user-select: none;
    }
    .drop-zone:hover, .drop-zone.drag-over { border-color: var(--p-primary-color); background: var(--p-primary-50); }
    .drop-icon { font-size: 1.5rem; color: var(--p-surface-400); }
    .drop-zone.drag-over .drop-icon { color: var(--p-primary-color); }
    .drop-text { font-size: 0.875rem; color: var(--p-surface-600); }
    .drop-hint { font-size: 0.75rem; color: var(--p-surface-400); }
    .upload-progress { display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0; color: var(--p-surface-500); font-size: 0.85rem; }
    .anexos-list { margin-top: 0.625rem; display: flex; flex-direction: column; gap: 0.3rem; }
    .anexo-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.35rem 0.5rem; background: var(--p-surface-50); border-radius: 6px; border: 1px solid var(--p-surface-200); }
    .anexo-icon { font-size: 1rem; color: var(--p-surface-500); flex-shrink: 0; }
    .anexo-nome { flex: 1; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
    .anexo-tamanho { font-size: 0.75rem; color: var(--p-surface-400); white-space: nowrap; }
    .anexos-empty { font-size: 0.85rem; color: var(--p-surface-400); display: block; padding: 0.25rem 0; }
  `],
})
export class AnexosPanelComponent implements OnChanges {
  @Input() registroId: string | null = null;
  @Input() listarFn!: (id: string) => Observable<PatrimonioAnexo[]>;
  @Input() uploadFn!: (id: string, file: File) => Observable<PatrimonioAnexo>;
  @Input() deletarFn!: (id: string, anexoId: string) => Observable<void>;
  @Input() downloadUrlFn!: (id: string, anexoId: string) => string;

  private readonly confirmSvc = inject(ConfirmationService);
  private readonly messageSvc = inject(MessageService);

  protected readonly anexos = signal<PatrimonioAnexo[]>([]);
  protected readonly carregando = signal(false);
  protected readonly dragOver = signal(false);
  protected readonly uploadando = signal(false);

  ngOnChanges(changes: SimpleChanges): void {
    if ('registroId' in changes) {
      if (this.registroId) {
        this.carregar();
      } else {
        this.anexos.set([]);
      }
    }
  }

  private carregar(): void {
    if (!this.registroId) return;
    this.carregando.set(true);
    this.listarFn(this.registroId).subscribe({
      next: (data) => { this.anexos.set(data); this.carregando.set(false); },
      error: () => this.carregando.set(false),
    });
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(false);
    Array.from(event.dataTransfer?.files ?? []).forEach(f => this.upload(f));
  }

  protected onFileInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    Array.from(input.files ?? []).forEach(f => this.upload(f));
    input.value = '';
  }

  private upload(file: File): void {
    if (!this.registroId) return;
    this.uploadando.set(true);
    this.uploadFn(this.registroId, file).subscribe({
      next: (anexo) => {
        this.anexos.update(l => [...l, anexo]);
        this.uploadando.set(false);
        this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: `"${file.name}" anexado.` });
      },
      error: (err) => {
        this.uploadando.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro ao enviar arquivo.' });
      },
    });
  }

  protected confirmarExcluir(event: Event, anexoId: string): void {
    this.confirmSvc.confirm({
      target: event.target as EventTarget,
      message: 'Excluir este anexo?',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        if (!this.registroId) return;
        this.deletarFn(this.registroId, anexoId).subscribe({
          next: () => {
            this.anexos.update(l => l.filter(a => a.id !== anexoId));
            this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Anexo excluído.' });
          },
          error: (err) => this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: err?.error?.detail ?? 'Erro.' }),
        });
      },
    });
  }

  protected mimeIcon(mime: string): string {
    if (mime === 'application/pdf') return 'pi-file-pdf';
    if (mime.startsWith('image/')) return 'pi-image';
    if (mime.includes('spreadsheet') || mime.includes('excel') || mime === 'text/csv') return 'pi-file-excel';
    if (mime.includes('word')) return 'pi-file-word';
    return 'pi-file';
  }

  protected formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1_048_576).toFixed(1)} MB`;
  }
}
