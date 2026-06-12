# Segurança e LGPD

## Autenticação e sessão
- **JWT** assinado HS256 (`SECRET_KEY` por ambiente): access 30 min + refresh 7 dias (rotação a cada refresh).
- Senhas com **bcrypt** (cost 12), nunca registradas em logs/auditoria.
- Rate limit nos endpoints de auth (10 req/min/IP) contra força bruta.
- 2FA TOTP opcional na fase 2 (campo `users.totp_enabled` já previsto).

## Autorização e tenancy
- RBAC com 7 perfis (níveis hierárquicos) aplicado via dependency `require_roles`.
- **Isolamento multi-tenant:** `organization_id` extraído do token (nunca do payload do cliente)
  e aplicado em todas as queries; FKs cruzadas validadas dentro do tenant (ex.: simulação só
  enxerga empresa da própria organização).
- API keys com hash SHA-256 (segredo exibido uma única vez), prefixo identificável `tbk_`,
  revogação e rate limit por chave.

## Auditoria
- Toda ação de escrita + login/logout grava `audit_logs`: usuário, organização, ação,
  entidade, metadados resumidos (sem dados sensíveis), **IP, user-agent e timestamp**.
- Logs imutáveis pela API (somente leitura para admin/dono/contador).

## Proteção de dados (LGPD)
| Princípio | Implementação |
|---|---|
| Base legal / consentimento | Aceite explícito no registro (`lgpd_consent_version`, `lgpd_consent_at`) |
| Minimização | Coletamos apenas dados cadastrais e fiscais necessários ao serviço |
| Transparência | Premissas e memória de cálculo visíveis; política de privacidade versionada |
| Retenção | Soft delete (`deleted_at`) + rotina de expurgo configurável (`DATA_RETENTION_DAYS`) |
| Portabilidade | Exportação CSV/XLSX de catálogo e simulações |
| Eliminação | Exclusão de organização ⇒ anonimização de usuários + expurgo programado |
| Segurança | TLS no proxy (produção), segredos via env, criptografia em repouso no Postgres gerenciado |
| Encarregado (DPO) | Canal dpo@taxbridge.com.br (placeholder) |

Dados pessoais tratados no MVP: nome, e-mail, hash de senha, IP (auditoria). Dados fiscais de
empresas (CNPJ, notas) são dados **corporativos**, tratados sob contrato (operador).

## Criptografia de dados sensíveis
- Em trânsito: TLS (terminação no proxy/ingress em produção).
- Em repouso: senha (bcrypt) e API keys (SHA-256) sempre com hash; demais campos sensíveis
  prontos para `pgcrypto`/KMS na fase 2 (coluna a coluna, conforme classificação).

## Backups e recuperação
- Volume Postgres persistente no Compose; em produção: backup diário automatizado + PITR
  (WAL) no provedor gerenciado; teste de restore trimestral documentado.

## Checklist OWASP aplicado no MVP
- [x] Validação forte de entrada (Pydantic v2, tipos e limites em todos os campos)
- [x] SQL apenas via ORM parametrizado (sem string SQL)
- [x] CORS restrito à origem do frontend (`CORS_ORIGINS`)
- [x] Erros sem stack trace para o cliente; mensagens neutras em auth (sem user enumeration)
- [x] Segredos fora do código (.env / variáveis de ambiente)
- [x] Soft delete impede vazamento por IDs reutilizados; UUIDs não sequenciais
