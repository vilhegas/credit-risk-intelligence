"""Contrato SQLAlchemy das tabelas persistidas."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = sa.MetaData(schema="credit")

execution_runs = sa.Table(
    "execution_runs", metadata,
    sa.Column("id", UUID(as_uuid=True), primary_key=True),
    sa.Column("dataset_version", sa.Text, nullable=False),
    sa.Column("configuration", JSONB, nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False,
        server_default=sa.text("CURRENT_TIMESTAMP"),
    ),
    sa.CheckConstraint("length(trim(dataset_version)) > 0", name="ck_run_version"),
)

treated_records = sa.Table(
    "treated_records", metadata,
    sa.Column("id", UUID(as_uuid=True), primary_key=True),
    sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("credit.execution_runs.id"),
              nullable=False),
    sa.Column("subject_key", sa.Text, nullable=False),
    sa.Column("reference_date", sa.Date, nullable=False),
    sa.Column("features", JSONB, nullable=False),
    sa.Column("defaulted", sa.SmallInteger, nullable=False),
    sa.CheckConstraint("defaulted IN (0, 1)", name="ck_record_target"),
    sa.CheckConstraint("length(trim(subject_key)) > 0", name="ck_record_subject"),
    sa.UniqueConstraint("run_id", "subject_key", "reference_date", name="uq_record"),
)

predictions = sa.Table(
    "predictions", metadata,
    sa.Column("id", UUID(as_uuid=True), primary_key=True),
    sa.Column("run_id", UUID(as_uuid=True), sa.ForeignKey("credit.execution_runs.id"),
              nullable=False),
    sa.Column("record_id", UUID(as_uuid=True), sa.ForeignKey("credit.treated_records.id"),
              nullable=False),
    sa.Column("model_version", sa.Text, nullable=False),
    sa.Column("probability", sa.Numeric(12, 11), nullable=False),
    sa.CheckConstraint("probability BETWEEN 0 AND 1", name="ck_prediction_probability"),
    sa.CheckConstraint("length(trim(model_version)) > 0", name="ck_model_version"),
    sa.UniqueConstraint("run_id", "record_id", "model_version", name="uq_prediction"),
)
