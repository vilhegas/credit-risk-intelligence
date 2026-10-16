"""Ingestão transacional do ZIP local da fonte UCI 350."""

import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime
from io import BytesIO
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from zipfile import BadZipFile, ZipFile

import numpy as np
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

from credit_risk.persistence.schema import execution_runs, treated_records

SOURCE = "https://doi.org/10.24432/C55S3H"
CONTRACT = "uci-350-v1"
MEMBER = "default of credit card clients.xls"
TARGET = "default payment next month"
PAY = ("PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6")
FEATURES = (
    "LIMIT_BAL",
    *PAY,
    *(f"BILL_AMT{i}" for i in range(1, 7)),
    *(f"PAY_AMT{i}" for i in range(1, 7)),
)
COLUMNS = (
    "ID", "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE", *PAY,
    *(f"BILL_AMT{i}" for i in range(1, 7)),
    *(f"PAY_AMT{i}" for i in range(1, 7)), TARGET,
)
MAX_BYTES = 32 * 1024 * 1024
MAX_ROWS = 100_000


class IngestionError(ValueError):
    """Arquivo ou proveniência incompatível com o contrato."""


@dataclass(frozen=True)
class Provenance:
    """Confirmações documentais fornecidas por quem obteve o arquivo."""

    version: str
    obtained_at: datetime
    license_confirmed: bool
    temporal_order_confirmed: bool
    evidence: str

    def validate(self) -> None:
        if not self.version.strip() or not self.evidence.strip():
            raise IngestionError("Informe versão e evidência documental da fonte.")
        if self.obtained_at.utcoffset() is None:
            raise IngestionError("A data de obtenção deve conter fuso horário.")
        if self.obtained_at > datetime.now(UTC):
            raise IngestionError("A data de obtenção não pode estar no futuro.")
        if not self.license_confirmed or not self.temporal_order_confirmed:
            raise IngestionError("Confirme licença e sequência temporal antes da ingestão.")


@dataclass(frozen=True)
class ImportResult:
    run_id: UUID
    row_count: int
    reused: bool


def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Valida sem imputar, excluir linhas ou inferir categorias."""
    if tuple(frame.columns) != COLUMNS:
        raise IngestionError("Cabeçalho ou ordem das 25 colunas incompatível.")
    if not 0 < len(frame) <= MAX_ROWS:
        raise IngestionError("Quantidade de registros fora dos limites.")
    try:
        numeric = frame.apply(pd.to_numeric, errors="raise")
        values = numeric.to_numpy(dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise IngestionError("Todos os campos devem ser numéricos.") from exc
    if not np.isfinite(values).all():
        raise IngestionError("Valores ausentes ou não finitos não são aceitos.")
    if not np.equal(values, np.trunc(values)).all():
        raise IngestionError("O contrato desta fonte exige valores inteiros.")
    if (np.abs(values) > 2**53 - 1).any():
        raise IngestionError("Valor fora do intervalo inteiro seguro.")
    numeric = numeric.astype("int64")
    if (numeric["ID"] <= 0).any() or numeric["ID"].duplicated().any():
        raise IngestionError("ID deve ser positivo e único.")
    if not numeric[TARGET].isin([0, 1]).all():
        raise IngestionError("Alvo deve conter somente 0 ou 1.")
    return numeric


def read_archive(path: Path) -> tuple[pd.DataFrame, dict]:
    """Lê bytes limitados, sem extrair membros no sistema de arquivos."""
    with path.open("rb") as stream:
        archive_bytes = stream.read(MAX_BYTES + 1)
    if len(archive_bytes) > MAX_BYTES:
        raise IngestionError("ZIP excede o limite de tamanho.")
    try:
        with ZipFile(BytesIO(archive_bytes)) as archive:
            members = archive.infolist()
            if len(members) != 1 or members[0].filename != MEMBER:
                raise IngestionError("ZIP deve conter exclusivamente o XLS esperado.")
            member = members[0]
            if member.flag_bits & 1 or not 0 < member.file_size <= MAX_BYTES:
                raise IngestionError("XLS criptografado, vazio ou acima do limite.")
            with archive.open(member) as stream:
                xls_bytes = stream.read(MAX_BYTES + 1)
            if len(xls_bytes) > MAX_BYTES:
                raise IngestionError("XLS excede o limite descompactado.")
    except (BadZipFile, RuntimeError, NotImplementedError, EOFError) as exc:
        raise IngestionError("Arquivo ZIP inválido ou não suportado.") from exc
    try:
        frame = pd.read_excel(
            BytesIO(xls_bytes), engine="xlrd", header=1, nrows=MAX_ROWS + 1,
        )
    except ImportError:
        raise
    except Exception as exc:
        raise IngestionError("Não foi possível interpretar o XLS esperado.") from exc
    frame = validate_frame(frame)
    quality = {
        "rows": len(frame),
        "missing_values": 0,
        "duplicate_ids": 0,
        "excluded_rows": 0,
        "unexpected_row_count": len(frame) != 30_000,
        "undocumented_codes": {
            name: int((~frame[name].isin(allowed)).sum())
            for name, allowed in [
                *((name, [-1, *range(1, 10)]) for name in PAY),
                ("EDUCATION", [1, 2, 3, 4]),
                ("MARRIAGE", [1, 2, 3]),
            ]
        },
    }
    return frame, {
        "archive_filename": path.name,
        "archive_bytes": len(archive_bytes),
        "archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "member_filename": MEMBER,
        "member_bytes": len(xls_bytes),
        "member_sha256": hashlib.sha256(xls_bytes).hexdigest(),
        "quality": quality,
    }


def ingest_uci(path: str | Path, engine: Engine, provenance: Provenance) -> ImportResult:
    """Persiste uma única execução por fonte, contrato e conteúdo do XLS."""
    provenance.validate()
    frame, metadata = read_archive(Path(path))
    run_id = uuid5(NAMESPACE_URL, f"{SOURCE}:{CONTRACT}:{metadata['member_sha256']}")
    configuration = {
        **metadata,
        "source": SOURCE,
        "source_version": provenance.version,
        "contract_version": CONTRACT,
        "obtained_at": provenance.obtained_at.astimezone(UTC).isoformat(),
        "license": "CC BY 4.0",
        "license_confirmed": True,
        "temporal_order_confirmed": True,
        "evidence": provenance.evidence,
        "citation": "Yeh e Lien (2009), doi:10.1016/j.eswa.2007.12.020",
        "reference_date_convention": "2005-09-30; referência comum, não observada por cliente",
        "reader_versions": {"pandas": pd.__version__, "numpy": np.__version__},
    }
    with engine.begin() as connection:
        inserted = connection.execute(
            insert(execution_runs).values(
                id=run_id,
                dataset_version=f"{CONTRACT}:{metadata['member_sha256']}",
                configuration=configuration,
            ).on_conflict_do_nothing(index_elements=[execution_runs.c.id]).returning(
                execution_runs.c.id
            )
        ).scalar_one_or_none()
        if inserted is None:
            stored = connection.execute(
                sa.select(execution_runs.c.configuration).where(execution_runs.c.id == run_id)
            ).scalar_one()
            return ImportResult(run_id, stored["quality"]["rows"], True)
        batch = []
        for row in frame.to_dict(orient="records"):
            batch.append({
                "id": uuid4(),
                "run_id": run_id,
                "subject_key": f"uci-350:{int(row['ID'])}",
                "reference_date": date(2005, 9, 30),
                "features": {name: int(row[name]) for name in FEATURES},
                "defaulted": int(row[TARGET]),
            })
            if len(batch) == 1000:
                connection.execute(treated_records.insert(), batch)
                batch.clear()
        if batch:
            connection.execute(treated_records.insert(), batch)
    return ImportResult(run_id, len(frame), False)
