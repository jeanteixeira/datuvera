from sqlalchemy.orm import defer
from app.models.quality_run import QualityRun
from app.quality.models import QualityResult


class QualityRunService:
    def __init__(self, db):
        self.db = db

    def persist(self, source_id: int, schema: str, table: str, result: QualityResult):
        snapshot = result.model_dump(mode='json')
        run = QualityRun(source_id=source_id, schema_name=schema, table_name=table,
                         overall_score=snapshot['score'],
                         completeness_score=snapshot['dimensions'].get('completeness'),
                         uniqueness_score=snapshot['dimensions'].get('uniqueness'),
                         validity_score=snapshot['dimensions'].get('validity'),
                         checks=snapshot['checks'])
        try:
            self.db.add(run)
            self.db.commit()
            self.db.refresh(run)
        except Exception:
            self.db.rollback()
            raise
        return run

    def list(self, source_id, schema, table, limit=20, offset=0):
        return (self.db.query(QualityRun).options(defer(QualityRun.checks)).filter_by(source_id=source_id, schema_name=schema, table_name=table)
                .order_by(QualityRun.created_at.desc(), QualityRun.id.desc()).limit(limit).offset(offset).all())

    def get(self, source_id, run_id):
        return self.db.query(QualityRun).filter_by(source_id=source_id, id=run_id).first()

    def latest(self, source_id, schema, table):
        rows = self.list(source_id, schema, table, limit=1)
        return rows[0] if rows else None
