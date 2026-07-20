# Roadmap ERP — De App Financeiro a ERP completo para PMEs

Este documento define a evolução do App Financeiro para um **ERP modular para pequenas e médias empresas**, mantendo o que já existe como primeiro domínio pronto (Financeiro) e estruturando os demais domínios em cima da mesma plataforma.

## Princípios

1. **Monolito modular** — um único backend FastAPI e um único frontend Angular, com fronteiras de domínio claras. Sem microserviços no horizonte de PME; a separação é lógica (pastas/módulos), não física.
2. **A plataforma já existente é o alicerce** — multi-empresa (PJ/PF), permissões por matriz usuário × menu × ação, auditoria, soft delete, notificações, busca global e storage de anexos servem a **todos** os domínios, não só ao financeiro.
3. **Todo domínio novo conversa com o Financeiro** — venda faturada gera contas a receber; compra recebida gera contas a pagar; folha gera lançamentos. O financeiro é o ponto de convergência do ERP.
4. **Mesmas convenções em tudo** — UUID v7, `empresa_id` obrigatório, `decimal(15,2)`, soft delete, auditoria, PT-BR na interface, código em inglês, módulo = `models.py / schemas.py / repository.py / service.py / routes.py`.

## Mapa de domínios

| # | Domínio | Status | Módulos |
|---|---------|--------|---------|
| 0 | **Plataforma** | ✅ existente | multi-empresa, usuários/auth, permissões, auditoria, notificações, busca, certificado digital, configurações |
| 1 | **Financeiro** | ✅ existente | lançamentos, contas bancárias, cartão/fatura, transferências, conciliação OFX/CSV, fluxo de caixa, inadimplência, extrato, DRE/relatórios, patrimonial, importação. **Evolução planejada — integração bancária**: cobrança registrada (boleto + Pix) e pagamento eletrônico via **CNAB 240 remessa/retorno** com baixa automática; adapter `CobrancaProvider` preparado para API bancária/agregador (PlugBoleto, Kobana) com webhook de liquidação como evolução. **Integração Banco Cora (opcional)**: implementação `CoraCobranca` via API oficial (developers.cora.com.br) — boleto registrado com Pix híbrido, multa/juros/descontos, webhook de liquidação p/ baixa em tempo real; requer plano CoraPro; demanda de cliente em prospecção (jul/2026) |
| 2 | **Cadastros (dados mestres)** | 🔶 parcial | contatos (existe); produtos e serviços (já com campos tributários da reforma: CST-IBS/CBS, cClassTrib), **produtos × fornecedores** (de-para p/ importação de XML e cotações), unidades de medida, tabelas de preço, transportadoras, **centros de custo** (a fazer) |
| 3 | **Estoque** | ⬜ a fazer | depósitos, movimentações, inventário, custo médio, alertas de estoque mínimo |
| 4 | **Compras** | ⬜ a fazer | solicitações, cotações, pedidos de compra (com **centro de custo** por item), **aprovação por alçada** (grupos de aprovação com aprovadores em níveis, estilo Protheus), recebimento de mercadoria, **importação de XML de NF-e** (entrada por XML com de-para de produtos do fornecedor) |
| 5 | **Vendas** | ⬜ a fazer | orçamentos, pedidos de venda, faturamento, comissões, devoluções |
| 6 | **Fiscal** | 🔶 parcial | certificado digital (existe); emissão NF-e / NFS-e, cálculo de impostos, inutilização/cancelamento, exportação para contador, **captura de XML na SEFAZ (Distribuição DF-e) e manifestação do destinatário** (a fazer) |
| 7 | **Contabilidade** | ⬜ a fazer | plano de contas contábil, centros de custo, lançamentos contábeis (partidas dobradas, manuais + automáticos), livro diário e razão, balancete, balanço patrimonial e DRE contábil, encerramento de exercício, SPED Contábil (ECD)/ECF via exportação ou API |
| 8 | **Serviços** | ⬜ a fazer | ordens de serviço, contratos recorrentes, agendamento, **locação de equipamentos** (contratos de locação, disponibilidade/reservas, faturamento recorrente, devolução e manutenção — equipamentos vêm do Patrimonial) |
| 9 | **RH (folha completa)** | ⬜ a fazer | colaboradores, cargos, férias/ausências, cálculo de folha (proventos, descontos, encargos), provisões e lançamentos no financeiro; **eSocial via API de terceiros** (mesma filosofia de adapter do fiscal) |
| 10 | **CRM** | ⬜ por último | funil de vendas, oportunidades, atividades/follow-up, histórico do cliente — decisão de produto: última fase planejada |
| 11 | **Gestão de Contratos** (opcional, estilo SIGAGCT) | ⬜ a fazer | contratos de compra e venda com vigência, cronograma físico-financeiro, **medições** (aprovação → gera pedido/faturamento), aditivos (valor/prazo), reajustes por índice, cauções e garantias, saldo de contrato, alertas de vencimento |
| 12 | **Integração com IA** (opcional, transversal) | ⬜ a fazer | categorização automática de lançamentos, sugestão de conciliação, leitura de documentos (boletos/notas/contratos), assistente de consultas em linguagem natural, previsão de fluxo de caixa, detecção de anomalias |
| 13 | **Produção (PCP light)** (opcional) | ⬜ a fazer | ficha técnica (BOM) com custo do acabado, ordens de produção (reserva/baixa de insumos, entrada do acabado), apontamento e perdas |

**Módulos opcionais** (habilitáveis por empresa/licença): **Contabilidade, RH, CRM, Gestão de Contratos, Integração com IA e Produção**. O núcleo (Cadastros → Estoque → Compras → Vendas → Fiscal + Financeiro/Plataforma) é o produto base.

## Organização do código por domínio

Hoje os módulos ficam achatados em `backend/app/modules/<modulo>`. Com 10 domínios isso vira ruído. Estrutura alvo (migração gradual, sem big bang):

```
backend/app/modules/
├── plataforma/        # usuario, empresa, permissao, auditoria, notificacao, busca, certificado
├── financeiro/        # lancamento, conta_bancaria, fatura, transferencia, conciliacao,
│                      # fluxo_caixa, dashboard, relatorio, patrimonio
├── cadastros/         # contato, pessoa, produto, unidade, tabela_preco, transportadora, centro_custo
├── estoque/           # deposito, movimentacao, inventario
├── compras/           # cotacao, pedido_compra, recebimento
├── vendas/            # orcamento, pedido_venda, faturamento, comissao
├── fiscal/            # nfe, nfse, imposto, exportacao_contabil
├── contabilidade/     # plano_contas, lancamento_contabil, regra_contabilizacao, balancete, encerramento
├── crm/               # funil, oportunidade, atividade
├── servicos/          # ordem_servico, contrato, locacao
└── rh/                # colaborador, cargo, ausencia, folha
```

Frontend espelha a mesma divisão: `src/app/features/<dominio>/<tela>`. O menu lateral e a matriz de permissões passam a ser agrupados por domínio — **cada domínio pode ser habilitado/desabilitado por empresa** (nem toda empresa do dono usa estoque, por exemplo).

## Entrada no sistema (sessão de trabalho)

Após o login, o usuário informa o **contexto da sessão** antes de entrar (fluxo inspirado em ERPs de mercado):

1. **Data base** — default hoje; vira a data padrão de digitação/competência da sessão (não impede lançar em outras datas, apenas preenche).
2. **Empresa** — informada por **código curto** (campo `codigo` na tabela `empresa`, ex.: `001`) com autocomplete por código ou nome. Lembrar a última usada por usuário.
3. **Módulo (domínio)** — qual domínio abrir (Financeiro, Compras, Vendas...). Só aparecem os domínios habilitados para a empresa **e** nos quais o usuário tem ao menos um menu liberado.

O contexto (data base + empresa + módulo) fica visível no header e pode ser trocado sem novo login. O menu lateral mostra apenas os menus do módulo escolhido.

## Administração de acessos (cadastro menu × usuário)

Tela de administração para **associar menus aos usuários**, evoluindo a matriz já existente (`menu`, `menu_acao_disponivel`, `usuario_permissao`):

- Árvore **módulo → menu → ações** (visualizar, incluir, editar, excluir, ações especiais) com marcação em massa por módulo ou por menu.
- Concessão **por empresa** (usuário pode ter acessos diferentes em cada empresa) ou global (todas as empresas do usuário).
- Cópia de acessos de um usuário para outro e, como evolução, **perfis/templates** reutilizáveis.
- Regra mantida: usuário novo nasce **sem nenhum acesso**; admin libera explicitamente. Tudo auditado.

## Integrações entre domínios (o que faz disso um ERP e não apps soltos)

- **Vendas → Financeiro**: faturar pedido gera lançamento(s) de contas a receber (com parcelamento) e, se houver produto, baixa de estoque.
- **Compras → Financeiro + Estoque**: recebimento gera contas a pagar e entrada de estoque com custo.
- **Compras → Patrimonial (ativação de bem)**: item de pedido com destino `imobilizado` não entra no estoque — no recebimento gera **ativo no Patrimonial** com valor de aquisição, nota de origem e centro de custo herdados; contabiliza como imobilizado (não despesa) e alimenta a depreciação e a locação de equipamentos.
- **Vendas/Compras → Fiscal**: pedido faturado emite NF-e/NFS-e; a nota autorizada trava a edição do pedido.
- **Estoque → Contabilidade gerencial**: custo médio alimenta margem por produto no DRE.
- **CRM → Vendas**: oportunidade ganha vira orçamento/pedido com um clique.
- **Serviços → Vendas/Financeiro**: OS concluída fatura como serviço (NFS-e) e gera recebível; contratos geram recorrência (já existe no financeiro).
- **RH → Financeiro**: salários/provisões entram como lançamentos previstos por colaborador.
- **Todos → Contabilidade**: eventos financeiros, fiscais e de folha geram lançamentos contábeis automáticos via regras de contabilização (categoria financeira → conta contábil/centro de custo); lançamentos manuais cobrem o restante.
- Regra geral: documento de origem referencia o lançamento gerado (`origem_tipo` + `origem_id` no lançamento), garantindo rastreabilidade e estorno consistente.

## Novas entidades principais (esboço)

- `produto` (tipo: produto | serviço | kit | **imobilizado**; unidade, ncm, cest, preço de venda, custo, controla_estoque, escopo global/específico como contatos). Produto **não é** ativo: item de compra com destino `imobilizado` gera ativo no Patrimonial no recebimento (ver Integrações).
- `deposito`, `estoque_saldo`, `estoque_movimentacao` (entrada, saída, ajuste, transferência entre depósitos — mesmo padrão atômico das transferências bancárias)
- `pedido_compra`, `pedido_compra_item` (com `centro_custo_id` e `destino`: estoque | imobilizado), `recebimento` — o centro de custo do item acompanha o contas a pagar gerado e a contabilização automática; destino `imobilizado` ativa o bem no Patrimonial
- `solicitacao_compra` + `solicitacao_compra_item` (quem pede, centro de custo, quantidade, justificativa — pode nascer de estoque mínimo ou manual)
- `cotacao` + `cotacao_fornecedor` + `cotacao_item_preco` (uma cotação compara N fornecedores para os itens da(s) solicitação(ões); mapa comparativo escolhe vencedor por item ou global; usa `produto_fornecedor` para sugerir fornecedores e últimos preços)
- `grupo_aprovacao`, `grupo_aprovacao_nivel` (nível 1..N, valor limite de alçada), `grupo_aprovacao_aprovador` (usuário × nível, com aprovador substituto e vigência p/ férias), `pedido_aprovacao` (histórico: quem aprovou/rejeitou, quando, observação)
- `nfe_entrada` (chave, XML no storage, status de processamento)
- `produto_fornecedor` (cadastro **Produtos × Fornecedores**, no domínio Cadastros): produto interno × fornecedor, com código e descrição do produto no fornecedor, unidade do fornecedor + **fator de conversão** (fornecedor vende CX12, estoque controla UN), último preço e histórico, prazo de entrega. É o de-para que resolve a importação de XML (aprende no primeiro vínculo, igual à conciliação bancária) e ainda alimenta cotações de compra (comparar fornecedores por produto) e sugestão de reposição
- `orcamento`, `pedido_venda`, `pedido_venda_item`, `faturamento`
- `nota_fiscal` (chave, série, número, status SEFAZ, XML no storage, eventos)
- `oportunidade`, `funil_etapa`, `atividade_crm`
- `ordem_servico`, `contrato`
- `equipamento` (vinculado ao Patrimonial), `contrato_locacao`, `contrato_locacao_item` (equipamento, período, valor), `reserva_equipamento`, `devolucao` (checklist/vistoria), `manutencao_equipamento`
- `colaborador`, `cargo`, `ausencia`, `folha_pagamento`, `folha_item` (proventos/descontos/encargos), `evento_esocial`
- `centro_custo` (cadastro em Cadastros — Fase 1 — pois Compras, Vendas e lançamentos financeiros o referenciam antes da Contabilidade existir)
- `conta_contabil` (plano hierárquico), `lancamento_contabil` + `partida` (débito/crédito, sempre balanceadas), `regra_contabilizacao`, `exercicio_contabil`

Todas com `empresa_id`, UUID v7, soft delete e auditoria — sem exceção.

## Ordem de implementação recomendada

A ordem segue dependência de dados + valor imediato para PME comercial/serviços:

1. **Fase 0 — Consolidação da base**: commit/push do estado atual, CI (lint + testes), reorganização dos módulos por domínio, flag de domínios habilitados por empresa, campo `codigo` na empresa, **tela de entrada** (data base + empresa por código + módulo) e **tela de administração de acessos** (menu × usuário por módulo/empresa).
2. **Fase 1 — Cadastros**: produtos e serviços (já com campos tributários da reforma — CST-IBS/CBS, cClassTrib — além de NCM/CFOP/CSTs legados), **produtos × fornecedores**, unidades, tabela de preços e **centros de custo** (incluindo campo opcional `centro_custo_id` nos lançamentos financeiros, para o custo gerencial começar a rodar antes da Contabilidade). Pré-requisito de tudo.
3. **Fase 2 — Estoque**: depósitos, movimentações, inventário, custo médio.
4. **Fase 3 — Compras**: fluxo completo **solicitação → cotação → pedido**: a solicitação de compra (manual ou gerada por estoque mínimo) alimenta a cotação, que compara N fornecedores num mapa comparativo (preço, prazo, frete — pré-preenchido pelo cadastro produtos × fornecedores) e gera o pedido para o(s) vencedor(es); etapas intermediárias puláveis por configuração (compra direta = pedido sem SC/cotação, para empresas menores). **Parâmetro por empresa "nota exige pedido"**: quando ligado, nenhuma NF-e de entrada é processada (upload ou captura DF-e) sem vínculo com pedido de compra **aprovado** — a importação valida fornecedor, itens, quantidades e preços contra o pedido (tolerâncias configuráveis) e diverge para conferência quando não bate; quando desligado, permite entrada direta criando o pedido implícito. Pedido de compra (**centro de custo obrigatório por item**) → **aprovação por alçada** → recebimento → contas a pagar + entrada de estoque; o centro de custo flui do pedido para o lançamento financeiro e, na Fase 6, para a contabilização. **Workflow de aprovação (estilo Protheus)**: grupos de aprovação por empresa, cada grupo com níveis (1..N) e valor de alçada por nível; aprovadores associados a níveis, com substituto e vigência (férias/ausência). Pedido emitido entra como *aguardando aprovação* e percorre os níveis em sequência até o nível cuja alçada cobre o valor total; qualquer rejeição devolve ao comprador com motivo. Notificações (e-mail/sistema já existentes) avisam o aprovador da vez; painel "minhas aprovações pendentes" multi-empresa; tudo auditado. Pedido só segue para recebimento/fiscal depois de aprovado; alteração de valor após aprovação reinicia o fluxo. Inclui **importação de XML de NF-e** (upload): lê o XML do fornecedor, sugere/cadastra fornecedor e produtos via **de-para** (código do produto no fornecedor → produto interno), vincula a pedido existente ou cria entrada direta, e gera estoque + contas a pagar com impostos destacados. Parcelas do XML (duplicatas) viram o parcelamento do contas a pagar.
5. **Fase 4 — Vendas**: fluxo **orçamento → pedido de venda → faturamento**. Orçamento com validade, versões e envio ao cliente (PDF/link); aprovado, vira pedido com um clique. Pedido de venda: **reserva estoque**, passa por **análise de crédito** (limite por cliente + consulta ao módulo de inadimplência já existente — cliente devedor bloqueia ou exige liberação), e usa **Tipo de Operação de Saída (TES de saída)** que define CFOP, se movimenta estoque e a tributação. **Faturamento total ou parcial** (um pedido pode gerar N faturamentos/entregas): calcula impostos pelo motor fiscal (ICMS/ST/DIFAL, IPI, PIS/COFINS + IBS/CBS na transição), emite NF-e/NFS-e via adapter, gera **contas a receber** com o parcelamento da condição de pagamento, baixa o estoque e apura **comissões** por vendedor (liquidação junto com o recebimento — comissão paga sobre o recebido, configurável). **Devoluções**: NF-e de devolução referenciando a original, estorno proporcional de estoque, financeiro e comissão. Primeiro ciclo completo do ERP.
6. **Fase 5 — Fiscal**: emissão NF-e/NFS-e via **API de terceiros** (PlugNotas, Focus NFe ou similar) atrás de um adapter `EmissorFiscal`, mesma filosofia do `StorageProvider`. Emissor próprio SEFAZ fica como evolução futura opcional, sem mudança no domínio. Inclui **captura automática de XML na SEFAZ (Distribuição DF-e)** e **manifestação do destinatário** (ciência/confirmação) — as notas emitidas contra os CNPJs das empresas chegam sozinhas e caem na fila de importação de Compras, sem depender do fornecedor enviar o XML. Tudo via API de terceiros: o módulo de certificado digital já existente passa a servir para guardar o A1 e enviá-lo ao provedor da API.
7. **Fase 6 — Contabilidade**: plano de contas contábil e centros de custo; regras de contabilização automática a partir do financeiro/fiscal; lançamentos manuais; balancete, diário, razão, balanço e DRE contábil; encerramento de exercício. SPED Contábil (ECD)/ECF inicialmente via exportação para o contador, depois via API de terceiros.
8. **Fase 7 — Serviços**: OS e contratos (forte sinergia com recorrência já existente); **locação de equipamentos** — cadastro de equipamentos locáveis a partir do Patrimonial, contrato de locação com itens/período, agenda de disponibilidade e reservas, faturamento recorrente gerando contas a receber, devolução com vistoria e envio para manutenção. Nota fiscal: locação de bem móvel **não incide ISS** (Súmula Vinculante 31 do STF) — emite-se fatura/recibo de locação, não NFS-e; serviços acoplados (operador, montagem) esses sim saem como NFS-e.
9. **Fase 8 — RH**: colaboradores, cargos e ausências primeiro; depois cálculo de folha (proventos, descontos, encargos, provisões → lançamentos no financeiro); **eSocial via API de terceiros** atrás de adapter `EsocialProvider`. Fase de maior complexidade legal — planejar em sub-etapas.
10. **Fase 9 — CRM** (deixado por último por decisão de produto — Vendas opera sem ele até lá): funil e oportunidades alimentando Vendas.
11. **Fase 10 — Produção** (opcional): ficha técnica (BOM) e custo do acabado, ordens de produção com reserva/baixa de insumos e entrada do produto acabado no estoque, apontamento e perdas. Implementada quando alguma empresa do grupo (ou cliente) tiver operação industrial.

## Detalhamento do domínio Fiscal — Central Fiscal

O Fiscal não é só emissão: é uma **Central Fiscal multi-CNPJ**, o cockpit onde a operadora trata tudo de nota fiscal para todas as empresas do grupo numa tela só.

### NF-e — entrada (busca de XML por CNPJ)
- **Monitor DF-e**: consulta periódica à Distribuição DF-e para **cada CNPJ** cadastrado (via API de terceiros — sem conexão direta à SEFAZ nem middleware local), baixando resumos e XMLs completos das notas emitidas contra as empresas. Fila unificada multi-empresa.
- **Manifestação do destinatário** direto da fila: Ciência da Operação, Confirmação, Desconhecimento e Operação Não Realizada — com controle de prazo e alerta (manifestar é condição para baixar o XML completo e evita uso indevido do CNPJ).
- **Guarda de XML**: armazenamento no storage (MinIO/S3) pelo prazo legal (5+ anos), com busca por chave, fornecedor, período e empresa.
- Encaminhamento da nota manifestada para a fila de **importação de Compras** (de-para de produtos, estoque, contas a pagar).

### NF-e — saída (emissão e eventos)
- Emissão via adapter `EmissorFiscal` (API de terceiros), com **Carta de Correção (CC-e)**, **cancelamento**, **inutilização de numeração** e consulta de status/DANFE.
- Nota autorizada trava o documento de origem (pedido/faturamento).

### NFS-e — novo modelo nacional (avaliação jul/2026)
Contexto regulatório vigente:
- A **LC 214/2025** obrigou todos os municípios a aderirem ao **padrão nacional da NFS-e** desde 01/01/2026 (sob pena de perda de transferências voluntárias da União). O município autoriza emissão pelo **Emissor Nacional** (gratuito, web ou API) ou mantém emissor próprio enviando tudo ao **ADN — Ambiente de Dados Nacional**.
- A partir de **01/09/2026**, ME/EPP do Simples Nacional prestadoras de serviço deverão emitir **exclusivamente pelo Emissor Nacional** (web ou API).
- **Decisão de arquitetura**: o adapter `EmissorFiscal` para NFS-e prioriza o **padrão nacional (API do Emissor Nacional/ADN)** como caminho principal; padrões municipais legados (ABRASF etc.) só via API de terceiros quando inevitável. Isso simplifica radicalmente o multi-município.
- O ADN também **distribui** as NFS-e recebidas pelas empresas → mesma lógica do monitor DF-e, para serviços tomados.

### Impostos em Compras (entrada)

Princípio: **na entrada o sistema não calcula imposto — captura, valida e classifica**. Quem calcula é o fornecedor; os valores vêm destacados no XML. O trabalho do ERP é decidir o que cada imposto vira: **crédito a recuperar** ou **custo do produto**.

- **Tipo de Operação de Entrada (equivalente à TES do Protheus)**: cadastro parametrizável que define, por operação (revenda, uso/consumo, imobilizado, industrialização...): CFOP de entrada; se atualiza estoque; se gera financeiro; **quais impostos geram crédito** (ICMS, IPI, PIS/COFINS, IBS/CBS) conforme o **regime tributário da empresa** (Simples, Presumido, Real — cada empresa do grupo pode ter um); se o imposto não creditável compõe o custo. Sugerida automaticamente por produto/fornecedor/CFOP do XML, com aprendizado como no de-para.
- **Formação de custo**: custo de aquisição = mercadoria + frete + seguro + despesas + IPI e ICMS-ST quando não recuperáveis + impostos não creditáveis − créditos recuperáveis. É esse custo que entra no custo médio do estoque.
- **Validação**: o sistema confere os impostos do XML contra o esperado (NCM/CST/cClassTrib do cadastro de produtos + regime da empresa) e sinaliza divergências (ex.: fornecedor destacou ICMS-ST indevido) para conferência antes de efetivar.
- **Escrituração**: créditos apurados alimentam a apuração fiscal (Fase 5) e a contabilização automática (Fase 6, contas de impostos a recuperar × estoque × fornecedores).

### Impostos em Vendas (saída)

Na saída a responsabilidade inverte: **o sistema calcula**. Motor fiscal próprio parametrizado por: produto (NCM, CSTs, cClassTrib), TES de saída (CFOP, tributação da operação), regime da empresa emissora, UF de origem/destino (ICMS interestadual, ST, DIFAL) e cliente (contribuinte ou não). Calcula ICMS/ST/DIFAL, IPI, PIS/COFINS e, na transição da reforma, IBS/CBS/IS conforme NT 2025.002. A API emissora **valida** o cálculo na transmissão (rejeições da SEFAZ retornam para ajuste), mas a regra de negócio é nossa — não dependemos do provedor para saber o preço final com impostos na tela do pedido.

### Reforma Tributária (IBS/CBS/IS) — impacto imediato
- **NT 2025.002** alterou o layout da NF-e/NFC-e com os grupos de IBS/CBS/IS. Campos **CST-IBS/CBS** e **cClassTrib** por item: obrigatórios em produção a partir de **03/08/2026** para Regime Normal (homologação desde 01/07/2026); Simples/MEI a partir de **01/2027**.
- Consequência no roadmap: o cadastro de **produto (Fase 1) já nasce com os campos tributários da reforma** (CST-IBS/CBS, cClassTrib) além dos legados (NCM, CFOP, CST ICMS/PIS/COFINS), evitando retrabalho na Fase 5.
- A API emissora escolhida deve comprovar suporte à NT 2025.002 e ao Emissor Nacional NFS-e — critério de seleção do fornecedor.

## Decisões firmadas (jul/2026)

1. **Fiscal**: emissão via **API de terceiros** atrás de adapter `EmissorFiscal`; emissor próprio é evolução opcional. **Sem middleware fiscal local** (sem equivalente a TSS/Protheus): emissão, captura DF-e, manifestação e NFS-e passam todos pela API de terceiros na nuvem — nada de serviço fiscal para instalar/manter na VM. O certificado digital A1 (módulo já existente) é enviado ao provedor da API, que assina e transmite; o ERP só orquestra e guarda os XMLs no próprio storage.
2. **Segmento prioritário**: **comércio e serviços igualmente** — ordem de fases mantida (ciclo comercial completo primeiro, serviços na Fase 7).
3. **PDV/frente de caixa**: **fora do escopo** — vendas via pedido/faturamento atendem; PDV seria projeto à parte.
4. **RH**: **folha completa dentro do ERP** (proventos, descontos, encargos), com **eSocial via API de terceiros** atrás de adapter.
