import { Component, signal } from '@angular/core';
import { AccordionModule } from 'primeng/accordion';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { DividerModule } from 'primeng/divider';
import { TabsModule } from 'primeng/tabs';

@Component({
  selector: 'app-ajuda',
  standalone: true,
  imports: [AccordionModule, CardModule, TagModule, DividerModule, TabsModule],
  template: `
    <div class="ajuda-container">

      <div class="ajuda-header">
        <i class="pi pi-question-circle header-icon"></i>
        <div>
          <h1>Central de Ajuda</h1>
          <p>Guia completo de uso do App Financeiro — versão 1.1 (atualizado em junho/2026)</p>
        </div>
      </div>

      <p-tabs [(value)]="abaAtiva">
        <p-tablist>
          <p-tab value="interface"><i class="pi pi-desktop"></i> Interface</p-tab>
          <p-tab value="financeiro"><i class="pi pi-wallet"></i> Financeiro</p-tab>
          <p-tab value="cadastros"><i class="pi pi-database"></i> Cadastros</p-tab>
          <p-tab value="admin"><i class="pi pi-building"></i> Administração</p-tab>
          <p-tab value="dicas"><i class="pi pi-lightbulb"></i> Dicas</p-tab>
        </p-tablist>

        <p-tabpanels>

          <!-- ── INTERFACE ──────────────────────────────────────────────── -->
          <p-tabpanel value="interface">
            <p-accordion [multiple]="true" [value]="['header']">

              <p-accordion-panel value="header">
                <p-accordion-header><i class="pi pi-bars ico"></i>&nbsp; Barra Superior (Header)</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <div class="tipos-grid">
                      <div class="tipo-item">
                        <i class="pi pi-search"></i>
                        <strong>Busca Global</strong>
                        <span>Digite e pressione Enter para buscar lançamentos por descrição</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-building"></i>
                        <strong>Seletor de Empresa</strong>
                        <span>Troca a empresa ativa — todos os dados filtram por ela automaticamente</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-moon"></i>
                        <strong>Modo Escuro</strong>
                        <span>Clique para alternar o tema claro/escuro — preferência salva no navegador</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-bell"></i>
                        <strong>Sino de Alertas</strong>
                        <span>Badge vermelho indica contas vencidas ou com vencimento hoje</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-user"></i>
                        <strong>Iniciais do Usuário</strong>
                        <span>Clique para abrir o dialog de Alterar Senha</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-sign-out"></i>
                        <strong>Sair</strong>
                        <span>Encerra a sessão com segurança</span>
                      </div>
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="sidebar">
                <p-accordion-header><i class="pi pi-bars ico"></i>&nbsp; Menu Lateral (Sidebar)</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>O menu lateral agrupa as rotinas por categoria:</p>
                    <div class="hierarquia">
                      <div class="nivel1"><i class="pi pi-home"></i> <strong>Principal</strong> — Dashboard e Fluxo de Caixa</div>
                      <div class="nivel1"><i class="pi pi-wallet"></i> <strong>Financeiro</strong> — Contas a Pagar, Contas a Receber, Extrato Bancário, Inadimplência, Transferências, Conciliação Bancária</div>
                      <div class="nivel1"><i class="pi pi-database"></i> <strong>Cadastros</strong> — Empresas, Categorias, Clientes/Fornecedores, Contas/Cartões, Patrimonial</div>
                      <div class="nivel1"><i class="pi pi-building"></i> <strong>Administração</strong> — Usuários, Importação em lote, Configurações</div>
                      <div class="nivel1"><i class="pi pi-question-circle"></i> <strong>Suporte</strong> — Esta página de Ajuda</div>
                    </div>
                    <p-divider />
                    <strong>Recolher o menu:</strong>
                    <p>Clique no botão <strong>&lt;</strong> na borda direita da sidebar para minimizar. Recolhida, exibe apenas ícones com tooltip ao passar o mouse. Clique em <strong>&gt;</strong> para expandir.</p>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="dashboard">
                <p-accordion-header><i class="pi pi-chart-bar ico"></i>&nbsp; Dashboard</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Painel inicial com resumo financeiro da empresa selecionada para o mês corrente.</p>
                    <div class="dois-cols">
                      <div>
                        <strong>KPIs do mês:</strong>
                        <ul>
                          <li><strong>Saldo em conta</strong> — total das contas bancárias ativas (exceto cartões)</li>
                          <li><strong>Receitas realizadas</strong> — recebimentos pagos no mês</li>
                          <li><strong>Receitas previstas</strong> — pendentes ainda a receber</li>
                          <li><strong>Despesas realizadas</strong> — pagamentos efetuados</li>
                          <li><strong>Despesas previstas</strong> — contas a pagar pendentes</li>
                          <li><strong>Saldo líquido</strong> — receitas realizadas menos despesas realizadas</li>
                        </ul>
                      </div>
                      <div>
                        <strong>Gráficos:</strong>
                        <ul>
                          <li><strong>Barras:</strong> Receitas × Despesas dos últimos 6 meses</li>
                          <li><strong>Pizza:</strong> Top despesas por categoria no mês</li>
                        </ul>
                        <br />
                        <strong>Alertas de vencimento:</strong>
                        <ul>
                          <li>Banner vermelho para contas vencidas</li>
                          <li>Listas: "Vence Hoje", "Vencidos", "Próximos 7 Dias"</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="tema">
                <p-accordion-header><i class="pi pi-moon ico"></i>&nbsp; Modo Escuro</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Alterna entre tema claro e escuro em toda a aplicação.</p>
                    <ul>
                      <li>Clique no ícone <i class="pi pi-moon"></i> / <i class="pi pi-sun"></i> no header</li>
                      <li>A preferência é salva automaticamente no navegador</li>
                      <li>Na próxima visita o tema é restaurado automaticamente</li>
                    </ul>
                    <div class="dica-box">
                      <i class="pi pi-lightbulb"></i>
                      O modo escuro reduz o cansaço visual em ambientes com pouca luz.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

            </p-accordion>
          </p-tabpanel>

          <!-- ── FINANCEIRO ─────────────────────────────────────────────── -->
          <p-tabpanel value="financeiro">
            <p-accordion [multiple]="true" [value]="['lancamentos']">

              <p-accordion-panel value="lancamentos">
                <p-accordion-header><i class="pi pi-list ico"></i>&nbsp; Contas a Pagar e Receber</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <div class="dois-cols">
                      <div>
                        <strong>Cadastrar lançamento:</strong>
                        <ol>
                          <li>Clique em <strong>+ Novo</strong></li>
                          <li>Preencha descrição, valor, datas de competência e vencimento</li>
                          <li>Selecione categoria (obrigatório) e contato (opcional)</li>
                          <li>Escolha o modo: <strong>Simples</strong>, <strong>Parcelado</strong> ou <strong>Recorrente</strong></li>
                          <li>Adicione <strong>Tags</strong> livres (ex: urgente, projeto-x)</li>
                        </ol>
                      </div>
                      <div>
                        <strong>Ações por lançamento:</strong>
                        <ul>
                          <li><i class="pi pi-check-circle cor-verde"></i> <strong>Baixa</strong> — registra pagamento/recebimento com conta bancária (aceita valor acima do previsto)</li>
                          <li><i class="pi pi-ban" style="color:var(--p-orange-500)"></i> <strong>Marcar não realizado</strong> — sinaliza um previsto que comprovadamente não ocorreu (sem excluir)</li>
                          <li><i class="pi pi-pencil"></i> <strong>Editar</strong> — altera dados do lançamento</li>
                          <li><i class="pi pi-search cor-azul"></i> <strong>Consultar</strong> — visualiza o lançamento em modo leitura</li>
                          <li><i class="pi pi-copy"></i> <strong>Duplicar</strong> — cria cópia na mesma empresa</li>
                          <li><i class="pi pi-history"></i> <strong>Histórico</strong> — log completo de alterações</li>
                          <li><i class="pi pi-paperclip"></i> <strong>Anexos</strong> — visualiza arquivos anexados</li>
                          <li><i class="pi pi-times cor-vermelho"></i> <strong>Cancelar</strong> — inativa o lançamento</li>
                        </ul>
                      </div>
                    </div>
                    <p-divider />
                    <strong>Modos de criação:</strong>
                    <div class="tipos-grid">
                      <div class="tipo-item">
                        <i class="pi pi-file"></i>
                        <strong>Simples</strong>
                        <span>Um único lançamento com valor e data definidos</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-list"></i>
                        <strong>Parcelado</strong>
                        <span>Divide o valor total em N parcelas mensais automáticas</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-refresh"></i>
                        <strong>Recorrente</strong>
                        <span>Repete o mesmo valor em frequência semanal, quinzenal, mensal ou anual</span>
                      </div>
                    </div>
                    <p-divider />
                    <strong>Filtros, ordenação e exportação:</strong>
                    <ul>
                      <li>Navegue entre meses com as setas ou clique no calendário para ir direto ao mês</li>
                      <li>Filtre por status: Todos / Pendentes / Pagos / Cancelados</li>
                      <li><strong>Filtros avançados <span class="tag-novo">NOVO</span>:</strong> filtre dentro da tela por texto, categoria, fornecedor/cliente, faixa de valor e faixa de datas. Use <strong>Limpar filtros</strong> para remover todos de uma vez.</li>
                      <li><strong>Ordenação <span class="tag-novo">NOVO</span>:</strong> clique no cabeçalho de qualquer coluna (descrição, valor, vencimento…) para ordenar de forma crescente/decrescente.</li>
                      <li><i class="pi pi-file-excel cor-verde"></i> Exportar Excel e <i class="pi pi-file-pdf cor-vermelho"></i> PDF com os lançamentos filtrados</li>
                    </ul>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="extrato">
                <p-accordion-header><i class="pi pi-receipt ico-azul"></i>&nbsp; Extrato Bancário</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Visão detalhada de todas as movimentações de uma conta bancária específica, com saldo progressivo por dia.</p>
                    <ol>
                      <li>Selecione a <strong>conta bancária</strong> no filtro superior</li>
                      <li>Defina o período (data início e data fim)</li>
                      <li>O extrato exibe lançamentos pagos com saldo acumulado a cada linha</li>
                      <li>O <strong>saldo anterior</strong> é calculado a partir do saldo inicial da conta cadastrada</li>
                    </ol>
                    <strong>Efetivação pelo extrato:</strong>
                    <p>Lançamentos pendentes aparecem em destaque. Clique em <strong>Efetivar</strong> diretamente no extrato para registrar o pagamento sem precisar voltar à tela de Contas a Pagar/Receber.</p>
                    <div class="dica-box">
                      <i class="pi pi-lightbulb"></i>
                      O saldo é calculado a partir do <strong>Saldo Inicial</strong> e <strong>Data do Saldo</strong> configurados no cadastro da conta bancária. Certifique-se de que esses campos estejam corretos.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="inadimplencia">
                <p-accordion-header><i class="pi pi-exclamation-circle ico-despesa"></i>&nbsp; Inadimplência</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Visão consolidada de todas as contas a receber vencidas, agrupadas por cliente.</p>
                    <strong>Indicadores:</strong>
                    <ul>
                      <li>Total geral em atraso</li>
                      <li>Número de clientes inadimplentes</li>
                      <li>Quantidade de lançamentos vencidos</li>
                      <li>Maior prazo de atraso (em dias)</li>
                    </ul>
                    <strong>Por cliente:</strong>
                    <p>Expande a lista de lançamentos daquele cliente com dias de atraso e valor individual. Badge <span class="tag-laranja">laranja</span> para &lt;30 dias, <span class="tag-vermelho">vermelho</span> para &gt;30 dias.</p>
                    <div class="dica-box">
                      <i class="pi pi-lightbulb"></i>
                      Use o botão <i class="pi pi-file-excel"></i> para exportar a lista de inadimplentes para Excel.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="transferencias">
                <p-accordion-header><i class="pi pi-arrows-h ico-azul"></i>&nbsp; Transferências</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Movimentação entre contas sem gerar despesa ou receita no resultado financeiro.</p>
                    <ol>
                      <li>Selecione a conta de <strong>Origem</strong></li>
                      <li>Selecione a conta de <strong>Destino</strong> (pode ser de outra empresa do grupo)</li>
                      <li>Informe valor e data</li>
                      <li>Confirme — ambas as contas são atualizadas simultaneamente e de forma atômica</li>
                    </ol>
                    <div class="dica-box">
                      <i class="pi pi-info-circle"></i>
                      Transferências entre empresas diferentes do grupo são suportadas. O sistema debita da origem e credita no destino em uma única operação.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="fluxo">
                <p-accordion-header><i class="pi pi-chart-line ico-verde"></i>&nbsp; Fluxo de Caixa</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Visão mensal de receitas e despesas realizadas e previstas, organizada por dia.</p>
                    <ul>
                      <li>Navegue com as setas ou clique no calendário para ir a qualquer mês</li>
                      <li>Filtre por empresa específica e/ou conta bancária</li>
                    </ul>
                    <strong>Colunas exibidas:</strong>
                    <div class="tipos-grid">
                      <div class="tipo-item"><i class="pi pi-check-circle" style="color:var(--p-green-500)"></i><strong>Rec. Realizadas</strong><span>Recebimentos efetivados no dia</span></div>
                      <div class="tipo-item"><i class="pi pi-clock" style="color:var(--p-blue-500)"></i><strong>Rec. Previstas</strong><span>A receber pendentes</span></div>
                      <div class="tipo-item"><i class="pi pi-check-circle" style="color:var(--p-red-500)"></i><strong>Desp. Realizadas</strong><span>Pagamentos efetuados</span></div>
                      <div class="tipo-item"><i class="pi pi-clock" style="color:var(--p-orange-500)"></i><strong>Desp. Previstas</strong><span>A pagar pendentes</span></div>
                      <div class="tipo-item"><i class="pi pi-chart-line" style="color:var(--p-purple-500)"></i><strong>Saldo</strong><span>Resultado acumulado do dia</span></div>
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="conciliacao">
                <p-accordion-header><i class="pi pi-check-square ico-azul"></i>&nbsp; Conciliação Bancária</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Comparação entre o extrato bancário exportado pelo banco e os lançamentos cadastrados no sistema.</p>
                    <strong>Como conciliar:</strong>
                    <ol>
                      <li>Exporte o extrato do banco em formato <strong>OFX</strong> (recomendado) ou <strong>CSV</strong></li>
                      <li>Selecione a conta bancária no filtro superior</li>
                      <li>Clique em <strong>Importar OFX</strong> ou <strong>Importar CSV</strong></li>
                      <li>Para cada transação pendente, escolha uma ação:
                        <ul>
                          <li><strong>Conciliar</strong> — vincula a transação a um lançamento existente (o sistema sugere automaticamente)</li>
                          <li><strong>Lançamento</strong> — cria um novo lançamento e já concilia</li>
                          <li><strong>Ignorar</strong> — marca a transação como verificada sem vincular</li>
                        </ul>
                      </li>
                    </ol>
                    <p-divider />
                    <strong>Status das transações:</strong>
                    <div class="tipos-grid">
                      <div class="tipo-item"><i class="pi pi-clock" style="color:var(--p-orange-500)"></i><strong>Pendente</strong><span>Aguardando análise</span></div>
                      <div class="tipo-item"><i class="pi pi-check-circle" style="color:var(--p-green-500)"></i><strong>Conciliada</strong><span>Vinculada a lançamento</span></div>
                      <div class="tipo-item"><i class="pi pi-minus-circle" style="color:var(--p-surface-400)"></i><strong>Ignorada</strong><span>Verificada e descartada</span></div>
                    </div>
                    <div class="dica-box">
                      <i class="pi pi-lightbulb"></i>
                      Qualquer usuário com acesso à empresa pode ver e conciliar as importações da conta, independente de quem fez o upload.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="cartao">
                <p-accordion-header><i class="pi pi-credit-card ico-roxo"></i>&nbsp; Cartão de Crédito e Faturas</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>O sistema trata cartões de crédito de forma especial: as compras alimentam uma <strong>fatura aberta</strong> e a saída de caixa real ocorre apenas no pagamento da fatura.</p>
                    <strong>Fluxo do cartão:</strong>
                    <ol>
                      <li>Cadastre o cartão em <strong>Cadastros → Contas/Cartões</strong> com dia de fechamento e dia de vencimento</li>
                      <li>Ao lançar uma despesa, selecione o cartão como conta — a compra entra na <strong>fatura aberta</strong> do mês</li>
                      <li>No fechamento do mês, feche a fatura manualmente em <strong>Contas/Cartões → Faturas</strong></li>
                      <li>Pague a fatura indicando a conta bancária de débito — apenas esse pagamento afeta o saldo</li>
                    </ol>
                    <div class="dica-box">
                      <i class="pi pi-exclamation-triangle"></i>
                      Compras no cartão <strong>não reduzem</strong> o saldo bancário imediatamente. Somente o <strong>pagamento da fatura</strong> gera saída de caixa real.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

            </p-accordion>
          </p-tabpanel>

          <!-- ── CADASTROS ──────────────────────────────────────────────── -->
          <p-tabpanel value="cadastros">
            <p-accordion [multiple]="true" [value]="['categorias']">

              <p-accordion-panel value="categorias">
                <p-accordion-header><i class="pi pi-tags ico-amarelo"></i>&nbsp; Categorias</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Organiza receitas e despesas em hierarquia de até <strong>3 níveis</strong>. Categorias podem ser compartilhadas entre todas as empresas (escopo Global) ou exclusivas de uma empresa.</p>
                    <strong>Plano padrão:</strong>
                    <p>O sistema oferece um plano de contas pré-configurado. Acesse <strong>Categorias → Inicializar Plano Padrão</strong> para criar automaticamente as categorias mais comuns.</p>
                    <strong>Unir categorias (Merge):</strong>
                    <ol>
                      <li>Clique no ícone <i class="pi pi-arrows-h"></i> na categoria de origem</li>
                      <li>Selecione a categoria de destino</li>
                      <li>Confirme — todos os lançamentos migram para o destino e a origem é inativada</li>
                    </ol>
                    <div class="dica-box">
                      <i class="pi pi-exclamation-triangle"></i>
                      O merge é irreversível. A categoria de origem é inativada e não pode ser revertida automaticamente.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="contatos">
                <p-accordion-header><i class="pi pi-users ico-azul"></i>&nbsp; Clientes e Fornecedores</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Cadastro unificado de clientes e fornecedores — Pessoa Jurídica (CNPJ) ou Física (CPF).</p>
                    <strong>Escopo:</strong>
                    <ul>
                      <li><strong>Global:</strong> disponível para todas as empresas do grupo</li>
                      <li><strong>Específico:</strong> exclusivo de uma empresa</li>
                    </ul>
                    <p-divider />
                    <strong>Autopreenchimento por CNPJ <span class="tag-novo">NOVO</span></strong>
                    <p>Ao cadastrar um contato <strong>Pessoa Jurídica</strong>, digite o CNPJ e clique no botão <i class="pi pi-search cor-azul"></i> <strong>Consultar</strong> ao lado do campo. O sistema busca os dados na Receita Federal (via BrasilAPI) e preenche automaticamente <strong>razão social, nome fantasia, e-mail, telefone e endereço completo</strong>.</p>
                    <div class="dica-box">
                      <i class="pi pi-lightbulb"></i>
                      A consulta só preenche campos que vieram com valor — não apaga nada que você já tenha digitado. Disponível apenas para CNPJ (PJ).
                    </div>
                    <p-divider />
                    <strong>Unir contatos (Merge):</strong>
                    <ol>
                      <li>Clique no ícone <i class="pi pi-arrows-h"></i> no contato de origem</li>
                      <li>Selecione o contato de destino</li>
                      <li>Confirme — todos os lançamentos migram e o contato de origem é inativado</li>
                    </ol>
                    <div class="dica-box">
                      <i class="pi pi-lightbulb"></i>
                      Use o Merge para eliminar duplicatas criadas por importações ou cadastros manuais diferentes para o mesmo cliente.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="contas">
                <p-accordion-header><i class="pi pi-credit-card ico-verde"></i>&nbsp; Contas e Cartões</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <strong>Tipos disponíveis:</strong>
                    <div class="tipos-grid">
                      <div class="tipo-item"><i class="pi pi-building-columns"></i><strong>Conta Corrente</strong><span>Conta bancária principal com cheques e débitos</span></div>
                      <div class="tipo-item"><i class="pi pi-piggy-bank"></i><strong>Poupança</strong><span>Conta de poupança com rendimento mensal</span></div>
                      <div class="tipo-item"><i class="pi pi-box"></i><strong>Caixinha</strong><span>Dinheiro em espécie / fundo de caixa</span></div>
                      <div class="tipo-item"><i class="pi pi-chart-pie"></i><strong>Aplicação</strong><span>CDB, fundos de investimento, renda fixa</span></div>
                      <div class="tipo-item"><i class="pi pi-credit-card"></i><strong>Cartão de Crédito</strong><span>Fatura fechada automaticamente por competência</span></div>
                    </div>
                    <p-divider />
                    <strong>Saldo inicial:</strong>
                    <p>Ao cadastrar uma conta, informe o <strong>Saldo Inicial</strong> e a <strong>Data do Saldo</strong>. O sistema usa esses valores como ponto de partida para o cálculo do saldo real, ignorando movimentações anteriores à data informada.</p>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="patrimonial">
                <p-accordion-header><i class="pi pi-building ico-amarelo"></i>&nbsp; Patrimonial</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Controle de bens patrimoniais da empresa: imóveis e veículos.</p>
                    <div class="dois-cols">
                      <div>
                        <strong>Imóveis:</strong>
                        <ul>
                          <li>Cadastre endereço completo, matrícula e inscrição municipal</li>
                          <li>Registre valor de aquisição, valor de mercado e valor venal</li>
                          <li>Múltiplas matrículas por imóvel (cartório, prefeitura)</li>
                          <li>Status: Ativo, Locado, Em Reforma, Vendido, Inativo</li>
                          <li>Anexe documentos: escrituras, IPTU, fotos</li>
                        </ul>
                      </div>
                      <div>
                        <strong>Veículos:</strong>
                        <ul>
                          <li>Placa, RENAVAM, chassi, número do motor</li>
                          <li>Marca, modelo, ano de fabricação e ano do modelo</li>
                          <li>Quilometragem e combustível</li>
                          <li>Valor de aquisição e valor de mercado atual</li>
                          <li>Status: Ativo, Vendido, Sinistrado, Inativo</li>
                          <li>Anexe documentos: CRV, CRLV, laudos</li>
                        </ul>
                      </div>
                    </div>
                    <div class="dica-box">
                      <i class="pi pi-lightbulb"></i>
                      Todos os usuários com acesso à empresa podem visualizar e editar os bens patrimoniais, independentemente de quem os cadastrou.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="importacao">
                <p-accordion-header><i class="pi pi-upload ico-azul"></i>&nbsp; Importação em Lote</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Importa lançamentos financeiros em massa a partir de planilha Excel.</p>
                    <strong>Como importar:</strong>
                    <ol>
                      <li>Acesse <strong>Administração → Importação</strong></li>
                      <li>Faça download do modelo de planilha para ver o formato correto</li>
                      <li>Preencha a planilha com os lançamentos</li>
                      <li>Faça upload do arquivo Excel</li>
                      <li>Mapeie as colunas da planilha para os campos do sistema</li>
                      <li>Revise o preview e confirme a importação</li>
                    </ol>
                    <strong>Campos reconhecidos:</strong>
                    <ul>
                      <li><strong>CAP/CAR:</strong> identifica se é despesa (CAP) ou receita (CAR)</li>
                      <li><strong>Titular:</strong> nome da empresa — identifica para qual empresa importar</li>
                      <li><strong>Categoria e Fornecedor:</strong> criados automaticamente se não existirem</li>
                    </ul>
                    <div class="dica-box">
                      <i class="pi pi-exclamation-triangle"></i>
                      Revise sempre o preview antes de confirmar. A importação cria lançamentos em status <strong>Pendente</strong> que podem ser editados individualmente depois.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

            </p-accordion>
          </p-tabpanel>

          <!-- ── ADMINISTRAÇÃO ──────────────────────────────────────────── -->
          <p-tabpanel value="admin">
            <p-accordion [multiple]="true" [value]="['usuarios']">

              <p-accordion-panel value="usuarios">
                <p-accordion-header><i class="pi pi-user-edit ico-roxo"></i>&nbsp; Usuários e Perfis</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <strong>Três perfis de acesso:</strong>
                    <div class="tipos-grid">
                      <div class="tipo-item">
                        <i class="pi pi-star" style="color:var(--p-yellow-500)"></i>
                        <strong>Admin</strong>
                        <span>Acesso total irrestrito ao sistema</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-shield" style="color:var(--p-blue-500)"></i>
                        <strong>Gestor</strong>
                        <span>Cria usuários e configura permissões</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-user" style="color:var(--p-surface-500)"></i>
                        <strong>Usuário</strong>
                        <span>Acesso conforme permissões individuais liberadas</span>
                      </div>
                    </div>
                    <p-divider />
                    <strong>Ações disponíveis na tabela de usuários:</strong>
                    <ul>
                      <li><i class="pi pi-shield"></i> <strong>Permissões de telas</strong> — matriz de menus × ações (ver, criar, editar, excluir)</li>
                      <li><i class="pi pi-building"></i> <strong>Acesso a empresas</strong> — define quais empresas do grupo o usuário pode visualizar</li>
                      <li><i class="pi pi-user-plus"></i> / <i class="pi pi-user-minus"></i> <strong>Promover/remover Gestor</strong> — exclusivo do Admin</li>
                      <li><i class="pi pi-ban"></i> / <i class="pi pi-check-circle"></i> <strong>Inativar/Reativar</strong> — desativa sem excluir</li>
                    </ul>
                    <p-divider />
                    <strong>Alterar sua senha:</strong>
                    <p>Clique nas suas iniciais no canto superior direito do header.</p>
                    <p-divider />
                    <strong>Sessão e segurança <span class="tag-novo">NOVO</span></strong>
                    <ul>
                      <li>A sessão expira automaticamente após <strong>2 horas</strong> de validade do login.</li>
                      <li>Quando o acesso expira, o sistema <strong>redireciona para a tela de login</strong> automaticamente na próxima ação.</li>
                      <li>O acesso é feito por <strong>conexão segura (HTTPS)</strong> — o cadeado aparece na barra do navegador.</li>
                    </ul>
                    <div class="dica-box">
                      <i class="pi pi-info-circle"></i>
                      Novos usuários iniciam <strong>sem nenhum acesso</strong>. O Admin ou Gestor precisa liberar as permissões e os acessos às empresas explicitamente.
                    </div>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="permissoes">
                <p-accordion-header><i class="pi pi-lock ico-roxo"></i>&nbsp; Permissões</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>A matriz de permissões controla o que cada usuário pode fazer em cada módulo do sistema.</p>
                    <div class="permissoes-exemplo">
                      <div class="perm-linha header">
                        <span>Módulo</span><span>Visualizar</span><span>Criar</span><span>Editar</span><span>Excluir</span>
                      </div>
                      <div class="perm-linha">
                        <span>Lançamentos</span>
                        <i class="pi pi-check cor-verde"></i><i class="pi pi-check cor-verde"></i>
                        <i class="pi pi-check cor-verde"></i><i class="pi pi-times cor-vermelho"></i>
                      </div>
                      <div class="perm-linha">
                        <span>Configurações</span>
                        <i class="pi pi-times cor-vermelho"></i><i class="pi pi-times cor-vermelho"></i>
                        <i class="pi pi-times cor-vermelho"></i><i class="pi pi-times cor-vermelho"></i>
                      </div>
                    </div>
                    <p-divider />
                    <ul>
                      <li>Novo usuário inicia <strong>sem nenhum acesso</strong></li>
                      <li>Use <strong>"Selecionar coluna"</strong> para liberar uma ação em todos os módulos de uma vez</li>
                      <li>Use <strong>"Selecionar linha"</strong> para liberar todas as ações de um módulo</li>
                      <li>Permissões são independentes por usuário — sem perfis fixos ou grupos</li>
                    </ul>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="historico">
                <p-accordion-header><i class="pi pi-history ico-azul"></i>&nbsp; Histórico de Alterações</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>Registra automaticamente todas as alterações feitas em lançamentos financeiros e transferências.</p>
                    <strong>Como consultar:</strong>
                    <ol>
                      <li>Abra a lista de Contas a Pagar ou Receber</li>
                      <li>Clique no ícone <i class="pi pi-history"></i> no lançamento</li>
                      <li>O painel exibe cada alteração com: data, hora, campo modificado, valor anterior e valor novo</li>
                    </ol>
                    <strong>Eventos registrados:</strong>
                    <ul>
                      <li>
                        <p-tag value="INSERT" severity="success" /> Criação do lançamento
                      </li>
                      <li>
                        <p-tag value="UPDATE" severity="info" /> Qualquer alteração de campo
                      </li>
                      <li>
                        <p-tag value="DELETE" severity="danger" /> Inativação / cancelamento
                      </li>
                    </ul>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="empresas">
                <p-accordion-header><i class="pi pi-building ico-verde"></i>&nbsp; Empresas</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <p>O sistema suporta múltiplas empresas (PJ ou PF) operadas pelo mesmo grupo. Cada empresa tem seus dados independentes.</p>
                    <strong>Tipos:</strong>
                    <div class="tipos-grid">
                      <div class="tipo-item">
                        <i class="pi pi-building"></i>
                        <strong>Pessoa Jurídica</strong>
                        <span>Campos CNPJ com máscara, razão social e nome fantasia</span>
                      </div>
                      <div class="tipo-item">
                        <i class="pi pi-user"></i>
                        <strong>Pessoa Física</strong>
                        <span>Campos CPF com máscara e nome completo</span>
                      </div>
                    </div>
                    <p-divider />
                    <strong>Cadastros compartilhados:</strong>
                    <p>Categorias e Contatos com escopo <strong>Global</strong> são visíveis em todas as empresas. Com escopo <strong>Específico</strong>, ficam restritos à empresa escolhida.</p>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

              <p-accordion-panel value="config">
                <p-accordion-header><i class="pi pi-cog ico-cinza"></i>&nbsp; Configurações</p-accordion-header>
                <p-accordion-content>
                  <div class="accordion-content">
                    <ul>
                      <li><strong>Dados da empresa:</strong> razão social, CNPJ/CPF, endereço, logo e identidade visual</li>
                      <li><strong>Trava de fechamento:</strong> define o mês/data até onde os lançamentos estão protegidos contra edição acidental. Usuários com permissão especial ainda podem editar lançamentos travados.</li>
                      <li><strong>Moeda:</strong> Real (BRL) — padrão do sistema</li>
                      <li><strong>Regime:</strong> Caixa — data do pagamento/recebimento define a competência</li>
                    </ul>
                  </div>
                </p-accordion-content>
              </p-accordion-panel>

            </p-accordion>
          </p-tabpanel>

          <!-- ── DICAS ──────────────────────────────────────────────────── -->
          <p-tabpanel value="dicas">
            <div class="dicas-container">

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-chevron-left cor-azul"></i> Menu recolhível</div>
                <p>Clique na seta na borda direita da sidebar para recolher o menu e ganhar espaço na tela. Os ícones permanecem visíveis com tooltip ao passar o mouse.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-moon cor-roxo"></i> Modo escuro</div>
                <p>Clique na lua no header para alternar entre tema claro e escuro. A preferência é salva e restaurada automaticamente na próxima visita.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-tags cor-azul"></i> Tags em lançamentos</div>
                <p>Adicione tags livres nos lançamentos (ex: "urgente", "projeto-abc") para classificação personalizada além das categorias hierárquicas.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-copy cor-verde"></i> Duplicar lançamento</div>
                <p>Clique no ícone de cópia em qualquer lançamento para criar uma cópia rapidamente. Útil para lançamentos repetidos que não se encaixam em recorrências fixas.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-file-excel cor-verde"></i> Exportar Excel e PDF</div>
                <p>Botões de exportação no topo de Contas a Pagar/Receber baixam os lançamentos filtrados em Excel ou PDF com totais de receitas e despesas.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-arrows-h cor-azul"></i> Merge de categorias e contatos</div>
                <p>Encontrou duplicatas? Use o ícone ↔ para unir dois registros. Todos os lançamentos migram automaticamente para o destino.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-receipt cor-azul"></i> Extrato Bancário</div>
                <p>Acesse Financeiro → Extrato Bancário para ver o saldo progressivo de qualquer conta. É possível efetivar lançamentos pendentes diretamente pelo extrato sem voltar à lista.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-exclamation-circle cor-vermelho"></i> Tela de Inadimplência</div>
                <p>Acesse Financeiro → Inadimplência para ver todas as contas a receber vencidas agrupadas por cliente. Exporte para Excel para controle externo.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-history cor-roxo"></i> Histórico de alterações</div>
                <p>Clique no ícone de relógio em qualquer lançamento para ver um log completo de modificações: quem alterou, quando, campo e valor anterior.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-shield cor-azul"></i> Perfil Gestor</div>
                <p>Crie usuários com perfil Gestor para delegar a criação de usuários e configuração de permissões sem conceder acesso total de Admin.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-building cor-verde"></i> Acesso por empresa</div>
                <p>Em Usuários → ícone de empresa, defina quais CNPJs/CPFs cada usuário pode ver. Ideal para equipes que gerenciam apenas uma empresa do grupo.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-calendar cor-azul"></i> Navegar entre meses</div>
                <p>Clique no ícone de calendário ao lado das setas de mês para ir direto a qualquer mês/ano sem precisar avançar um a um.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-lock cor-amarelo"></i> Trava de fechamento</div>
                <p>Configure a data de fechamento em Configurações. Lançamentos anteriores à data ficam protegidos. Somente usuários com permissão especial podem editá-los.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-check-square cor-azul"></i> Conciliação OFX</div>
                <p>Exporte o extrato do banco em OFX e importe na Conciliação Bancária. O sistema sugere automaticamente quais lançamentos correspondem a cada transação do extrato.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-credit-card cor-roxo"></i> Cartão de crédito</div>
                <p>Compras no cartão não reduzem o saldo bancário. Apenas o pagamento da fatura gera saída de caixa. Configure o dia de fechamento e vencimento no cadastro do cartão.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-search cor-azul"></i> Consulta de CNPJ</div>
                <p>No cadastro de um fornecedor PJ, digite o CNPJ e clique em <strong>Consultar</strong>: razão social, nome fantasia, e-mail, telefone e endereço são preenchidos automaticamente a partir da Receita Federal.</p>
              </div>

              <div class="dica-card">
                <div class="dica-title"><i class="pi pi-lock cor-verde"></i> Conexão segura</div>
                <p>O sistema roda em HTTPS (cadeado no navegador). Sua sessão expira após 2 horas e você é levado de volta ao login automaticamente — basta entrar de novo.</p>
              </div>

            </div>
          </p-tabpanel>

        </p-tabpanels>
      </p-tabs>
    </div>
  `,
  styles: [`
    .ajuda-container { padding: 1.5rem; max-width: 1100px; margin: 0 auto; }

    .ajuda-header {
      display: flex; align-items: center; gap: 1rem;
      margin-bottom: 1.5rem; padding-bottom: 1rem;
      border-bottom: 2px solid var(--p-primary-color);
    }
    .ajuda-header .header-icon { font-size: 2.5rem; color: var(--p-primary-color); }
    .ajuda-header h1 { margin: 0; font-size: 1.6rem; color: var(--p-surface-900); }
    .ajuda-header p { margin: 0.2rem 0 0; color: var(--p-surface-500); }

    .accordion-content { padding: 0.5rem 0; }
    .accordion-content ul, .accordion-content ol { padding-left: 1.4rem; }
    .accordion-content li { margin-bottom: 0.35rem; }

    .dois-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }

    .tipos-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 0.75rem; margin: 0.75rem 0; }
    .tipo-item {
      display: flex; flex-direction: column; align-items: center; gap: 0.3rem;
      padding: 0.75rem; border: 1px solid var(--p-surface-200);
      border-radius: 8px; text-align: center;
    }
    .tipo-item i { font-size: 1.4rem; color: var(--p-primary-color); }
    .tipo-item strong { font-size: 0.85rem; }
    .tipo-item span { font-size: 0.75rem; color: var(--p-surface-500); }

    .dica-box {
      background: var(--p-yellow-50); border-left: 4px solid var(--p-yellow-400);
      padding: 0.75rem 1rem; border-radius: 0 6px 6px 0;
      margin-top: 1rem; font-size: 0.9rem; display: flex; gap: 0.5rem; align-items: flex-start;
    }
    .dica-box i { color: var(--p-yellow-600); margin-top: 0.1rem; flex-shrink: 0; }

    .hierarquia { margin: 0.75rem 0; display: flex; flex-direction: column; gap: 0.4rem; }
    .nivel1 { display: flex; align-items: center; gap: 0.5rem; padding: 0.3rem 0; }

    .permissoes-exemplo { border: 1px solid var(--p-surface-200); border-radius: 6px; overflow: hidden; margin: 0.75rem 0; }
    .perm-linha { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; padding: 0.5rem 1rem; align-items: center; }
    .perm-linha.header { background: var(--p-surface-100); font-weight: 600; font-size: 0.85rem; }
    .perm-linha:not(.header) { border-top: 1px solid var(--p-surface-100); }

    .dicas-container { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }
    .dica-card { background: var(--p-surface-0); border: 1px solid var(--p-surface-200); border-radius: 10px; padding: 1.2rem; }
    .dica-title { display: flex; align-items: center; gap: 0.5rem; font-weight: 700; margin-bottom: 0.5rem; font-size: 1rem; }
    .dica-card p { margin: 0; color: var(--p-surface-600); font-size: 0.9rem; line-height: 1.5; }

    .tag-laranja { background: var(--p-orange-100); color: var(--p-orange-700); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
    .tag-vermelho { background: var(--p-red-100); color: var(--p-red-700); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
    .tag-novo { background: var(--p-green-500); color: #fff; padding: 0.05rem 0.4rem; border-radius: 10px; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.04em; vertical-align: middle; margin-left: 0.35rem; }

    .ico { color: var(--p-primary-color); }
    .ico-despesa { color: var(--p-red-500); }
    .ico-azul { color: var(--p-blue-500); }
    .ico-verde { color: var(--p-green-500); }
    .ico-amarelo { color: var(--p-yellow-600); }
    .ico-roxo { color: var(--p-purple-500); }
    .ico-cinza { color: var(--p-surface-500); }
    .cor-azul { color: var(--p-blue-500); }
    .cor-verde { color: var(--p-green-500); }
    .cor-vermelho { color: var(--p-red-500); }
    .cor-amarelo { color: var(--p-yellow-600); }
    .cor-roxo { color: var(--p-purple-500); }

    @media (max-width: 768px) {
      .dois-cols { grid-template-columns: 1fr; }
    }
  `],
})
export class AjudaComponent {
  protected abaAtiva = signal('interface');
}
