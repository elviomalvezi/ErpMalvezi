# ErpMalvezi — Plano de Desenvolvimento em Fases

Detalhamento operacional das fases de desenvolvimento do **produto base ErpMalvezi** — genérico e parametrizável, para qualquer cliente. O primeiro projeto de cliente (8 módulos, meta 3–4 meses) valida a sequência e o prazo, mas as entregas são sempre do produto. Cada fase lista objetivo, entregas, entidades novas, critérios de aceite e estimativa. As estimativas assumem 1 desenvolvedor full-time apoiado por IA; ajustar conforme a realidade.

**Entrega transversal — produto demonstrável**: ao fim de **cada fase**, o ambiente de demonstração é atualizado: empresas fictícias (uma PJ comércio, uma PJ serviços/locação, uma PF), dados de exemplo realistas (seed idempotente `scripts/seed_demo.py`), e roteiro de demo cobrindo o que a fase entregou. O produto está **sempre pronto para apresentação a prospects** — nunca "em obra".

**Convenções em todas as fases**: `empresa_id` obrigatório, UUID v7, `decimal(15,2)`, soft delete, auditoria, permissões novas registradas na matriz de menus (migration), PT-BR na interface, testes de service para cada regra de negócio.

---

## Visão geral do cronograma

| Fase | Entrega | Estimativa | Acumulado |
|------|---------|-----------|-----------|
| 0 | Plataforma pronta p/ multi-empresa em abas + base técnica | 3 semanas | 3 sem |
| 1 | Cadastros (produtos, centros de custo, SPC) | 2 semanas | 5 sem |
| 1b | Integração bancária (Cora + CNAB) — paralelizável | 2 semanas | — |
| 2 | Estoque (com armazém virtual e nº de série) | 3 semanas | 8 sem |
| 3 | Compras (SC → cotação → pedido → alçada → XML) | 4 semanas | 12 sem |
| 4 | Vendas (orçamento template → pedido → faturamento) | 4 semanas | 16 sem |
| 5 | Fiscal (emissão + DF-e + manifestação + NFS-e) | 3 semanas | 19 sem* |
| 6 | Serviços e Locação (OS, contratos, armazém virtual) | 3 semanas | 22 sem* |
| 7 | Relatórios e painéis | 1 semana | 23 sem* |

\* Fases 5 e 6 têm forte potencial de paralelização com 4 e entre si (o adapter fiscal pode começar junto com Vendas). Com paralelização, o total comprime para **~16–18 semanas (~4 meses)** — no limite da meta Pavani; o caminho crítico é Compras + Vendas.

Opcionais (contratação à parte): CRM (+RD Station), IA (+medição de consumo), Contabilidade, RH/Folha, Gestão de Contratos, Produção.

---

## Fase 0 — Consolidação e plataforma multi-empresa (3 semanas)

**Objetivo**: preparar a base técnica e entregar a experiência multi-empresa prometida (abas por empresa) antes de qualquer módulo novo — ela afeta o layout de todas as telas.

**Entregas**
1. **CI** (GitHub Actions): lint (ruff) + mypy + pytest no backend; build + testes no frontend; bloqueio de merge com falha. Corrigir os 21 testes quebrados pelo ambiente (mocks × Python 3.14/pytest 9).
2. **Reorganização por domínio**: mover `app/modules/<modulo>` para `app/modules/<dominio>/<modulo>` (plataforma, financeiro, cadastros); frontend espelha em `features/<dominio>/`. Migração mecânica, sem mudança de comportamento — cobertura de testes garante.
3. **Campo `codigo` na empresa** (migration + telas) e **flags de domínios habilitados por empresa** (`empresa_dominio`).
4. **Tela de entrada**: data base + empresa por código + módulo; contexto no header, trocável sem relogar.
5. **Navegação por abas de empresa** (preferência por usuário): barra de abas com as empresas acessíveis; cada aba mantém o contexto do módulo; garantia de que todo request carrega o `empresa_id` da aba ativa (interceptor + validação backend).
6. **Administração de acessos**: árvore módulo → menu → ações, concessão por empresa ou global, cópia entre usuários.
7. **Seed de demonstração** (`scripts/seed_demo.py`): empresas fictícias + usuários + dados financeiros de exemplo — base do ambiente de apresentação, evoluída a cada fase.

**Critérios de aceite**: usuária alterna entre 2 empresas em abas sem relogar e sem vazamento de contexto (lançamento nasce sempre na empresa da aba ativa); usuário novo não vê nada até receber acesso; CI verde.

---

## Fase 1 — Cadastros (2 semanas)

**Objetivo**: dados mestres que todos os módulos seguintes consomem.

**Entregas**
1. `produto` (tipos produto/serviço/kit/imobilizado; NCM, CFOP, CSTs legados + CST-IBS/CBS e cClassTrib; controla_estoque; escopo global/específico), `unidade` (com conversões), `tabela_preco`, `transportadora`.
2. `produto_fornecedor` (código/descrição no fornecedor, unidade + fator de conversão, último preço, prazo).
3. `centro_custo` (hierárquico simples) + campo opcional `centro_custo_id` no lançamento financeiro (migration + tela + relatório por centro de custo no financeiro atual).
4. **Adapter `CreditoProvider`** + implementação SPC (consulta do cadastro do cliente; resultado aritmético exibido, decisão manual). Mock provider para dev/testes.
5. **Cadastro configurável de provedores de crédito** (`provedor_credito` por empresa): tipo **SPC ou Serasa**, credenciais cifradas (Fernet), ambiente, ativo; **limite mensal de consultas com alerta** (bureau cobra por consulta) e **log de consultas** (quem/quando/cliente/resultado — atende LGPD). As telas usam o provedor ativo da empresa.

**Critérios de aceite**: produto cadastrado com dados fiscais completos; despesa lançada com centro de custo aparece no relatório; consulta SPC retorna e fica registrada no histórico do cliente.

---

## Fase 1b — Integração bancária (2 semanas, paralelizável com 1–2)

**Objetivo**: cobrança registrada e baixa automática — valor imediato para o financeiro já em produção.

**Entregas**
1. Adapter `CobrancaProvider`; entidades `cobranca_titulo` (vínculo com lançamento), eventos de registro/liquidação/baixa.
1b. **Configuração de API no cadastro de contas**: aba "Integração" na conta bancária (`integracao_bancaria`: provedor nenhuma/cora/cnab240, ambiente, credenciais **cifradas com Fernet** — mesmo padrão do módulo de certificados —, webhook secret, teste de conexão). O adapter resolve a implementação pela configuração da conta; permissão própria na matriz; credencial nunca retorna ao frontend após salva.
2. **`CoraCobranca`**: emissão de boleto registrado com Pix híbrido via API (OAuth2 + mTLS), webhook de liquidação → baixa automática do título.
3. **`Cnab240Cobranca`**: geração de remessa e leitura de retorno (banco de maior volume primeiro), conciliação de ocorrências.
4. Remessa de **pagamento** CNAB 240 (fase inicial: fornecedores) com retorno → baixa.

**Critérios de aceite**: título emitido no Cora sandbox liquida via webhook e baixa sozinho; remessa CNAB validada no validador do banco homologado.

---

## Fase 2 — Estoque (3 semanas)

**Objetivo**: saldos confiáveis, incluindo os depósitos virtuais que sustentam a locação.

**Entregas**
1. `deposito` (físico e **virtual**: locação, manutenção), `estoque_saldo`, `estoque_movimentacao` (entrada, saída, ajuste, transferência — atômicas).
2. **Número de série**: `produto_serie` (opcional por produto), rastreio de série por movimentação e por depósito.
3. Custo médio por empresa; inventário (contagem, divergência, acerto); estoque mínimo → gera sugestão de solicitação de compra (consumida na Fase 3).
4. Motor de **transferência por evento** (API interna): reserva/efetiva/retorna entre depósitos — será chamado por Vendas (Fase 4) e Locação (Fase 6).

**Critérios de aceite**: transferência entre depósitos nunca deixa saldo inconsistente (teste de concorrência); série individual localizável ("onde está o equipamento X?"); custo médio recalcula corretamente em entradas sucessivas.

---

## Fase 3 — Compras (4 semanas)

**Objetivo**: ciclo completo de entrada — da solicitação ao contas a pagar — com governança de alçada.

**Entregas**
1. `solicitacao_compra` (manual + gerada por estoque mínimo).
2. `cotacao` (mapa comparativo N fornecedores, sugestão de vencedor + justificativa registrada, vencedor por item/global).
3. `pedido_compra` (centro de custo obrigatório por item; destino estoque/imobilizado; TES de entrada).
4. **Alçadas**: `grupo_aprovacao` + níveis + aprovadores (com substituto/vigência); fluxo sequencial, rejeição com motivo, reinício em alteração de valor, painel multi-empresa de pendências, notificação ao aprovador.
5. **Recebimento**: contra pedido (tolerâncias) → entrada de estoque (custo formado) + contas a pagar (parcelas) + ativação no Patrimonial quando imobilizado.
6. **Importação de XML de NF-e** (upload): parser, de-para `produto_fornecedor` com aprendizado, duplicatas → parcelas, impostos capturados e classificados pela TES (crédito × custo). Parâmetro por empresa "nota exige pedido".

**Critérios de aceite**: pedido acima da alçada do nível 1 sobe ao nível 2; XML real de fornecedor entra sem redigitação com estoque e financeiro corretos; parâmetro "nota exige pedido" bloqueia XML órfão.

---

## Fase 4 — Vendas e Faturamento (4 semanas)

**Objetivo**: ciclo de receita completo, com o documento que chega ao cliente final impecável.

**Entregas**
1. **Motor de templates de documentos** (por empresa e tipo de documento; HTML → PDF): base para orçamento, OS e futuros. Template padrão + template personalizado por cliente do ErpMalvezi.
2. `orcamento` (versões, validade, PDF com foto e especificação técnica por item, envio por link/e-mail) → conversão em pedido.
3. `pedido_venda` (reserva de estoque via motor da Fase 2; análise de crédito: limite + inadimplência + consulta SPC; TES de saída).
4. **Motor de impostos de saída**: ICMS/ST/DIFAL, IPI, PIS/COFINS + IBS/CBS (NT 2025.002) parametrizado por produto/TES/regime/UFs/cliente — cálculo exibido no pedido antes de faturar.
5. **Faturamento total/parcial** → contas a receber (condição de pagamento), baixa de estoque (com série), fila para emissão fiscal (Fase 5).
6. `comissao` (por vendedor, base configurável, liquidação sobre recebido) + separação de vendas por comissão; `devolucao` referenciada com estornos proporcionais.

**Critérios de aceite**: orçamento em PDF com layout do cliente aprovado; pedido de cliente inadimplente bloqueia; faturamento parcial mantém saldo do pedido; comissão só liquida quando o título é recebido.

---

## Fase 5 — Fiscal (3 semanas; adapter pode iniciar em paralelo à Fase 4)

**Objetivo**: Central Fiscal multi-CNPJ — tudo via API de terceiros, sem middleware local.

**Entregas**
1. Seleção e contratação do provedor (critérios: NT 2025.002, Emissor Nacional NFS-e, DF-e, preço/nota) + adapter `EmissorFiscal`.
2. **Emissão NF-e** a partir do faturamento; eventos: CC-e, cancelamento, inutilização; DANFE; travamento do documento de origem.
3. **NFS-e padrão nacional** (Emissor Nacional/ADN) para faturamento de serviços.
4. **Monitor DF-e** por CNPJ (agendado): resumos, manifestação com controle de prazo, download de XML → fila de importação de Compras; guarda no storage (5+ anos) com busca.
5. Exportação para o contador (XMLs + relatórios por período).

**Critérios de aceite**: nota emitida e autorizada em homologação nos 2 CNPJs de teste; nota de fornecedor aparece no monitor e flui até o estoque; cancelamento/CC-e funcionando; nenhum XML fora do nosso storage.

---

## Fase 6 — Serviços e Locação (3 semanas; paralelizável com Fase 5)

**Objetivo**: OS, contratos e a locação com armazém virtual — o diferencial do produto.

**Entregas**
1. **Abas por natureza**: OS (manutenção) × Contratos (locação) × Vendas de serviço.
2. `ordem_servico`: fluxo abertura → execução → faturamento; ficha técnica completa (equipamento marca/modelo/série, condições de chegada, defeitos, acessórios, solução, peças — baixa estoque — e mão de obra); **template de OS personalizado** (motor da Fase 4).
3. `contrato_locacao` (itens com equipamento/série, período, valor; reajuste por índice) + **agenda de disponibilidade** (bloqueio de dupla locação).
4. Integração com o **armazém virtual** (Fase 2): pedido reserva → faturamento move para depósito de locados → devolução (com vistoria/checklist e cobrança de avaria) retorna ao disponível; mesmo fluxo para manutenção interna.
5. Faturamento recorrente de contratos (motor de recorrência existente) → contas a receber; fatura de locação (sem ISS — Súmula 31) separada de NFS-e de serviços acoplados.
6. **Retorno por equipamento**: receita de locação × custo/manutenção por série.

**Critérios de aceite**: mesmo equipamento não loca duas vezes no mesmo período; ciclo completo reserva → locação → devolução → disponível refletido nos saldos; contrato mensal fatura sozinho; relatório de retorno por equipamento correto.

---

## Fase 7 — Relatórios e painéis (1 semana)

Painel consolidado e por empresa (vendas, estoque, locação, caixa); vendas por comissão; inadimplência; retorno por equipamento; exportação Excel/PDF. Aproveita módulo `relatorio` existente.

---

## Fases opcionais (sob contratação)

| Módulo | Pré-requisitos | Estimativa |
|--------|----------------|-----------|
| **CRM** (funil, oportunidades, RD Station) | Fase 4 | 3 semanas |
| **IA** (categorização, leitura de docs, assistente, **medição de consumo com limite/trava**) | núcleo estável | 4 semanas |
| **Contabilidade** (partidas dobradas, balancete, ECD/ECF) | Fases 3–5 | 6 semanas |
| **RH/Folha** (colaboradores → motor de folha → eSocial API) | núcleo | 8+ semanas, em sub-etapas |
| **Gestão de Contratos** (SIGAGCT: medições, aditivos, saldo) | Fases 3–4 | 4 semanas |
| **Produção** (BOM, OP, apontamento) | Fase 2 | 4 semanas |

---

## Implantação (projeto de cliente — modelo Pavani)

Corre em paralelo ao fim do desenvolvimento:

1. **Homologação fiscal** — notas de teste em ambiente oficial, por CNPJ (durante Fase 5).
2. **Configuração do ambiente do cliente** — instância isolada (VM/containers), domínio e SSL do cliente, certificados A1.
3. **Carga assistida de dados** — clientes, fornecedores, produtos, equipamentos (com série), saldos de estoque e títulos em aberto (importadores CSV).
4. **Treinamento presencial** — por área (financeiro, compras/estoque, vendas, fiscal, serviços/locação).
5. **Virada acompanhada** — primeiras notas e faturamentos ao vivo.
6. **Operação assistida (1 mês, remota)** — canal direto, ajustes finos, sistema antigo em paralelo.

## Riscos e mitigação

- **Abas de empresa** afetam todas as telas → por isso estão na Fase 0, antes de qualquer tela nova.
- **Motor de impostos** é o item de maior incerteza técnica (transição da reforma) → começar pelo regime dos primeiros clientes (Simples) e validar com o contador do cliente cedo.
- **Dependências externas** (Cora, SPC, provedor fiscal, certificados) têm lead time de contratação → disparar pedidos de credenciamento na Fase 0, não quando o módulo começar.
- **Prazo Pavani (3–4 meses)** exige paralelização das Fases 5–6 e corte disciplinado de escopo não prometido.
