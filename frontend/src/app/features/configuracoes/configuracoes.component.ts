import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { SelectModule } from 'primeng/select';
import { ToggleSwitchModule } from 'primeng/toggleswitch';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MessageService } from 'primeng/api';

import { EmpresaStore } from '../../core/stores/empresa.store';
import { EmpresaService } from '../../core/services/empresa.service';
import { EmpresaResponse, EmpresaUpdate, RegimeTributario } from '../../core/models';

@Component({
  selector: 'app-configuracoes',
  standalone: true,
  providers: [MessageService],
  imports: [
    ReactiveFormsModule,
    ButtonModule,
    InputTextModule,
    SelectModule,
    ToggleSwitchModule,
    MessageModule,
    ToastModule,
    ProgressSpinnerModule,
  ],
  template: `
    <p-toast />

    <div class="page">
      <div class="page-header">
        <div>
          <h1 class="page-title">Configurações</h1>
          @if (empresa()) {
            <p class="page-subtitle">{{ empresa()!.nome_principal }}</p>
          }
        </div>
        @if (empresa()) {
          <p-button
            label="Salvar alterações"
            icon="pi pi-check"
            (onClick)="salvar()"
            [loading]="salvando()"
          />
        }
      </div>

      @if (carregando()) {
        <div class="loading-wrap">
          <p-progressSpinner strokeWidth="3" [style]="{ width: '48px', height: '48px' }" />
        </div>
      } @else if (!empresaStore.empresaAtiva()) {
        <p-message severity="info">
          Selecione uma empresa no cabeçalho para visualizar suas configurações.
        </p-message>
      } @else if (empresa()) {
        <form [formGroup]="form">

          <!-- ── Identificação ── -->
          <div class="section">
            <div class="section-title">Identificação</div>
            <div class="section-body">
              <div class="field-row">
                <div class="field field-grow">
                  <label>Razão Social / Nome *</label>
                  <input pInputText formControlName="nome_principal" [style]="{ width: '100%' }" />
                </div>
                <div class="field field-grow">
                  <label>Nome Fantasia / Apelido</label>
                  <input pInputText formControlName="nome_alternativo" placeholder="Opcional" [style]="{ width: '100%' }" />
                </div>
              </div>

              @if (empresa()!.tipo === 'PJ') {
                <div class="field" style="max-width:280px">
                  <label>Regime Tributário</label>
                  <p-select
                    formControlName="regime_tributario"
                    [options]="regimesOpcoes"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Selecione"
                    [style]="{ width: '100%' }"
                  />
                </div>
              }

              <div class="field-row">
                <div class="field field-grow">
                  <label>Telefone</label>
                  <input pInputText formControlName="telefone" placeholder="(11) 99999-9999" [style]="{ width: '100%' }" />
                </div>
                <div class="field field-grow">
                  <label>E-mail</label>
                  <input pInputText formControlName="email" type="email" placeholder="contato@empresa.com" [style]="{ width: '100%' }" />
                </div>
              </div>
            </div>
          </div>

          <!-- ── Endereço ── -->
          <div class="section">
            <div class="section-title">Endereço</div>
            <div class="section-body">
              <div class="field-row">
                <div class="field" style="flex:0 0 150px">
                  <label>CEP</label>
                  <input pInputText formControlName="endereco_cep" placeholder="00000-000" maxlength="9" [style]="{ width: '100%' }" />
                </div>
                <div class="field field-grow">
                  <label>Logradouro</label>
                  <input pInputText formControlName="logradouro" [style]="{ width: '100%' }" />
                </div>
                <div class="field" style="flex:0 0 100px">
                  <label>Número</label>
                  <input pInputText formControlName="numero" [style]="{ width: '100%' }" />
                </div>
              </div>
              <div class="field-row">
                <div class="field field-grow">
                  <label>Complemento</label>
                  <input pInputText formControlName="complemento" [style]="{ width: '100%' }" />
                </div>
                <div class="field field-grow">
                  <label>Bairro</label>
                  <input pInputText formControlName="bairro" [style]="{ width: '100%' }" />
                </div>
              </div>
              <div class="field-row">
                <div class="field field-grow">
                  <label>Cidade</label>
                  <input pInputText formControlName="cidade" [style]="{ width: '100%' }" />
                </div>
                <div class="field" style="flex:0 0 70px">
                  <label>UF</label>
                  <input pInputText formControlName="uf" maxlength="2" placeholder="SP" [style]="{ width: '100%' }" />
                </div>
              </div>
            </div>
          </div>

          <!-- ── Configurações Financeiras ── -->
          <div class="section">
            <div class="section-title">Configurações Financeiras</div>
            <div class="section-body">
              <div class="field-row">
                <div class="field">
                  <label>Separador decimal</label>
                  <p-select
                    formControlName="separador_decimal"
                    [options]="separadoresOpcoes"
                    optionLabel="label"
                    optionValue="value"
                    [style]="{ width: '160px' }"
                  />
                </div>
                <div class="field">
                  <label>Separador de milhares</label>
                  <p-select
                    formControlName="separador_milhares"
                    [options]="separadoresOpcoes"
                    optionLabel="label"
                    optionValue="value"
                    [style]="{ width: '160px' }"
                  />
                </div>
                <div class="field">
                  <label>Casas dec. (valor)</label>
                  <p-select
                    formControlName="casas_decimais_valor"
                    [options]="casasDecimaisOpcoes"
                    optionLabel="label"
                    optionValue="value"
                    [style]="{ width: '100px' }"
                  />
                </div>
                <div class="field">
                  <label>Casas dec. (%)</label>
                  <p-select
                    formControlName="casas_decimais_percentual"
                    [options]="casasDecimaisOpcoes"
                    optionLabel="label"
                    optionValue="value"
                    [style]="{ width: '100px' }"
                  />
                </div>
              </div>

              <div class="field-row">
                <div class="field">
                  <label>Mês início do exercício</label>
                  <p-select
                    formControlName="mes_inicio_exercicio"
                    [options]="mesesOpcoes"
                    optionLabel="label"
                    optionValue="value"
                    [style]="{ width: '180px' }"
                  />
                </div>
                <div class="field">
                  <label>Dia fechamento mensal</label>
                  <p-select
                    formControlName="dia_fechamento_mensal"
                    [options]="diasOpcoes"
                    optionLabel="label"
                    optionValue="value"
                    [style]="{ width: '120px' }"
                  />
                </div>
                <div class="field field-toggle">
                  <label>Trava de fechamento</label>
                  <p-toggleswitch formControlName="trava_fechamento_ativa" />
                </div>
              </div>

              <div class="field-row">
                <div class="field">
                  <label>Prefixo de lançamento</label>
                  <input pInputText formControlName="prefixo_lancamento" maxlength="10" [style]="{ width: '130px' }" />
                </div>
                <div class="field field-toggle">
                  <label>Reiniciar numeração anualmente</label>
                  <p-toggleswitch formControlName="reset_anual_numeracao" />
                </div>
              </div>
            </div>
          </div>

          @if (formErro()) {
            <p-message severity="error">{{ formErro() }}</p-message>
          }

        </form>
      }
    </div>
  `,
  styles: [`
    .page { max-width: 860px; }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1.5rem;
    }
    .page-title { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 700; }
    .page-subtitle { margin: 0; color: var(--p-surface-500); font-size: 0.875rem; }

    .loading-wrap {
      display: flex;
      justify-content: center;
      padding: 3rem;
    }

    .section {
      border: 1px solid var(--p-surface-200);
      border-radius: 8px;
      margin-bottom: 1.25rem;
      overflow: hidden;
    }

    .section-title {
      background: var(--p-surface-50);
      padding: 0.6rem 1rem;
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: var(--p-surface-500);
      border-bottom: 1px solid var(--p-surface-200);
    }

    .section-body {
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.875rem;
    }

    .field {
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }

    .field label {
      font-size: 0.8rem;
      font-weight: 600;
    }

    .field-row {
      display: flex;
      gap: 0.875rem;
      flex-wrap: wrap;
      align-items: flex-start;
    }

    .field-grow { flex: 1 1 180px; }

    .field-toggle {
      flex-direction: row;
      align-items: center;
      gap: 0.75rem;
      padding-top: 1.4rem;
    }
  `],
})
export class ConfiguracoesComponent implements OnInit {
  protected readonly empresaStore = inject(EmpresaStore);
  private readonly empresaService = inject(EmpresaService);
  private readonly messageService = inject(MessageService);
  private readonly fb = inject(FormBuilder);

  protected readonly empresa = signal<EmpresaResponse | null>(null);
  protected readonly carregando = signal(false);
  protected readonly salvando = signal(false);
  protected readonly formErro = signal<string | null>(null);

  protected readonly regimesOpcoes = [
    { label: 'Simples Nacional', value: 'Simples' },
    { label: 'Lucro Presumido', value: 'Presumido' },
    { label: 'Lucro Real', value: 'Real' },
    { label: 'MEI', value: 'MEI' },
  ];

  protected readonly separadoresOpcoes = [
    { label: ', (vírgula)', value: ',' },
    { label: '. (ponto)', value: '.' },
  ];

  protected readonly casasDecimaisOpcoes = [0, 1, 2, 3, 4].map((n) => ({ label: String(n), value: n }));

  protected readonly mesesOpcoes = [
    { label: 'Janeiro', value: 1 }, { label: 'Fevereiro', value: 2 },
    { label: 'Março', value: 3 }, { label: 'Abril', value: 4 },
    { label: 'Maio', value: 5 }, { label: 'Junho', value: 6 },
    { label: 'Julho', value: 7 }, { label: 'Agosto', value: 8 },
    { label: 'Setembro', value: 9 }, { label: 'Outubro', value: 10 },
    { label: 'Novembro', value: 11 }, { label: 'Dezembro', value: 12 },
  ];

  protected readonly diasOpcoes = Array.from({ length: 28 }, (_, i) => ({ label: String(i + 1), value: i + 1 }));

  protected readonly form = this.fb.group({
    nome_principal: ['', [Validators.required, Validators.minLength(2)]],
    nome_alternativo: [''],
    regime_tributario: [null as RegimeTributario | null],
    telefone: [''],
    email: [''],
    endereco_cep: [''],
    logradouro: [''],
    numero: [''],
    complemento: [''],
    bairro: [''],
    cidade: [''],
    uf: [''],
    separador_decimal: [','],
    separador_milhares: ['.'],
    casas_decimais_valor: [2],
    casas_decimais_percentual: [2],
    mes_inicio_exercicio: [1],
    trava_fechamento_ativa: [false],
    dia_fechamento_mensal: [5],
    prefixo_lancamento: ['LCT-'],
    reset_anual_numeracao: [false],
  });

  ngOnInit(): void {
    const ativa = this.empresaStore.empresaAtiva();
    if (ativa) {
      this.carregar(ativa.id);
    }
  }

  private carregar(id: string): void {
    this.carregando.set(true);
    this.empresaService.obter(id).subscribe({
      next: (e) => {
        this.empresa.set(e);
        this.form.patchValue({
          nome_principal: e.nome_principal,
          nome_alternativo: e.nome_alternativo ?? '',
          regime_tributario: e.regime_tributario,
          telefone: e.telefone ?? '',
          email: e.email ?? '',
          endereco_cep: e.endereco_cep ?? '',
          logradouro: e.logradouro ?? '',
          numero: e.numero ?? '',
          complemento: e.complemento ?? '',
          bairro: e.bairro ?? '',
          cidade: e.cidade ?? '',
          uf: e.uf ?? '',
          separador_decimal: e.separador_decimal,
          separador_milhares: e.separador_milhares,
          casas_decimais_valor: e.casas_decimais_valor,
          casas_decimais_percentual: e.casas_decimais_percentual,
          mes_inicio_exercicio: e.mes_inicio_exercicio,
          trava_fechamento_ativa: e.trava_fechamento_ativa,
          dia_fechamento_mensal: e.dia_fechamento_mensal,
          prefixo_lancamento: e.prefixo_lancamento,
          reset_anual_numeracao: e.reset_anual_numeracao,
        });
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }

  protected salvar(): void {
    this.formErro.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.formErro.set('Razão Social é obrigatória.');
      return;
    }

    const v = this.form.getRawValue();
    const sepDec = v.separador_decimal ?? ',';
    const sepMil = v.separador_milhares ?? '.';
    if (sepDec === sepMil) {
      this.formErro.set('Separador decimal e de milhares não podem ser iguais.');
      return;
    }

    const payload: EmpresaUpdate = {
      nome_principal: v.nome_principal,
      nome_alternativo: v.nome_alternativo || null,
      regime_tributario: (v.regime_tributario as RegimeTributario) || null,
      telefone: v.telefone || null,
      email: v.email || null,
      endereco_cep: v.endereco_cep || null,
      logradouro: v.logradouro || null,
      numero: v.numero || null,
      complemento: v.complemento || null,
      bairro: v.bairro || null,
      cidade: v.cidade || null,
      uf: v.uf || null,
      separador_decimal: sepDec,
      separador_milhares: sepMil,
      casas_decimais_valor: v.casas_decimais_valor ?? 2,
      casas_decimais_percentual: v.casas_decimais_percentual ?? 2,
      mes_inicio_exercicio: v.mes_inicio_exercicio ?? 1,
      trava_fechamento_ativa: v.trava_fechamento_ativa ?? false,
      dia_fechamento_mensal: v.dia_fechamento_mensal ?? 5,
      prefixo_lancamento: v.prefixo_lancamento || 'LCT-',
      reset_anual_numeracao: v.reset_anual_numeracao ?? false,
    };

    this.salvando.set(true);
    const id = this.empresaStore.empresaAtiva()!.id;
    this.empresaService.atualizar(id, payload).subscribe({
      next: (e) => {
        this.empresa.set(e);
        this.salvando.set(false);
        this.messageService.add({ severity: 'success', summary: 'Salvo', detail: 'Configurações salvas com sucesso.' });
        this.empresaStore.carregar();
      },
      error: (err) => {
        const detail = typeof err.error?.detail === 'string' ? err.error.detail : 'Erro ao salvar configurações.';
        this.formErro.set(detail);
        this.salvando.set(false);
      },
    });
  }
}
