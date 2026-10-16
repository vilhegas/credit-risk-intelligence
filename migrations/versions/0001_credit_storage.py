"""Cria armazenamento e concede somente leitura e inserção à aplicação."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA credit")
    op.create_table(
        "execution_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_version", sa.Text(), nullable=False),
        sa.Column("configuration", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("length(trim(dataset_version)) > 0", name="ck_run_version"),
        schema="credit",
    )
    op.create_table(
        "treated_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_key", sa.Text(), nullable=False),
        sa.Column("reference_date", sa.Date(), nullable=False),
        sa.Column("features", postgresql.JSONB(), nullable=False),
        sa.Column("defaulted", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["credit.execution_runs.id"]),
        sa.CheckConstraint("defaulted IN (0, 1)", name="ck_record_target"),
        sa.CheckConstraint("length(trim(subject_key)) > 0", name="ck_record_subject"),
        sa.UniqueConstraint("run_id", "subject_key", "reference_date", name="uq_record"),
        schema="credit",
    )
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("probability", sa.Numeric(12, 11), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["credit.execution_runs.id"]),
        sa.ForeignKeyConstraint(["record_id"], ["credit.treated_records.id"]),
        sa.CheckConstraint("probability BETWEEN 0 AND 1", name="ck_prediction_probability"),
        sa.CheckConstraint("length(trim(model_version)) > 0", name="ck_model_version"),
        sa.UniqueConstraint("run_id", "record_id", "model_version", name="uq_prediction"),
        schema="credit",
    )
    op.execute("GRANT USAGE ON SCHEMA credit TO credit_app")
    op.execute("GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA credit TO credit_app")


def downgrade() -> None:
    op.drop_table("predictions", schema="credit")
    op.drop_table("treated_records", schema="credit")
    op.drop_table("execution_runs", schema="credit")
    op.execute("DROP SCHEMA credit")
