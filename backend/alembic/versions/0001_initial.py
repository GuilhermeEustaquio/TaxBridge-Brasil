"""Schema inicial — 21 tabelas do TaxBridge Brasil.

Estratégia: a migração inicial materializa o metadata declarativo do SQLAlchemy
(fonte única da verdade em app/models). Migrações subsequentes devem ser geradas
com `alembic revision --autogenerate -m "..."` contra um banco em dia.

Revision ID: 0001
Revises:
Create Date: 2026-06-11
"""

from alembic import op

from app.models import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
