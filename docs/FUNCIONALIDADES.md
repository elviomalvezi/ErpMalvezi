# ERP Malvezi — Catálogo de Funcionalidades

> Plataforma web de controle financeiro multi-empresa, inspirada no Conta Azul.
> Documento de referência funcional · Atualizado em junho/2026.

---

## Visão geral

O **ERP Malvezi** centraliza a gestão financeira de **várias empresas** (Pessoa Jurídica e Pessoa Física) operadas por um mesmo grupo, com a rotina concentrada em uma operação central (secretária). O foco é **eficiência operacional**: importação automatizada, ações em lote entre empresas e visão consolidada — tudo em português (PT-BR).

- **Multi-empresa de um único dono** (não é SaaS multi-tenant tradicional).
- **Regime de caixa** (data de pagamento/recebimento define a competência).
- **Hospedagem em VM interna** (intranet), com acesso seguro via HTTPS.

---

## 1. Multi-empresa

- Cadastro de empresas **PJ (CNPJ)** ou **PF (CPF)**, com formulário adaptativo (máscaras e validações por tipo).
- **Seletor de empresa** no topo — todos os dados filtram automaticamente pela empresa ativa.
- **Cadastros compartilhados**: Categorias e Contatos podem ser **Globais** (todas as empresas) ou **Específicos** (uma empresa).
- **Operações entre empresas**: duplicar e transferir lançamentos entre entidades do grupo.
- **Isolamento de acesso**: cada usuário só enxerga as empresas que lhe foram liberadas.

## 2. Autenticação, permissões e segurança

- **Login** com e-mail e senha; **recuperação de senha** por e-mail.
- **Sessão de 2 horas** com **logout automático** e redirecionamento ao login quando expira.
- **Revogação de sessão imediata**: inativar um usuário ou trocar a senha derruba os acessos na hora.
- **Conexão segura (HTTPS)** com certificado válido.
- **Matriz de permissões `usuário × menu × ação`** (visualizar, criar, editar, excluir) — sem perfis fixos; novo usuário começa **sem nenhum acesso**.
- **Perfis**: Admin (acesso total), Gestor (gerencia usuários e permissões), Usuário (acesso conforme liberação).
- **Auditoria automática** de todas as alterações financeiras (quem, quando, valor anterior e novo).

## 3. Dashboard

- **KPIs do mês**: saldo em conta, receitas/despesas realizadas e previstas, saldo líquido.
- **Gráficos**: Receitas × Despesas (últimos 6 meses) e Top despesas por categoria.
- **Alertas de vencimento**: contas vencidas, "Vence Hoje", "Vencidos" e "Próximos 7 dias".

## 4. Fluxo de Caixa

- Visão mensal por dia de **receitas e despesas realizadas e previstas**.
- Navegação livre entre meses; filtros por empresa e conta bancária.
- Colunas de realizado, previsto e **saldo acumulado**.

## 5. Contas a Pagar e a Receber (núcleo de lançamentos)

- Modos de criação: **Simples**, **Parcelado** (N parcelas) e **Recorrente** (semanal/quinzenal/mensal/anual).
- **Baixa** (pagamento/recebimento) com conta bancária — aceita **baixa parcial** e **valor acima do previsto**.
- **Marcar como não realizado** — sinaliza um previsto que não ocorreu, sem excluir.
- **Duplicar**, **Tags livres**, **Anexos** (armazenados com segurança no banco), **Histórico** completo de alterações.
- **Filtros avançados**: texto, categoria, fornecedor/cliente, faixa de valor e de datas.
- **Ordenação** por qualquer coluna; **exportação** para Excel e PDF.

## 6. Extrato Bancário

- Movimentações de uma conta com **saldo progressivo** por dia, a partir do saldo inicial cadastrado.
- **Efetivação direto pelo extrato** (sem voltar à tela de lançamentos).

## 7. Inadimplência

- Contas a receber vencidas **agrupadas por cliente**.
- Indicadores: total em atraso, nº de inadimplentes, lançamentos vencidos, maior prazo de atraso.
- Exportação para Excel.

## 8. Transferências entre contas

- Movimentação entre contas **sem afetar o resultado** (não é receita nem despesa).
- **Intra e inter-empresa**, de forma **atômica** (debita e credita numa única operação).

## 9. Conciliação Bancária (OFX / CSV)

- Importa o extrato do banco em **OFX** ou **CSV**.
- **Sugestão automática** de correspondência entre transações e lançamentos.
- Ações por transação: **Conciliar**, **Criar lançamento** ou **Ignorar**.
- **Aprendizado de categorização**: memoriza padrões e sugere categoria/contato nas próximas importações.

## 10. Cartão de Crédito e Faturas

- Compras alimentam a **fatura aberta**; o **pagamento da fatura** é o que gera saída de caixa real.
- Fechamento por competência, com dia de fechamento e vencimento configuráveis.

## 11. Categorias / Plano de Contas

- Hierarquia de até **3 níveis**; escopo Global ou Específico.
- **Plano de contas padrão** pré-configurado.
- **Unir categorias (merge)** — migra lançamentos e inativa a origem.

## 12. Clientes e Fornecedores

- Cadastro unificado **PJ/PF**, escopo Global ou Específico.
- **Consulta de CNPJ (autopreenchimento)**: digita o CNPJ e o sistema preenche razão social, nome fantasia, e-mail, telefone e endereço a partir da Receita Federal.
- **Unir contatos (merge)** para eliminar duplicatas.

## 13. Contas Bancárias e Cartões

- Tipos: **Conta Corrente, Poupança, Caixinha, Aplicação e Cartão de Crédito**.
- **Saldo inicial** e data de referência como ponto de partida do cálculo de saldo.

## 14. Patrimonial

- Controle de **Imóveis** (matrícula, inscrição, valores, status) e **Veículos** (placa, RENAVAM, chassi, valores, status).
- **Anexos de documentos** e **vínculo com lançamentos** financeiros.

## 15. Importação em Lote

- Importa lançamentos em massa a partir de planilha **Excel/CSV**.
- **Mapeamento de colunas**, identificação de empresa/categoria/fornecedor e **preview** antes de confirmar.

## 16. DRE / Relatórios

- **Demonstrativo de Resultado** por empresa e período.

## 17. Configurações

- Dados da empresa, logo e identidade visual.
- **Trava de fechamento mensal** (protege lançamentos antigos contra edição).
- Moeda (BRL) e regime de caixa.

---

## Infraestrutura e confiabilidade

- **Arquitetura**: Angular (frontend) + Python/FastAPI (backend) + PostgreSQL (banco), em contêineres Docker.
- **HTTPS** com certificado válido e cabeçalhos de segurança (HSTS, proteção contra clickjancking, rate-limit).
- **Backup diário automático** do banco de dados (com rotação), cobrindo inclusive os anexos.
- **Auditoria** e **soft delete** (nada com histórico é apagado, apenas inativado).
- Pronto para evoluir para nuvem (AWS) sem mudança de código, se houver necessidade futura.

---

## Decisões de escopo

- **Conciliação por OFX/CSV** cobre a necessidade de integração bancária sem custo nem dependência externa.
- **Open Finance ficou fora do escopo** (exigiria participação regulada no Banco Central ou um agregador pago).
- **Regime de caixa** apenas (sem regime de competência) no momento.
