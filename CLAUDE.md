1# App Financeiro

Plataforma web de controle financeiro inspirada no Conta Azul. Documento principal de referência: `App_Financeiro_Especificacao_MVP.docx` na raiz deste diretório.

## Estado atual

- Especificação funcional do MVP **concluída** (14 módulos detalhados em `App_Financeiro_Especificacao_MVP.docx`).
- Stack tecnológico **definido** (Angular + Python/FastAPI + PostgreSQL).
- Estratégia de hospedagem: desenvolvimento **local** e produção em **VM interna** (intranet) com Docker Compose. **AWS opcional como evolução futura**, não destino obrigatório.
- Modelagem de dados consolidada, wireframes, scaffolding, arquitetura técnica e roadmap **a fazer**.

## Contexto operacional (não óbvio do código)

A plataforma atende um cenário muito específico que dirige todas as decisões de produto:

- **Multi-empresa de um único dono**: várias empresas (CNPJs e também Pessoas Físicas) operadas por uma mesma pessoa. Não é SaaS multi-tenant tradicional; é multi-empresa de uma única conta de usuário.
- **Operação centralizada numa secretária**: uma única pessoa cuida da rotina financeira de várias entidades. Eficiência operacional (importação automatizada, ações em lote entre empresas) pesa muito mais que sofisticação contábil.
- **Idioma**: interface, mensagens de validação e documentação em **português (PT-BR)**. Código (variáveis, comentários técnicos) pode ser em inglês.

## Decisões de produto firmadas

- **Empresa pode ser PJ (CNPJ) ou PF (CPF)**, com formulário adaptativo (máscaras, validações e campos diferentes conforme tipo).
- **Cadastros compartilhados**: Categorias, Clientes e Fornecedores podem ter escopo `global` (todas as empresas do usuário) ou `especifico` (uma única empresa). Default sugerido: global.
- **Visualização multi-empresa simultânea** é uma preferência do usuário (default desligada). Quando ligada, o usuário escolhe a empresa no momento da inclusão de cada lançamento.
- **Operações entre empresas em lançamentos**: duplicar (clonar na mesma ou em outra) e transferir (mover entre empresas).
- **Conciliação bancária via OFX/CSV é requisito do MVP** (não fase posterior). **Open Finance está fora do escopo do projeto** (decisão firmada): exigiria participação regulada no Banco Central ou a contratação de um agregador pago (Pluggy/Belvo/etc.); a conciliação por OFX/CSV cobre a necessidade sem custo nem dependência externa.
- **Modelo de permissões**: matriz `usuário × menu × ação`, sem perfis fixos. Novo usuário inicia **sem nenhum acesso**; admin libera explicitamente. Templates são evolução opcional.
- **Apenas regime de caixa** no MVP. Regime de competência fica fora.
- **Cartão de crédito** tem tratamento especial: compras alimentam fatura aberta, fatura fecha automaticamente, pagamento da fatura é o que gera saída de caixa real.
- **Trava de fechamento mensal**: lançamentos com competência ≤ data de fechamento ficam congelados (só edita quem tem permissão "Editar lançamentos após fechamento").
- **Soft delete**: nunca excluir registros com histórico; apenas inativar.
- **Auditoria** em todas as alterações financeiras (quem, quando, valor anterior, valor novo).

## Estrutura modular do MVP (14 módulos)

1. Multi-empresa (PJ/PF, escopos compartilhados, modo simultâneo, duplicar/transferir lançamentos)
2. Cadastro e autenticação de usuários (login, recuperação de senha; sem auto-cadastro; sem 2FA no MVP)
3. Configurações gerais da empresa (dados, logo, identidade visual)
4. Configurações financeiras (moeda, fechamento mensal, numeração)
5. Categorias / plano de contas (hierárquico em 3 níveis, plano padrão pronto)
6. Cadastro de clientes e fornecedores (PJ/PF, tabela `contato` unificada)
7. Contas bancárias e cartões (corrente, poupança, caixinha, aplicação, cartão)
8. Tratamento especial de cartão de crédito (fatura, parcelamento, pagamento)
9. Contas a pagar e a receber — núcleo de lançamentos (parcelamento, recorrência, baixa parcial, anexos)
10. Transferências entre contas (atômicas, intra e inter-empresa)
11. Conciliação bancária OFX/CSV (com aprendizado de categorização)
12. Fluxo de caixa (regime de caixa: realizado, previsto, projetado)
13. Dashboard inicial
14. Gestão de permissões (matriz usuário × menu × ação)

## Stack tecnológico

### Frontend

- **Angular 17+** com standalone components e Signals
- **TypeScript** estrito (`strict: true`)
- **PrimeNG** (preferido) ou Angular Material como biblioteca de componentes — escolha em aberto, decidir no scaffolding
- **NgRx Signals** para estado global
- **RxJS** onde fluxos assíncronos justificam (HTTP, WebSocket futuro)
- Testes: **Jest** + **Cypress** (e2e)

### Backend

- **Python 3.12+**
- **FastAPI** (framework web)
- **SQLAlchemy 2.x** + **Alembic** (ORM e migrations)
- **Pydantic v2** (validação e serialização — DTOs e configuração)
- **PyJWT** + **passlib (bcrypt)** (autenticação e hash de senha)
- **pytest** + **httpx** (testes unitários e de integração)
- **Ruff** (lint e formatter) + **mypy** (typing estático)
- **uvicorn** como servidor ASGI

### Banco de dados

- **PostgreSQL 16+** — local via Docker, na nuvem via AWS RDS.
- Justificativa do Postgres: constraints fortes, transações atômicas (transferências, baixas, conciliação), e Row-Level Security (RLS) viável para isolamento multi-empresa.

### Hospedagem

**Desenvolvimento local (cada dev):**
Docker Compose com Postgres, MinIO (S3-compatible), Mailhog (SMTP local). Backend `uvicorn --reload`, frontend `ng serve`.

**Produção em VM interna (intranet):**
- Sistema operacional: Ubuntu Server LTS (ou Debian).
- Docker + Docker Compose orquestrando: Postgres, FastAPI (uvicorn por trás de gunicorn ou uvicorn workers), Angular servido como estático pelo Nginx, MinIO para anexos e logos, Postfix relay (ou SMTP existente da empresa) para e-mails.
- Nginx como **reverse proxy único** terminando HTTPS (certificado da CA interna ou Let's Encrypt se houver domínio público) e roteando para frontend e backend.
- Acesso restrito à rede interna; remoto via VPN/Tailscale quando necessário.
- Backup diário do Postgres via `pg_dump` cron, com cópia cifrada para storage cloud barato (Backblaze B2, Wasabi ou S3 IA — apenas como cofre off-site, sem aplicação rodando lá).
- UPS (nobreak) obrigatório para evitar corrupção de banco em queda de energia.

**AWS como evolução futura (opcional):**
Mesmo stack pode ir para AWS sem mudança de código quando/se houver justificativa: RDS (Postgres), S3 (anexos), SES (e-mail), ECS Fargate ou EC2 (backend), S3+CloudFront (frontend), Secrets Manager (credenciais), GitHub Actions (CI/CD). Gatilhos típicos: aumento de usuários, requisito de SLA, expansão geográfica, exigência de auditoria externa.

### Princípio de portabilidade

Para que a aplicação rode igual em dev local, VM interna e (eventualmente) AWS, **projetar com adapters desde o início**:

- **Storage**: interface `StorageProvider` com implementações `LocalFileStorage` (dev) e `S3Storage` (MinIO ou AWS S3). Código de domínio nunca toca em filesystem ou boto3 diretamente.
- **E-mail**: interface `EmailSender` com implementação SMTP (cobre Mailhog em dev, Postfix interno e SES — todos via SMTP).
- **Configurações**: `pydantic-settings` lendo `.env` em qualquer ambiente. Em prod interna, `.env` fica fora do repo, num diretório protegido na VM.
- **Banco**: connection string vem do ambiente, idêntica em qualquer host (apenas host/credenciais mudam).
- **Logs**: `structlog` enviando para stdout (lido por `docker logs` em dev e prod interna; CloudWatch via Fluent Bit se um dia for AWS).

## Estrutura sugerida do repositório

Monorepo simples com frontend e backend separados:

```
App Financeiro/
├── CLAUDE.md
├── App_Financeiro_Especificacao_MVP.docx
├── docker-compose.yml          # Postgres, MinIO, Mailhog
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/                # migrations
│   ├── app/
│   │   ├── core/               # config, security, db
│   │   ├── domain/             # entidades e regras de negócio puras
│   │   ├── infrastructure/     # adapters (storage, email, repos)
│   │   ├── api/                # routers FastAPI
│   │   ├── modules/            # um por módulo do MVP
│   │   └── main.py
│   └── tests/
└── frontend/
    ├── angular.json
    ├── package.json
    └── src/
        ├── app/
        │   ├── core/           # interceptors, guards, services base
        │   ├── shared/         # componentes reutilizáveis
        │   └── features/       # um por módulo do MVP
        └── environments/
```

## Convenções

### Banco de dados

- Tabelas: `snake_case`, no singular (`empresa`, `lancamento`, `categoria`).
- Datas: `data_*` (ex: `data_vencimento`, `data_pagamento`); timestamps: `criado_em`, `atualizado_em`.
- Soft delete: campo `ativa` (boolean) + nunca apagar registros com histórico.
- IDs: **UUID v7** (ordenável temporalmente, melhor para índices que UUID v4) — decisão firmada.
- Moeda: **`decimal(15,2)`** (escala fixa, evita ambiguidade de centavos vs reais nos cálculos). Operações financeiras usam `Decimal` em Python (nunca `float`).
- Auditoria: tabela `auditoria` central com `tabela`, `registro_id`, `acao` (insert/update/delete), `usuario_id`, `valor_anterior` (jsonb), `valor_novo` (jsonb), `criado_em`.

### Backend (Python)

- Imports em ordem: stdlib → terceiros → projeto, separados por linha em branco.
- Type hints obrigatórios em assinaturas de função (mypy strict).
- Funções de domínio puras (sem efeito colateral) sempre que possível; efeitos isolados em adapters.
- Erros de regra de negócio: classes próprias de exceção (`DomainError`, `PermissionDeniedError`, `LancamentoCongeladoError`) — convertidas em HTTP no router.
- Cada módulo do MVP fica em `app/modules/<modulo>/` com `routes.py`, `service.py`, `repository.py`, `schemas.py`, `models.py`.

### Frontend (Angular)

- Standalone components sempre; nada de NgModules.
- Signals para estado local; NgRx Signals para estado compartilhado.
- Services com `providedIn: 'root'` por padrão.
- Mensagens de UI e validação em **português (PT-BR)**; código (variáveis, métodos, tipos) em **inglês**.
- Testes de componente: `@testing-library/angular` + Jest. E2E: Cypress.

### Git

- Branches: `main` (estável), `develop` (integração), `feature/<modulo>-<descricao>`.
- Commits em formato Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`).

## Como trabalhar neste projeto

Quando for implementar uma funcionalidade, sempre:

1. Localize o módulo correspondente na especificação `App_Financeiro_Especificacao_MVP.docx`.
2. Respeite as decisões de produto firmadas acima — elas não são detalhes de implementação, são **requisitos de produto**.
3. Em qualquer tabela financeira, lembre-se de incluir `empresa_id` obrigatório.
4. Em qualquer alteração de dados financeiros, gere registro de auditoria.
5. Em qualquer exclusão, prefira inativação (soft delete).
6. Valide permissões em três camadas: frontend (oculta), backend (rejeita), banco (RLS quando aplicável).

## Próximos passos sugeridos (em ordem)

1. ~~Definir stack tecnológico~~ — feito (Angular + FastAPI + Postgres, deploy em VM interna).
2. **Setup do ambiente local de desenvolvimento**: `docker-compose.yml` com Postgres, MinIO, Mailhog; `.env.example` com variáveis necessárias.
3. **Scaffolding do backend**: `pyproject.toml`, FastAPI mínimo rodando, Alembic configurado, primeira migration vazia, healthcheck, lint (ruff) e testes (pytest) passando vazios.
4. **Scaffolding do frontend**: `ng new`, biblioteca de componentes escolhida (PrimeNG ou Angular Material), layout base com header e seletor de empresa (mockado), roteamento, interceptor HTTP, ambiente de dev apontando para o backend local.
5. **Modelagem de dados consolidada**: arquivo `docs/modelo_dados.md` com diagrama ER (Mermaid) unificando os 14 módulos.
6. **Implementar módulos na ordem de dependência**: 1 → 2 → 14 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 3.
7. **Estratégia de testes**: unitários por regra de negócio, integração para fluxos críticos (parcelamento, baixa, conciliação, cartão).
8. **Provisionamento da VM de produção** (após módulos 1, 2, 14, 4, 5 funcionais): criar VM (Ubuntu Server LTS), instalar Docker e Docker Compose, configurar Nginx reverse proxy com HTTPS, definir estratégia de backup (cron + pg_dump + cópia off-site), nobreak, ajustar regras de firewall para acesso intranet.
9. **Pipeline de deploy**: GitHub Actions (ou GitLab CI) buildando imagens Docker, publicando em registry interno (Harbor) ou público com tag privada, e fazendo deploy na VM via SSH/`docker compose pull`. Sem necessidade de Kubernetes ou infra complexa.
10. **(Opcional, futuro)** Migração para AWS: gatilhos seriam crescimento de usuários, requisito de SLA, expansão geográfica. Stack já é portável; só muda o destino do deploy.
