import { Component, ViewChild, computed, effect, inject, signal, untracked } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators, FormsModule } from '@angular/forms';
import { UpperCasePipe, DatePipe } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { HttpClient } from '@angular/common/http';
import { ConfirmationService, MessageService, SortEvent } from 'primeng/api';
import { ButtonModule } from 'primeng/button';
import { ConfirmPopupModule } from 'primeng/confirmpopup';
import { DatePickerModule } from 'primeng/datepicker';
import { DialogModule } from 'primeng/dialog';
import { DividerModule } from 'primeng/divider';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { TextareaModule } from 'primeng/textarea';
import { ChipModule } from 'primeng/chip';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { Popover } from 'primeng/popover';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { CategoriaService } from '../../core/services/categoria.service';
import { ContatoService } from '../../core/services/contato.service';
import { ContaBancariaService } from '../../core/services/conta-bancaria.service';
import { LancamentoService } from '../../core/services/lancamento.service';
import { ExportacaoService } from '../../core/services/exportacao.service';
import { PatrimonioService } from '../../core/services/patrimonio.service';
import type {
  Lancamento,
  LancamentoAnexo,
  LancamentoCreate,
  LancamentoParceladoCreate,
  LancamentoRecorrenteCreate,
  LancamentoBaixaCreate,
  LancamentoUpdate,
  Categoria,
  Contato,
  ContaBancaria,
  Veiculo,
  Imovel,
} from '../../core/models';

type FiltroStatus = 'TODOS' | 'pendente' | 'pago' | 'cancelado' | 'nao_realizado';
type ModoDialog = 'simples' | 'parcelado' | 'recorrente';

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];

@Component({
  selector: 'app-lancamentos',
  standalone: true,
  providers: [ConfirmationService, MessageService],
  imports: [
    ReactiveFormsModule, FormsModule,
    ButtonModule, TableModule, DialogModule, TagModule, ToastModule,
    InputTextModule, InputNumberModule, SelectModule, DatePickerModule,
    TextareaModule, DividerModule, ConfirmPopupModule, TooltipModule, ChipModule,
    UpperCasePipe, DatePipe,
    Popover,
  ],
  template: `
<p-toast />
<p-confirmpopup />

@if (!empresaAtiva()) {
  <div class="sem-empresa">Selecione uma empresa para visualizar os lançamentos.</div>
} @else {
  <div class="page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">{{ titulo() }}</h1>
        <div class="month-nav">
          <p-button icon="pi pi-chevron-left" [text]="true" [rounded]="true" (onClick)="mesAnterior()" />
          <p-datepicker
            [ngModel]="mesAtual()"
            (onSelect)="mesAtual.set($event)"
            view="month"
            dateFormat="MM/yy"
            [readonlyInput]="true"
            [showIcon]="true"
            icon="pi pi-calendar"
            placeholder="Selecione o mês"
          />
          <p-button icon="pi pi-chevron-right" [text]="true" [rounded]="true" (onClick)="proximoMes()" />
        </div>
      </div>
      <div class="header-actions">
        <p-button icon="pi pi-file-excel" [text]="true" severity="success"
          pTooltip="Exportar Excel" tooltipPosition="bottom"
          (onClick)="exportarExcel()" [disabled]="listaFiltrada().length === 0" />
        <p-button icon="pi pi-file-pdf" [text]="true" severity="danger"
          pTooltip="Exportar PDF" tooltipPosition="bottom"
          (onClick)="exportarPDF()" [disabled]="listaFiltrada().length === 0" />
        <p-button label="Novo" icon="pi pi-plus" (onClick)="abrirCriar()" />
      </div>
    </div>

    <div class="status-bar">
      @for (opt of statusOpts; track opt.value) {
        <p-button
          [label]="opt.label"
          [outlined]="filtroStatus() !== opt.value"
          size="small"
          (onClick)="filtroStatus.set(opt.value)"
        />
      }
    </div>

    <div class="filtros-bar">
      <input pInputText class="filtro-busca"
        [ngModel]="filtroTexto()" (ngModelChange)="filtroTexto.set($event)"
        placeholder="Filtrar descrição, categoria, contato..." />
      <p-select [options]="categoriaOpts()" [ngModel]="filtroCategoria()" (ngModelChange)="filtroCategoria.set($event)"
        optionLabel="label" optionValue="value" [showClear]="true" placeholder="Categoria"
        [filter]="true" [style]="{ width: '190px' }" appendTo="body" />
      <p-select [options]="contatoOpts()" [ngModel]="filtroContato()" (ngModelChange)="filtroContato.set($event)"
        optionLabel="label" optionValue="value" [showClear]="true"
        [placeholder]="tipo() === 'DESPESA' ? 'Fornecedor' : 'Cliente'"
        [filter]="true" [style]="{ width: '190px' }" appendTo="body" />
      <p-inputnumber [ngModel]="filtroValorMin()" (ngModelChange)="filtroValorMin.set($event)"
        mode="currency" currency="BRL" locale="pt-BR" placeholder="Valor mín" [style]="{ width: '120px' }" />
      <p-inputnumber [ngModel]="filtroValorMax()" (ngModelChange)="filtroValorMax.set($event)"
        mode="currency" currency="BRL" locale="pt-BR" placeholder="Valor máx" [style]="{ width: '120px' }" />
      <p-datepicker [ngModel]="filtroDataIni()" (ngModelChange)="filtroDataIni.set($event)"
        dateFormat="dd/mm/yy" placeholder="Venc. de" [showButtonBar]="true" [style]="{ width: '125px' }" appendTo="body" />
      <p-datepicker [ngModel]="filtroDataFim()" (ngModelChange)="filtroDataFim.set($event)"
        dateFormat="dd/mm/yy" placeholder="Venc. até" [showButtonBar]="true" [style]="{ width: '125px' }" appendTo="body" />
      @if (temFiltrosAtivos()) {
        <p-button label="Limpar" icon="pi pi-filter-slash" severity="secondary" [text]="true" size="small" (onClick)="limparFiltros()" />
      }
    </div>

    <p-table
      [value]="listaFiltrada()"
      [loading]="loading()"
      [paginator]="true"
      [rows]="20"
      [rowsPerPageOptions]="[10, 20, 50]"
      [showCurrentPageReport]="true"
      currentPageReportTemplate="{first}–{last} de {totalRecords}"
      [customSort]="true"
      (sortFunction)="customSort($event)"
      size="small"
    >
      <ng-template pTemplate="header">
        <tr>
          <th pSortableColumn="descricao">Descrição <p-sortIcon field="descricao" /></th>
          <th>Categoria</th>
          <th>{{ tipo() === 'DESPESA' ? 'Fornecedor' : 'Cliente' }}</th>
          <th pSortableColumn="data_vencimento">Vencimento <p-sortIcon field="data_vencimento" /></th>
          <th class="col-right" pSortableColumn="valor">Valor <p-sortIcon field="valor" /></th>
          <th class="col-right" pSortableColumn="valor_pago">Pago <p-sortIcon field="valor_pago" /></th>
          <th pSortableColumn="status">Status <p-sortIcon field="status" /></th>
          <th style="width:7rem"></th>
        </tr>
      </ng-template>
      <ng-template pTemplate="body" let-lct>
        <tr [class.row-pago]="lct.status === 'pago'" [class.row-cancelado]="lct.status === 'cancelado'">
          <td>
            <span>{{ lct.descricao }}</span>
            @if (lct.numero_parcela) {
              <span class="parcela-badge">{{ lct.numero_parcela }}/{{ lct.total_parcelas }}</span>
            }
          </td>
          <td>{{ categoriaMap().get(lct.categoria_id) ?? '—' }}</td>
          <td>{{ contatoMap().get(lct.contato_id) ?? '—' }}</td>
          <td>{{ formatDate(lct.data_vencimento) }}</td>
          <td class="col-right">{{ formatMoeda(lct.valor) }}</td>
          <td class="col-right">{{ formatMoeda(lct.valor_pago) }}</td>
          <td>
            <p-tag [value]="statusLabel(lct.status)" [severity]="statusSeverity(lct.status)" />
          </td>
          <td>
            <div class="acoes">
              @if (lct.status === 'pendente') {
                <p-button
                  icon="pi pi-check"
                  [text]="true" [rounded]="true" size="small"
                  pTooltip="Registrar pagamento" tooltipPosition="left"
                  (onClick)="abrirBaixa(lct)"
                />
                <p-button
                  icon="pi pi-calendar-times"
                  [text]="true" [rounded]="true" size="small"
                  severity="warn"
                  pTooltip="Marcar como não realizado (previsto que não ocorreu)" tooltipPosition="left"
                  (onClick)="confirmarNaoRealizado($event, lct.id)"
                />
                <p-button
                  icon="pi pi-pencil"
                  [text]="true" [rounded]="true" size="small"
                  pTooltip="Editar" tooltipPosition="left"
                  (onClick)="abrirEditar(lct)"
                />
              }
              @if (lct.imovel_id || lct.veiculo_id) {
                <p-button
                  icon="pi pi-search"
                  [text]="true" [rounded]="true" size="small"
                  severity="info"
                  pTooltip="Consultar lançamentos deste patrimônio" tooltipPosition="left"
                  (onClick)="abrirConsultaPatrimonio(lct)"
                />
              }
              @if (lct.status === 'nao_realizado') {
                <p-button
                  icon="pi pi-replay"
                  [text]="true" [rounded]="true" size="small"
                  severity="warn"
                  pTooltip="Voltar para previsto" tooltipPosition="left"
                  (onClick)="reverterPrevisto(lct)"
                />
              }
              @if (lct.tem_anexo) {
                <p-button
                  icon="pi pi-paperclip"
                  [text]="true" [rounded]="true" size="small"
                  severity="secondary"
                  pTooltip="Ver anexos" tooltipPosition="left"
                  (onClick)="abrirAnexosPopup($event, lct)"
                />
              }
              <p-button
                icon="pi pi-copy"
                [text]="true" [rounded]="true" size="small"
                severity="secondary"
                pTooltip="Duplicar" tooltipPosition="left"
                (onClick)="duplicar(lct)"
              />
              <p-button
                icon="pi pi-history"
                [text]="true" [rounded]="true" size="small"
                severity="secondary"
                pTooltip="Histórico" tooltipPosition="left"
                (onClick)="abrirHistorico(lct)"
              />
              @if (lct.status !== 'cancelado') {
                <p-button
                  icon="pi pi-times"
                  [text]="true" [rounded]="true" size="small"
                  severity="danger"
                  pTooltip="Cancelar" tooltipPosition="left"
                  (onClick)="confirmarCancelamento($event, lct.id)"
                />
              }
            </div>
          </td>
        </tr>
      </ng-template>
      <ng-template pTemplate="emptymessage">
        <tr>
          <td colspan="8" class="empty-msg">Nenhum lançamento encontrado neste período.</td>
        </tr>
      </ng-template>
    </p-table>
  </div>
}

<!-- Dialog Criar / Editar -->
<p-dialog
  [header]="dialogTitulo()"
  [visible]="dialogVisivel()"
  (visibleChange)="dialogVisivel.set($event)"
  [modal]="true"
  [style]="{width: '640px'}"
  [closeOnEscape]="true"
>
  <form [formGroup]="form" (ngSubmit)="salvar()">
    @if (!editandoId()) {
      <div class="modo-selector">
        @for (m of modoOpts; track m.value) {
          <p-button
            [label]="m.label"
            [outlined]="modoDialog() !== m.value"
            size="small"
            type="button"
            (onClick)="modoDialog.set(m.value)"
          />
        }
      </div>
      <p-divider />
    }

    <div class="form-grid">
      <div class="field full">
        <label>Descrição *</label>
        <input pInputText formControlName="descricao" placeholder="Ex: Aluguel escritório" class="w-full" />
      </div>

      @if (modoDialog() === 'simples' || modoDialog() === 'recorrente' || editandoId()) {
        <div class="field">
          <label>Valor *</label>
          <p-inputNumber
            formControlName="valor"
            mode="decimal"
            [minFractionDigits]="2"
            [maxFractionDigits]="2"
            [min]="0.01"
            locale="pt-BR"
            class="w-full"
          />
        </div>
      }

      @if (modoDialog() === 'parcelado' && !editandoId()) {
        <div class="field">
          <label>Valor Total *</label>
          <p-inputNumber
            formControlName="valor_total"
            mode="decimal"
            [minFractionDigits]="2"
            [maxFractionDigits]="2"
            [min]="0.01"
            locale="pt-BR"
            class="w-full"
          />
        </div>
        <div class="field">
          <label>Nº de Parcelas *</label>
          <p-inputNumber formControlName="parcelas" [min]="2" [max]="360" [useGrouping]="false" class="w-full" />
        </div>
      }

      @if (modoDialog() === 'simples' || editandoId()) {
        <div class="field">
          <label>Data Competência *</label>
          <p-datepicker formControlName="data_competencia" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
        <div class="field">
          <label>Data Vencimento *</label>
          <p-datepicker formControlName="data_vencimento" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
      }

      @if ((modoDialog() === 'parcelado' || modoDialog() === 'recorrente') && !editandoId()) {
        <div class="field">
          <label>1ª Competência *</label>
          <p-datepicker formControlName="data_primeira_competencia" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
        <div class="field">
          <label>1º Vencimento *</label>
          <p-datepicker formControlName="data_primeiro_vencimento" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
        </div>
      }

      @if (modoDialog() === 'recorrente' && !editandoId()) {
        <div class="field">
          <label>Frequência *</label>
          <p-select
            formControlName="frequencia"
            [options]="frequenciaOpts"
            optionLabel="label"
            optionValue="value"
            placeholder="Selecione"
            class="w-full"
          />
        </div>
        <div class="field">
          <label>Quantidade *</label>
          <p-inputNumber formControlName="quantidade" [min]="2" [max]="120" [useGrouping]="false" class="w-full" />
        </div>
      }

      <div class="field">
        <label>Categoria</label>
        <p-select
          formControlName="categoria_id"
          [options]="categoriaOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          filterPlaceholder="Buscar categoria..."
          appendTo="body"
          placeholder="— Sem categoria —"
          [showClear]="true"
          class="w-full"
        />
      </div>

      <div class="field">
        <label>{{ tipo() === 'DESPESA' ? 'Fornecedor' : 'Cliente' }}</label>
        <p-select
          formControlName="contato_id"
          [options]="contatoOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          filterPlaceholder="Buscar..."
          appendTo="body"
          placeholder="— Sem contato —"
          [showClear]="true"
          class="w-full"
        />
      </div>

      <div class="field full">
        <label>Conta Bancária</label>
        <p-select
          formControlName="conta_bancaria_id"
          [options]="contaOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          filterPlaceholder="Buscar conta..."
          appendTo="body"
          placeholder="— Sem conta —"
          [showClear]="true"
          class="w-full"
        />
      </div>

      <div class="field full">
        <label>Observações</label>
        <textarea pTextarea formControlName="observacoes" rows="2" class="w-full" placeholder="Opcional"></textarea>
      </div>

      @if (isExigirVeiculo()) {
        <div class="field full">
          <label>Veículo <small style="font-weight:400;color:var(--p-red-400)">* obrigatório</small></label>
          <p-select
            formControlName="veiculo_id"
            [options]="veiculoOpts()"
            optionLabel="label"
            optionValue="value"
            [filter]="true"
            filterPlaceholder="Buscar veículo..."
            appendTo="body"
            placeholder="— Selecione o veículo —"
            class="w-full"
          />
        </div>
      }

      @if (isExigirImovel()) {
        <div class="field full">
          <label>Imóvel <small style="font-weight:400;color:var(--p-red-400)">* obrigatório</small></label>
          <p-select
            formControlName="imovel_id"
            [options]="imovelOpts()"
            optionLabel="label"
            optionValue="value"
            [filter]="true"
            filterPlaceholder="Buscar imóvel..."
            appendTo="body"
            placeholder="— Selecione o imóvel —"
            class="w-full"
          />
        </div>
      }

      <div class="field full">
        <label>Tags <small style="font-weight:400;color:var(--p-surface-400)">(Enter para adicionar)</small></label>
        <div class="tags-input-wrap">
          @for (tag of form.get('tags')?.value || []; track tag) {
            <p-chip [label]="tag" [removable]="true" (onRemove)="removerTag(tag)" />
          }
          <input class="tag-input" placeholder="Nova tag..." (keydown.enter)="adicionarTag($event)" (keydown.comma)="adicionarTag($event)" />
        </div>
      </div>
    </div>

    @if (editandoId()) {
      <p-divider />
      <div class="anexos-section">
        <div class="anexos-header">
          <span class="anexos-title">Anexos</span>
          @if (carregandoAnexos()) {
            <i class="pi pi-spin pi-spinner" style="font-size:0.85rem; color:var(--p-surface-400)"></i>
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
              <button class="p-button p-button-text p-button-sm p-button-rounded"
                pTooltip="Baixar" tooltipPosition="left"
                (click)="baixarAnexo(anexo)">
                <i class="pi pi-download"></i>
              </button>
              <p-button icon="pi pi-trash" [text]="true" [rounded]="true" size="small"
                severity="danger" pTooltip="Excluir" tooltipPosition="left"
                (onClick)="confirmarExcluirAnexo($event, anexo.id)" />
            </div>
          } @empty {
            <span class="anexos-empty">Nenhum arquivo anexado.</span>
          }
        </div>
      </div>
    }

    <div class="dialog-footer">
      <p-button label="Cancelar" [outlined]="true" type="button" (onClick)="fecharDialog()" />
      <p-button [label]="editandoId() ? 'Salvar' : 'Criar'" type="submit" [loading]="salvando()" />
    </div>
  </form>
</p-dialog>

<!-- Dialog Registrar Pagamento -->
<p-dialog
  header="Registrar Pagamento"
  [visible]="baixaDialogVisivel()"
  (visibleChange)="baixaDialogVisivel.set($event)"
  [modal]="true"
  [style]="{width: '420px'}"
>
  <form [formGroup]="baixaForm" (ngSubmit)="registrarBaixa()">
    <div class="form-grid">
      <div class="field">
        <label>Valor Pago *</label>
        <p-inputNumber
          formControlName="valor_pago"
          mode="decimal"
          [minFractionDigits]="2"
          [maxFractionDigits]="2"
          [min]="0.01"
          locale="pt-BR"
          class="w-full"
        />
      </div>
      <div class="field">
        <label>Data Pagamento *</label>
        <p-datepicker formControlName="data_pagamento" dateFormat="dd/mm/yy" [showIcon]="true" class="w-full" />
      </div>
      <div class="field full">
        <label>Conta Bancária *</label>
        <p-select
          formControlName="conta_bancaria_id"
          [options]="contaOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          filterPlaceholder="Buscar conta..."
          appendTo="body"
          placeholder="Selecione a conta"
          class="w-full"
        />
      </div>
      <div class="field full">
        <label>Categoria *</label>
        <p-select
          formControlName="categoria_id"
          [options]="categoriaOpts()"
          optionLabel="label"
          optionValue="value"
          [filter]="true"
          filterPlaceholder="Buscar categoria..."
          appendTo="body"
          placeholder="Selecione a categoria"
          class="w-full"
        />
      </div>
    </div>
    <div class="dialog-footer">
      <p-button label="Cancelar" [outlined]="true" type="button" (onClick)="baixaDialogVisivel.set(false)" />
      <p-button label="Registrar" type="submit" [loading]="salvando()" severity="success" [disabled]="baixaForm.invalid" />
    </div>
  </form>
</p-dialog>

<!-- Popover de Anexos (visualização rápida sem abrir o formulário) -->
<p-popover #opAnexo>
  <div class="popup-anexos">
    @if (carregandoAnexosPopup()) {
      <div class="popup-loading"><i class="pi pi-spin pi-spinner"></i></div>
    } @else if (anexosPopup().length === 0) {
      <span class="popup-vazio">Nenhum anexo encontrado.</span>
    } @else {
      @for (anexo of anexosPopup(); track anexo.id) {
        <div class="popup-item">
          <i [class]="'pi ' + mimeIcon(anexo.mime_type) + ' popup-item-icon'"></i>
          <span class="popup-item-nome" [title]="anexo.nome_original">{{ anexo.nome_original }}</span>
          <span class="popup-item-size">{{ formatBytes(anexo.tamanho) }}</span>
          <button class="popup-btn" pTooltip="Visualizar" tooltipPosition="left"
                  (click)="visualizarAnexo(anexo)">
            <i class="pi pi-eye"></i>
          </button>
          <button class="popup-btn" pTooltip="Baixar" tooltipPosition="left"
                  (click)="baixarAnexo(anexo)">
            <i class="pi pi-download"></i>
          </button>
        </div>
      }
    }
  </div>
</p-popover>

<!-- Dialog Histórico de Alterações -->
<p-dialog header="Histórico de Alterações" [(visible)]="historicoDialog"
  [modal]="true" [style]="{ width: '680px' }" [draggable]="true">
  @if (carregandoHistorico()) {
    <div style="text-align:center;padding:2rem"><i class="pi pi-spin pi-spinner" style="font-size:2rem"></i></div>
  } @else if (historicoItens().length === 0) {
    <p style="color:var(--p-surface-400);text-align:center;padding:2rem">Nenhum registro de alteração encontrado.</p>
  } @else {
    <div class="historico-lista">
      @for (h of historicoItens(); track h.id) {
        <div class="historico-item">
          <div class="historico-header">
            <span class="historico-acao" [class]="'acao-' + h.acao">{{ h.acao | uppercase }}</span>
            <span class="historico-data">{{ h.criado_em | date:'dd/MM/yyyy HH:mm' }}</span>
          </div>
          @if (h.valor_novo && h.acao !== 'delete') {
            <div class="historico-campos">
              @for (campo of objectEntries(h.valor_novo); track campo[0]) {
                @if (campo[1] !== null && campo[1] !== undefined) {
                  <div class="campo-linha">
                    <span class="campo-nome">{{ campo[0] }}</span>
                    <span class="campo-valor">
                      @if (h.valor_anterior && h.valor_anterior[campo[0]] !== campo[1]) {
                        <span class="valor-antes">{{ h.valor_anterior[campo[0]] }}</span>
                        <i class="pi pi-arrow-right" style="font-size:0.7rem"></i>
                      }
                      {{ campo[1] }}
                    </span>
                  </div>
                }
              }
            </div>
          }
        </div>
      }
    </div>
  }
  <ng-template pTemplate="footer">
    <p-button label="Fechar" severity="secondary" (onClick)="historicoDialog.set(false)" />
  </ng-template>
</p-dialog>

<!-- Dialog Consulta de Lançamentos do Patrimônio -->
<p-dialog [header]="consultaTitulo()" [(visible)]="consultaDialog"
  [modal]="true" [style]="{ width: '820px' }" [draggable]="true">
  @if (consultaLoading()) {
    <div style="text-align:center;padding:2rem"><i class="pi pi-spin pi-spinner" style="font-size:2rem"></i></div>
  } @else if (consultaLancamentos().length === 0) {
    <p style="color:var(--p-surface-400);text-align:center;padding:2rem">Nenhum lançamento vinculado a este patrimônio.</p>
  } @else {
    <p-table [value]="consultaLancamentos()" class="p-datatable-sm" [scrollable]="true" scrollHeight="420px">
      <ng-template pTemplate="header">
        <tr>
          <th>Vencimento</th>
          <th>Descrição</th>
          <th>Tipo</th>
          <th style="text-align:right">Valor</th>
          <th>Status</th>
        </tr>
      </ng-template>
      <ng-template pTemplate="body" let-l>
        <tr>
          <td>{{ formatDate(l.data_vencimento) }}</td>
          <td>{{ l.descricao }}</td>
          <td>
            <p-tag [value]="l.tipo === 'RECEITA' ? 'Receita' : 'Despesa'"
              [severity]="l.tipo === 'RECEITA' ? 'success' : 'danger'" />
          </td>
          <td style="text-align:right">{{ formatMoeda(l.valor) }}</td>
          <td><p-tag [value]="statusLabel(l.status)" [severity]="statusSeverity(l.status)" /></td>
        </tr>
      </ng-template>
      <ng-template pTemplate="footer">
        <tr>
          <td colspan="3" style="text-align:right;font-weight:600">Total</td>
          <td style="text-align:right;font-weight:600">{{ formatMoeda(consultaTotal()) }}</td>
          <td></td>
        </tr>
      </ng-template>
    </p-table>
  }
  <ng-template pTemplate="footer">
    <p-button label="Fechar" severity="secondary" (onClick)="consultaDialog.set(false)" />
  </ng-template>
</p-dialog>
  `,
  styles: [`
    .sem-empresa { color: var(--p-surface-500); padding: 2rem; }
    .page { display: flex; flex-direction: column; gap: 1rem; }
    .page-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
    .header-left { display: flex; align-items: center; gap: 1.5rem; }
    .header-actions { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .page-title { margin: 0; font-size: 1.5rem; font-weight: 700; }
    .month-nav { display: flex; align-items: center; gap: 0.25rem; }
    .month-label { font-size: 1rem; font-weight: 600; min-width: 11rem; text-align: center; }
    .status-bar { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .filtros-bar {
      display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center;
      margin-top: 0.75rem; padding: 0.5rem 0;
    }
    .filtro-busca { min-width: 240px; flex: 1 1 240px; max-width: 320px; }
    .col-right { text-align: right; }
    .acoes { display: flex; gap: 0.125rem; justify-content: flex-end; }
    .parcela-badge { margin-left: 0.4rem; font-size: 0.72rem; color: var(--p-surface-500); background: var(--p-surface-100); padding: 0.1rem 0.35rem; border-radius: 999px; }
    .row-pago td { opacity: 0.7; }
    .row-cancelado td { opacity: 0.45; text-decoration: line-through; }
    .empty-msg { text-align: center; padding: 2rem; color: var(--p-surface-500); }
    .modo-selector { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; }
    .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem 1.5rem; }
    .field { display: flex; flex-direction: column; gap: 0.25rem; }
    .tags-input-wrap { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; padding: 0.4rem 0.6rem; border: 1px solid var(--p-surface-300); border-radius: 6px; min-height: 38px; background: var(--p-surface-0); }
    .tag-input { border: none; outline: none; background: transparent; font-size: 0.875rem; min-width: 120px; flex: 1; color: var(--p-surface-700); }
    .field.full { grid-column: 1 / -1; }
    label { font-size: 0.875rem; font-weight: 500; }
    .dialog-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--p-surface-200); }
    .historico-lista { display: flex; flex-direction: column; gap: 0.75rem; max-height: 400px; overflow-y: auto; }
    .historico-item { border: 1px solid var(--p-surface-200); border-radius: 8px; overflow: hidden; }
    .historico-header { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.75rem; background: var(--p-surface-50); }
    .historico-acao { font-size: 0.75rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; }
    .acao-insert { background: var(--p-green-100); color: var(--p-green-700); }
    .acao-update { background: var(--p-blue-100); color: var(--p-blue-700); }
    .acao-delete { background: var(--p-red-100); color: var(--p-red-700); }
    .historico-data { font-size: 0.8rem; color: var(--p-surface-500); }
    .historico-campos { padding: 0.5rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
    .campo-linha { display: flex; gap: 0.5rem; font-size: 0.8rem; }
    .campo-nome { color: var(--p-surface-500); min-width: 120px; font-weight: 500; }
    .campo-valor { display: flex; align-items: center; gap: 0.3rem; flex: 1; }
    .valor-antes { text-decoration: line-through; color: var(--p-red-400); }
    :host ::ng-deep .w-full .p-inputnumber,
    :host ::ng-deep .p-select.w-full,
    :host ::ng-deep .p-datepicker.w-full { width: 100%; }
    .anexos-section { margin-top: 0.25rem; }
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
    .popup-anexos { min-width: 320px; max-width: 420px; display: flex; flex-direction: column; gap: 0.25rem; }
    .popup-loading { padding: 0.75rem 0; text-align: center; color: var(--p-surface-400); }
    .popup-vazio { font-size: 0.85rem; color: var(--p-surface-400); padding: 0.25rem 0; }
    .popup-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.3rem; border-radius: 6px; }
    .popup-item:hover { background: var(--p-surface-50); }
    .popup-item-icon { font-size: 1rem; color: var(--p-surface-500); flex-shrink: 0; }
    .popup-item-nome { flex: 1; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
    .popup-item-size { font-size: 0.75rem; color: var(--p-surface-400); white-space: nowrap; flex-shrink: 0; }
    .popup-btn { display: flex; align-items: center; justify-content: center; width: 1.75rem; height: 1.75rem; border-radius: 50%; color: var(--p-surface-500); text-decoration: none; flex-shrink: 0; }
    .popup-btn:hover { background: var(--p-surface-100); color: var(--p-primary-color); }
    .popup-btn .pi { font-size: 0.85rem; }
  `],
})
export class LancamentosComponent {
  @ViewChild('opAnexo') private readonly opAnexo!: Popover;

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly svc = inject(LancamentoService);
  private readonly categoriaSvc = inject(CategoriaService);
  private readonly contatoSvc = inject(ContatoService);
  private readonly contaSvc = inject(ContaBancariaService);
  private readonly confirmSvc = inject(ConfirmationService);
  private readonly messageSvc = inject(MessageService);
  private readonly exportSvc = inject(ExportacaoService);
  private readonly patrimonioSvc = inject(PatrimonioService);
  private readonly http = inject(HttpClient);
  protected readonly empresaStore = inject(EmpresaStore);

  protected readonly tipo = signal<'RECEITA' | 'DESPESA'>('DESPESA');
  protected readonly empresaAtiva = computed(() => this.empresaStore.empresaAtiva());
  protected readonly titulo = computed(() => this.tipo() === 'RECEITA' ? 'Contas a Receber' : 'Contas a Pagar');

  protected readonly mesAtual = signal(new Date());
  protected readonly mesTitulo = computed(() => {
    const d = this.mesAtual();
    return `${MESES[d.getMonth()]} / ${d.getFullYear()}`;
  });

  protected readonly filtroStatus = signal<FiltroStatus>('TODOS');
  protected readonly lista = signal<Lancamento[]>([]);
  private readonly abrirIdPendente = signal<string | null>(null);
  protected readonly loading = signal(false);
  protected readonly salvando = signal(false);

  protected readonly categorias = signal<Categoria[]>([]);
  protected readonly contatos = signal<Contato[]>([]);
  protected readonly contas = signal<ContaBancaria[]>([]);
  protected readonly veiculos = signal<Veiculo[]>([]);
  protected readonly imoveis = signal<Imovel[]>([]);
  private readonly categoriaSelecionada = signal<Categoria | null>(null);

  protected readonly categoriaMap = computed(() =>
    new Map(this.categorias().map(c => [c.id, c.nome]))
  );
  protected readonly contatoMap = computed(() =>
    new Map(this.contatos().map(c => [c.id, c.nome_principal]))
  );

  protected readonly categoriaOpts = computed(() =>
    this.categorias()
      .filter(c => c.ativa && c.tipo === this.tipo())
      .map(c => ({
        label: (c.nivel > 1 ? '  '.repeat(c.nivel - 1) + '↳ ' : '') + c.nome,
        value: c.id,
      }))
  );
  protected readonly contatoOpts = computed(() =>
    this.contatos().filter(c => c.ativa).map(c => ({ label: c.nome_principal, value: c.id }))
  );
  protected readonly contaOpts = computed(() =>
    this.contas().filter(c => c.ativa).map(c => ({ label: c.nome, value: c.id }))
  );
  protected readonly veiculoOpts = computed(() =>
    this.veiculos().filter(v => v.ativo).map(v => ({ label: `${v.marca} ${v.modelo} ${v.placa ? '(' + v.placa + ')' : ''}`.trim(), value: v.id }))
  );
  protected readonly imovelOpts = computed(() =>
    this.imoveis().filter(i => i.ativo).map(i => ({ label: i.descricao + (i.cidade ? ' — ' + i.cidade : ''), value: i.id }))
  );
  protected readonly isExigirVeiculo = computed(() => this.categoriaSelecionada()?.exigir_veiculo ?? false);
  protected readonly isExigirImovel = computed(() => this.categoriaSelecionada()?.exigir_imovel ?? false);
  protected readonly isMulta = this.isExigirVeiculo;
  protected readonly isIptu = this.isExigirImovel;

  // ── Filtros internos da grid ────────────────────────────────────────────────
  protected readonly filtroTexto = signal('');
  protected readonly filtroCategoria = signal<string | null>(null);
  protected readonly filtroContato = signal<string | null>(null);
  protected readonly filtroValorMin = signal<number | null>(null);
  protected readonly filtroValorMax = signal<number | null>(null);
  protected readonly filtroDataIni = signal<Date | null>(null);
  protected readonly filtroDataFim = signal<Date | null>(null);

  protected readonly temFiltrosAtivos = computed(() =>
    !!this.filtroTexto().trim() ||
    this.filtroCategoria() !== null ||
    this.filtroContato() !== null ||
    this.filtroValorMin() !== null ||
    this.filtroValorMax() !== null ||
    this.filtroDataIni() !== null ||
    this.filtroDataFim() !== null
  );

  protected limparFiltros(): void {
    this.filtroTexto.set('');
    this.filtroCategoria.set(null);
    this.filtroContato.set(null);
    this.filtroValorMin.set(null);
    this.filtroValorMax.set(null);
    this.filtroDataIni.set(null);
    this.filtroDataFim.set(null);
  }

  protected readonly listaFiltrada = computed(() => {
    const status = this.filtroStatus();
    const texto = this.filtroTexto().trim().toLowerCase();
    const cat = this.filtroCategoria();
    const contato = this.filtroContato();
    const vmin = this.filtroValorMin();
    const vmax = this.filtroValorMax();
    const dini = this.filtroDataIni();
    const dfim = this.filtroDataFim();
    const catMap = this.categoriaMap();
    const contMap = this.contatoMap();
    const dataIniStr = dini ? this.toISODate(dini) : null;
    const dataFimStr = dfim ? this.toISODate(dfim) : null;

    return this.lista().filter(l => {
      if (status !== 'TODOS' && l.status !== status) return false;
      if (cat && l.categoria_id !== cat) return false;
      if (contato && l.contato_id !== contato) return false;
      const valor = Number(l.valor);
      if (vmin != null && valor < vmin) return false;
      if (vmax != null && valor > vmax) return false;
      if (dataIniStr && l.data_vencimento < dataIniStr) return false;
      if (dataFimStr && l.data_vencimento > dataFimStr) return false;
      if (texto) {
        const desc = (l.descricao ?? '').toLowerCase();
        const cn = (l.categoria_id ? catMap.get(l.categoria_id) ?? '' : '').toLowerCase();
        const ct = (l.contato_id ? contMap.get(l.contato_id) ?? '' : '').toLowerCase();
        if (!desc.includes(texto) && !cn.includes(texto) && !ct.includes(texto)) return false;
      }
      return true;
    });
  });

  // Dialog state
  protected readonly dialogVisivel = signal(false);
  protected readonly editandoId = signal<string | null>(null);
  protected readonly modoDialog = signal<ModoDialog>('simples');
  protected readonly dialogTitulo = computed(() =>
    this.editandoId() ? `Editar ${this.titulo()}` : `Novo ${this.titulo()}`
  );

  // Baixa state
  protected readonly baixaDialogVisivel = signal(false);
  protected readonly baixandoId = signal<string | null>(null);

  // Anexos state (formulário de edição)
  protected readonly anexos = signal<LancamentoAnexo[]>([]);
  protected readonly carregandoAnexos = signal(false);
  protected readonly dragOver = signal(false);
  protected readonly uploadando = signal(false);

  // Anexos popup (visualização rápida na listagem)
  protected readonly anexosPopup = signal<LancamentoAnexo[]>([]);
  protected readonly carregandoAnexosPopup = signal(false);

  readonly statusOpts: { label: string; value: FiltroStatus }[] = [
    { label: 'Todos', value: 'TODOS' },
    { label: 'Pendente', value: 'pendente' },
    { label: 'Pago', value: 'pago' },
    { label: 'Não realizado', value: 'nao_realizado' },
    { label: 'Cancelado', value: 'cancelado' },
  ];

  readonly modoOpts: { label: string; value: ModoDialog }[] = [
    { label: 'Simples', value: 'simples' },
    { label: 'Parcelado', value: 'parcelado' },
    { label: 'Recorrente', value: 'recorrente' },
  ];

  readonly frequenciaOpts = [
    { label: 'Semanal', value: 'semanal' },
    { label: 'Quinzenal', value: 'quinzenal' },
    { label: 'Mensal', value: 'mensal' },
    { label: 'Anual', value: 'anual' },
  ];

  readonly form = this.fb.group({
    descricao: ['', [Validators.required, Validators.minLength(2)]],
    valor: [null as number | null],
    valor_total: [null as number | null],
    parcelas: [2 as number | null],
    frequencia: [null as string | null],
    quantidade: [12 as number | null],
    data_competencia: [null as Date | null],
    data_vencimento: [null as Date | null],
    data_primeira_competencia: [null as Date | null],
    data_primeiro_vencimento: [null as Date | null],
    categoria_id: [null as string | null],
    contato_id: [null as string | null],
    conta_bancaria_id: [null as string | null],
    observacoes: [null as string | null],
    tags: [[] as string[]],
    veiculo_id: [null as string | null],
    imovel_id: [null as string | null],
  });

  readonly baixaForm = this.fb.group({
    valor_pago: [null as number | null, [Validators.required, Validators.min(0.01)]],
    data_pagamento: [new Date() as Date | null, Validators.required],
    conta_bancaria_id: [null as string | null, Validators.required],
    categoria_id: [null as string | null, Validators.required],
  });

  constructor() {
    const routeTipo = this.route.snapshot.data['tipo'] as string;
    this.tipo.set(routeTipo === 'receita' ? 'RECEITA' : 'DESPESA');

    effect(() => {
      const empresa = this.empresaStore.empresaAtiva();
      this.mesAtual();
      if (empresa) untracked(() => this.carregarDados());
    });

    effect(() => {
      if (this.empresaStore.empresaAtiva()) {
        untracked(() => {
          this.carregarCategorias();
          this.carregarContatos();
          this.carregarContas();
          this.carregarVeiculosImoveis();
        });
      }
    });

    this.form.get('categoria_id')!.valueChanges.pipe(takeUntilDestroyed()).subscribe(catId => {
      const cat = this.categorias().find(c => c.id === catId) ?? null;
      this.categoriaSelecionada.set(cat);
      if (!cat?.exigir_veiculo) this.form.get('veiculo_id')!.setValue(null, { emitEvent: false });
      if (!cat?.exigir_imovel) this.form.get('imovel_id')!.setValue(null, { emitEvent: false });
    });

    // Abre lançamento ao navegar pela busca global
    this.route.queryParams.pipe(takeUntilDestroyed()).subscribe(params => {
      const mes = params['mes'] as string | undefined;
      const abrirId = params['abrir'] as string | undefined;
      if (mes) {
        const [y, m] = mes.split('-').map(Number);
        this.mesAtual.set(new Date(y, m - 1, 1));
      }
      if (abrirId) this.abrirIdPendente.set(abrirId);
    });

    effect(() => {
      const lista = this.lista();
      const abrirId = this.abrirIdPendente();
      const loading = this.loading();
      if (!abrirId || loading) return;
      const lct = lista.find(l => l.id === abrirId);
      untracked(() => {
        if (lct) this.abrirEditar(lct);
        this.abrirIdPendente.set(null);
        void this.router.navigate([], { relativeTo: this.route, queryParams: {}, replaceUrl: true });
      });
    });
  }

  protected mesAnterior(): void {
    const d = this.mesAtual();
    this.mesAtual.set(new Date(d.getFullYear(), d.getMonth() - 1, 1));
  }

  protected proximoMes(): void {
    const d = this.mesAtual();
    this.mesAtual.set(new Date(d.getFullYear(), d.getMonth() + 1, 1));
  }

  private toISODate(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  protected carregarDados(): void {
    const empresa = this.empresaAtiva();
    if (!empresa) return;
    const d = this.mesAtual();
    const inicio = this.toISODate(new Date(d.getFullYear(), d.getMonth(), 1));
    const fim = this.toISODate(new Date(d.getFullYear(), d.getMonth() + 1, 0));
    this.loading.set(true);
    this.svc.listar({
      empresaId: empresa.id,
      tipo: this.tipo(),
      dataInicio: inicio,
      dataFim: fim,
      apenasAtivos: false,
    }).subscribe({
      next: (data) => { this.lista.set(data); this.loading.set(false); },
      error: () => {
        this.loading.set(false);
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar lançamentos.' });
      },
    });
  }

  private carregarCategorias(): void {
    this.categoriaSvc.listar(null, true).subscribe({
      next: (data) => this.categorias.set(data),
      error: () => {},
    });
  }

  private carregarContatos(): void {
    const empresa = this.empresaAtiva();
    this.contatoSvc.listar({ empresaId: empresa?.id, apenasAtivas: true }).subscribe({
      next: (data) => this.contatos.set(data),
      error: () => {},
    });
  }

  private carregarContas(): void {
    const empresa = this.empresaAtiva();
    this.contaSvc.listar({ empresaId: empresa?.id, apenasAtivas: true }).subscribe({
      next: (data) => this.contas.set(data),
      error: () => {},
    });
  }

  private carregarVeiculosImoveis(): void {
    const empresa = this.empresaAtiva();
    this.patrimonioSvc.listarVeiculos({ empresaId: empresa?.id, apenasAtivos: true }).subscribe({
      next: (data) => this.veiculos.set(data),
      error: () => {},
    });
    this.patrimonioSvc.listarImoveis({ empresaId: empresa?.id, apenasAtivos: true }).subscribe({
      next: (data) => this.imoveis.set(data),
      error: () => {},
    });
  }

  protected abrirCriar(): void {
    this.editandoId.set(null);
    this.modoDialog.set('simples');
    this.categoriaSelecionada.set(null);
    this.form.reset({
      descricao: '',
      valor: null,
      valor_total: null,
      parcelas: 2,
      frequencia: null,
      quantidade: 12,
      data_competencia: new Date(),
      data_vencimento: new Date(),
      data_primeira_competencia: new Date(),
      data_primeiro_vencimento: new Date(),
      categoria_id: null,
      contato_id: null,
      conta_bancaria_id: null,
      observacoes: null,
      tags: [],
      veiculo_id: null,
      imovel_id: null,
    });
    this.dialogVisivel.set(true);
  }

  protected abrirEditar(lct: Lancamento): void {
    this.editandoId.set(lct.id);
    this.modoDialog.set('simples');
    this.carregarAnexos(lct.id);
    const cat = this.categorias().find(c => c.id === lct.categoria_id) ?? null;
    this.categoriaSelecionada.set(cat);
    this.form.reset({
      descricao: lct.descricao,
      valor: Number(lct.valor),
      valor_total: null,
      parcelas: null,
      frequencia: null,
      quantidade: null,
      data_competencia: lct.data_competencia ? new Date(lct.data_competencia + 'T00:00:00') : null,
      data_vencimento: lct.data_vencimento ? new Date(lct.data_vencimento + 'T00:00:00') : null,
      data_primeira_competencia: null,
      data_primeiro_vencimento: null,
      categoria_id: lct.categoria_id,
      contato_id: lct.contato_id,
      conta_bancaria_id: lct.conta_bancaria_id,
      observacoes: lct.observacoes,
      tags: lct.tags ?? [],
      veiculo_id: lct.veiculo_id ?? null,
      imovel_id: lct.imovel_id ?? null,
    });
    this.dialogVisivel.set(true);
  }

  protected fecharDialog(): void {
    this.dialogVisivel.set(false);
    this.anexos.set([]);
  }

  protected salvar(): void {
    const empresa = this.empresaAtiva();
    if (!empresa) return;
    const v = this.form.value;
    const modo = this.modoDialog();
    const editandoId = this.editandoId();

    if (editandoId) {
      if (!v.descricao || v.descricao.length < 2) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Descrição é obrigatória.' });
        return;
      }
      const payload: LancamentoUpdate = {};
      payload.descricao = v.descricao;
      if (v.valor != null) payload.valor = v.valor;
      if (v.data_competencia) payload.data_competencia = this.toISODate(v.data_competencia);
      if (v.data_vencimento) payload.data_vencimento = this.toISODate(v.data_vencimento);
      payload.categoria_id = v.categoria_id ?? null;
      payload.contato_id = v.contato_id ?? null;
      payload.observacoes = v.observacoes ?? null;
      payload.tags = v.tags ?? [];
      payload.veiculo_id = this.isMulta() ? (v.veiculo_id ?? null) : null;
      payload.imovel_id = this.isIptu() ? (v.imovel_id ?? null) : null;

      this.salvando.set(true);
      this.svc.atualizar(editandoId, payload).subscribe({
        next: (updated) => {
          this.lista.update(lst => lst.map(l => l.id === updated.id ? updated : l));
          this.salvando.set(false);
          this.dialogVisivel.set(false);
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento atualizado.' });
        },
        error: (err) => {
          this.salvando.set(false);
          const detail = err?.error?.detail ?? 'Erro ao atualizar lançamento.';
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
        },
      });
      return;
    }

    if (!v.descricao || v.descricao.length < 2) {
      this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Descrição é obrigatória.' });
      return;
    }

    this.salvando.set(true);

    if (modo === 'simples') {
      if (!v.valor || !v.data_competencia || !v.data_vencimento) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha valor, competência e vencimento.' });
        this.salvando.set(false);
        return;
      }
      if (this.isExigirVeiculo() && !v.veiculo_id) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Esta categoria exige a seleção de um veículo.' });
        this.salvando.set(false);
        return;
      }
      if (this.isExigirImovel() && !v.imovel_id) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Esta categoria exige a seleção de um imóvel.' });
        this.salvando.set(false);
        return;
      }
      const payload: LancamentoCreate = {
        empresa_id: empresa.id,
        tipo: this.tipo(),
        descricao: v.descricao,
        valor: v.valor,
        data_competencia: this.toISODate(v.data_competencia),
        data_vencimento: this.toISODate(v.data_vencimento),
        categoria_id: v.categoria_id ?? null,
        contato_id: v.contato_id ?? null,
        conta_bancaria_id: v.conta_bancaria_id ?? null,
        observacoes: v.observacoes ?? null,
        tags: v.tags ?? [],
        veiculo_id: this.isMulta() ? (v.veiculo_id ?? null) : null,
        imovel_id: this.isIptu() ? (v.imovel_id ?? null) : null,
      };
      this.svc.criar(payload).subscribe({
        next: (lct) => {
          this.lista.update(lst => [...lst, lct]);
          this.salvando.set(false);
          this.dialogVisivel.set(false);
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento criado.' });
        },
        error: (err) => {
          this.salvando.set(false);
          const detail = err?.error?.detail ?? 'Erro ao criar lançamento.';
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
        },
      });

    } else if (modo === 'parcelado') {
      if (!v.valor_total || !v.parcelas || !v.data_primeira_competencia || !v.data_primeiro_vencimento) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha valor total, parcelas e datas.' });
        this.salvando.set(false);
        return;
      }
      const payload: LancamentoParceladoCreate = {
        empresa_id: empresa.id,
        tipo: this.tipo(),
        descricao: v.descricao,
        valor_total: v.valor_total,
        parcelas: v.parcelas,
        data_primeira_competencia: this.toISODate(v.data_primeira_competencia),
        data_primeiro_vencimento: this.toISODate(v.data_primeiro_vencimento),
        categoria_id: v.categoria_id ?? null,
        contato_id: v.contato_id ?? null,
        conta_bancaria_id: v.conta_bancaria_id ?? null,
        observacoes: v.observacoes ?? null,
        tags: v.tags ?? [],
        veiculo_id: this.isMulta() ? (v.veiculo_id ?? null) : null,
        imovel_id: this.isIptu() ? (v.imovel_id ?? null) : null,
      };
      this.svc.criarParcelado(payload).subscribe({
        next: (lancamentos) => {
          this.salvando.set(false);
          this.dialogVisivel.set(false);
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: `${lancamentos.length} parcelas criadas.` });
          this.carregarDados();
        },
        error: (err) => {
          this.salvando.set(false);
          const detail = err?.error?.detail ?? 'Erro ao criar parcelamento.';
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
        },
      });

    } else {
      if (!v.valor || !v.frequencia || !v.quantidade || !v.data_primeira_competencia || !v.data_primeiro_vencimento) {
        this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha todos os campos obrigatórios.' });
        this.salvando.set(false);
        return;
      }
      const payload: LancamentoRecorrenteCreate = {
        empresa_id: empresa.id,
        tipo: this.tipo(),
        descricao: v.descricao,
        valor: v.valor,
        data_primeira_competencia: this.toISODate(v.data_primeira_competencia),
        data_primeiro_vencimento: this.toISODate(v.data_primeiro_vencimento),
        frequencia: v.frequencia as 'semanal' | 'quinzenal' | 'mensal' | 'anual',
        quantidade: v.quantidade,
        categoria_id: v.categoria_id ?? null,
        contato_id: v.contato_id ?? null,
        conta_bancaria_id: v.conta_bancaria_id ?? null,
        observacoes: v.observacoes ?? null,
        tags: v.tags ?? [],
        veiculo_id: this.isMulta() ? (v.veiculo_id ?? null) : null,
        imovel_id: this.isIptu() ? (v.imovel_id ?? null) : null,
      };
      this.svc.criarRecorrente(payload).subscribe({
        next: (lancamentos) => {
          this.salvando.set(false);
          this.dialogVisivel.set(false);
          this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: `${lancamentos.length} recorrências criadas.` });
          this.carregarDados();
        },
        error: (err) => {
          this.salvando.set(false);
          const detail = err?.error?.detail ?? 'Erro ao criar recorrência.';
          this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
        },
      });
    }
  }

  protected abrirBaixa(lct: Lancamento): void {
    this.baixandoId.set(lct.id);
    const restante = Number(lct.valor) - Number(lct.valor_pago);
    this.baixaForm.reset({
      valor_pago: restante > 0 ? restante : null,
      data_pagamento: new Date(),
      conta_bancaria_id: lct.conta_bancaria_id,
      categoria_id: lct.categoria_id,
    });
    this.baixaDialogVisivel.set(true);
  }

  protected registrarBaixa(): void {
    const id = this.baixandoId();
    if (!id) return;
    const v = this.baixaForm.value;
    if (!v.valor_pago || !v.data_pagamento || !v.conta_bancaria_id || !v.categoria_id) {
      this.messageSvc.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha todos os campos obrigatórios.' });
      return;
    }
    const payload: LancamentoBaixaCreate = {
      valor_pago: v.valor_pago,
      data_pagamento: this.toISODate(v.data_pagamento),
      conta_bancaria_id: v.conta_bancaria_id,
      categoria_id: v.categoria_id,
    };
    this.salvando.set(true);
    this.svc.registrarBaixa(id, payload).subscribe({
      next: (updated) => {
        this.lista.update(lst => lst.map(l => l.id === updated.id ? updated : l));
        this.salvando.set(false);
        this.baixaDialogVisivel.set(false);
        this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Pagamento registrado.' });
      },
      error: (err) => {
        this.salvando.set(false);
        const detail = err?.error?.detail ?? 'Erro ao registrar pagamento.';
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
      },
    });
  }

  protected confirmarCancelamento(event: Event, id: string): void {
    this.confirmSvc.confirm({
      target: event.target as EventTarget,
      message: 'Confirma o cancelamento deste lançamento?',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        this.svc.cancelar(id).subscribe({
          next: (updated) => {
            this.lista.update(lst => lst.map(l => l.id === updated.id ? updated : l));
            this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Lançamento cancelado.' });
          },
          error: (err) => {
            const detail = err?.error?.detail ?? 'Erro ao cancelar lançamento.';
            this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
          },
        });
      },
    });
  }

  protected confirmarNaoRealizado(event: Event, id: string): void {
    this.confirmSvc.confirm({
      target: event.target as EventTarget,
      message: 'Marcar este lançamento como não realizado? Ele sai do previsto, mas permanece visível.',
      icon: 'pi pi-calendar-times',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        this.svc.marcarNaoRealizado(id).subscribe({
          next: (updated) => {
            this.lista.update(lst => lst.map(l => l.id === updated.id ? updated : l));
            this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Marcado como não realizado.' });
          },
          error: (err) => {
            const detail = err?.error?.detail ?? 'Erro ao marcar como não realizado.';
            this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
          },
        });
      },
    });
  }

  protected reverterPrevisto(lct: Lancamento): void {
    this.svc.reverterPrevisto(lct.id).subscribe({
      next: (updated) => {
        this.lista.update(lst => lst.map(l => l.id === updated.id ? updated : l));
        this.messageSvc.add({ severity: 'success', summary: 'Sucesso', detail: 'Voltou para previsto.' });
      },
      error: (err) => {
        const detail = err?.error?.detail ?? 'Erro ao reverter lançamento.';
        this.messageSvc.add({ severity: 'error', summary: 'Erro', detail });
      },
    });
  }

  // ── Consulta de lançamentos do patrimônio ───────────────────────────────────
  protected readonly consultaDialog = signal(false);
  protected readonly consultaLoading = signal(false);
  protected readonly consultaTitulo = signal('Lançamentos do patrimônio');
  protected readonly consultaLancamentos = signal<Lancamento[]>([]);
  protected readonly consultaTotal = computed(() =>
    this.consultaLancamentos().reduce((acc, l) => acc + Number(l.valor), 0)
  );

  protected abrirConsultaPatrimonio(lct: Lancamento): void {
    this.consultaDialog.set(true);
    this.consultaLoading.set(true);
    this.consultaLancamentos.set([]);

    if (lct.imovel_id) {
      const imovel = this.imoveis().find(i => i.id === lct.imovel_id);
      this.consultaTitulo.set('Lançamentos do imóvel' + (imovel ? ` — ${imovel.descricao}` : ''));
      this.patrimonioSvc.listarLancamentosImovel(lct.imovel_id).subscribe({
        next: (data) => { this.consultaLancamentos.set(data); this.consultaLoading.set(false); },
        error: () => { this.consultaLoading.set(false); this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar lançamentos do imóvel.' }); },
      });
    } else if (lct.veiculo_id) {
      const veiculo = this.veiculos().find(v => v.id === lct.veiculo_id);
      this.consultaTitulo.set('Lançamentos do veículo' + (veiculo ? ` — ${veiculo.marca} ${veiculo.modelo}` : ''));
      this.patrimonioSvc.listarLancamentosVeiculo(lct.veiculo_id).subscribe({
        next: (data) => { this.consultaLancamentos.set(data); this.consultaLoading.set(false); },
        error: () => { this.consultaLoading.set(false); this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar lançamentos do veículo.' }); },
      });
    } else {
      this.consultaLoading.set(false);
    }
  }

  // Ordenação client-side: trata valor/valor_pago como número (chegam como string
  // do backend — Decimal serializado), e o restante como string/data.
  protected customSort(event: SortEvent): void {
    const numericos = new Set(['valor', 'valor_pago']);
    const field = event.field ?? '';
    const order = event.order ?? 1;
    event.data?.sort((a: Record<string, unknown>, b: Record<string, unknown>) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let v1: any = a[field];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let v2: any = b[field];
      if (numericos.has(field)) { v1 = Number(v1); v2 = Number(v2); }
      let res: number;
      if (v1 == null && v2 != null) res = -1;
      else if (v1 != null && v2 == null) res = 1;
      else if (v1 == null && v2 == null) res = 0;
      else if (typeof v1 === 'string' && typeof v2 === 'string') res = v1.localeCompare(v2);
      else res = v1 < v2 ? -1 : v1 > v2 ? 1 : 0;
      return res * order;
    });
  }

  protected formatDate(d: string | null): string {
    if (!d) return '—';
    const [y, m, day] = d.split('-');
    return `${day}/${m}/${y}`;
  }

  protected formatMoeda(v: number | string | null): string {
    if (v == null) return '—';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(v));
  }

  protected statusSeverity(s: string): 'warn' | 'success' | 'danger' | 'secondary' | 'info' {
    if (s === 'pendente') return 'warn';
    if (s === 'pago') return 'success';
    if (s === 'cancelado') return 'danger';
    if (s === 'nao_realizado') return 'info';
    return 'secondary';
  }

  protected statusLabel(s: string): string {
    if (s === 'pendente') return 'Pendente';
    if (s === 'pago') return 'Pago';
    if (s === 'cancelado') return 'Cancelado';
    if (s === 'nao_realizado') return 'Não realizado';
    return s;
  }

  // ── Anexos ──────────────────────────────────────────────────────────────────

  protected visualizarAnexo(anexo: LancamentoAnexo): void {
    this.svc.viewAnexoBlob(anexo.lancamento_id, anexo.id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
        setTimeout(() => URL.revokeObjectURL(url), 60_000);
      },
      error: () => this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao abrir o arquivo.' }),
    });
  }

  protected baixarAnexo(anexo: LancamentoAnexo): void {
    this.svc.downloadAnexoBlob(anexo.lancamento_id, anexo.id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = anexo.nome_original;
        a.click();
        URL.revokeObjectURL(url);
      },
      error: () => this.messageSvc.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao baixar o arquivo.' }),
    });
  }

  protected abrirAnexosPopup(event: Event, lct: Lancamento): void {
    this.anexosPopup.set([]);
    this.carregandoAnexosPopup.set(true);
    this.opAnexo.toggle(event);
    this.svc.listarAnexos(lct.id).subscribe({
      next: (data) => { this.anexosPopup.set(data); this.carregandoAnexosPopup.set(false); },
      error: () => { this.carregandoAnexosPopup.set(false); },
    });
  }

  private carregarAnexos(lancamentoId: string): void {
    this.carregandoAnexos.set(true);
    this.svc.listarAnexos(lancamentoId).subscribe({
      next: (data) => { this.anexos.set(data); this.carregandoAnexos.set(false); },
      error: () => this.carregandoAnexos.set(false),
    });
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver.set(false);
    Array.from(event.dataTransfer?.files ?? []).forEach(f => this.uploadFile(f));
  }

  protected onFileInputChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    Array.from(input.files ?? []).forEach(f => this.uploadFile(f));
    input.value = '';
  }

  private uploadFile(file: File): void {
    const id = this.editandoId();
    if (!id) return;
    this.uploadando.set(true);
    this.svc.uploadAnexo(id, file).subscribe({
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

  protected confirmarExcluirAnexo(event: Event, anexoId: string): void {
    this.confirmSvc.confirm({
      target: event.target as EventTarget,
      message: 'Excluir este anexo?',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Sim',
      rejectLabel: 'Não',
      accept: () => {
        const id = this.editandoId();
        if (!id) return;
        this.svc.deletarAnexo(id, anexoId).subscribe({
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

  protected adicionarTag(event: Event): void {
    event.preventDefault();
    const input = event.target as HTMLInputElement;
    const val = input.value.replace(',', '').trim();
    if (!val) return;
    const ctrl = this.form.get('tags');
    const atual: string[] = ctrl?.value ?? [];
    if (!atual.includes(val)) ctrl?.setValue([...atual, val]);
    input.value = '';
  }

  protected removerTag(tag: string): void {
    const ctrl = this.form.get('tags');
    const atual: string[] = ctrl?.value ?? [];
    ctrl?.setValue(atual.filter(t => t !== tag));
  }

  // ── Histórico de auditoria ────────────────────────────────────────────────
  protected historicoDialog = signal(false);
  protected carregandoHistorico = signal(false);
  protected historicoItens = signal<any[]>([]);

  protected objectEntries(obj: Record<string, any>): [string, any][] {
    return Object.entries(obj);
  }

  protected abrirHistorico(lct: Lancamento): void {
    this.historicoDialog.set(true);
    this.carregandoHistorico.set(true);
    this.historicoItens.set([]);
    this.http.get<any[]>(`/api/v1/auditoria/lancamento/${lct.id}`).subscribe({
      next: (data) => { this.historicoItens.set(data); this.carregandoHistorico.set(false); },
      error: () => { this.carregandoHistorico.set(false); },
    });
  }

  protected exportarExcel(): void {
    this.exportSvc.exportarExcel(
      this.listaFiltrada(),
      `${this.titulo()}_${this.mesTitulo()}`,
    );
  }

  protected exportarPDF(): void {
    this.exportSvc.exportarPDF(
      this.listaFiltrada(),
      this.titulo(),
      this.mesTitulo(),
    );
  }

  protected duplicar(lct: Lancamento): void {
    const empresaId = this.empresaStore.empresaAtiva()?.id;
    if (!empresaId) return;
    this.svc.duplicar(lct.id, empresaId).subscribe({
      next: () => {
        this.messageSvc.add({ severity: 'success', summary: 'Lançamento duplicado com sucesso.' });
        this.carregarDados();
      },
      error: (err) => {
        const detail = err?.error?.detail ?? 'Erro ao duplicar lançamento.';
        this.messageSvc.add({ severity: 'error', summary: detail });
      },
    });
  }
}
