# Banco de dados
DATABASE_URL=postgresql+psycopg2://taxbridge:taxbridge@localhost:5432/taxbridge

# Redis (filas/cache — worker fase 2)
REDIS_URL=redis://localhost:6379/0

# Segurança — TROQUE EM PRODUÇÃO (ex.: openssl rand -hex 32)
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (origens separadas por vírgula)
CORS_ORIGINS=http://localhost:3000

# Ambiente
ENV=development
AUTO_CREATE_TABLES=true
STORAGE_DIR=./storage
AUTH_RATE_LIMIT_PER_MINUTE=10
DATA_RETENTION_DAYS=1825

# IA assistente (opcional — sem chave, /ai/chat responde em modo offline)
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-opus-4-8
