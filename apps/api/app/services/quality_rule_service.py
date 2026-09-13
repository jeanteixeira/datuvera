from sqlalchemy import inspect
from sqlalchemy.sql.sqltypes import String, Numeric, Integer, Float, Boolean
from app.models.quality_rule import DatasetQualityRule
from app.quality.parameters import validate_parameters
from app.quality.rules import QualityRule
from app.services.connectors.postgres_connector import PostgreSQLConnector


class RuleValidationError(ValueError):
    pass


def validate_column(column, rule_type, parameters):
    dtype = column['type']
    numeric = isinstance(dtype, (Numeric, Integer, Float))
    textual = isinstance(dtype, String)
    if rule_type == 'email_format' and not textual:
        raise RuleValidationError('email_format requires a textual column')
    if rule_type in ('min_value', 'max_value') and not numeric:
        raise RuleValidationError('Value bounds require a numeric column')
    if rule_type == 'allowed_values':
        values = parameters['values']
        if textual and not all(isinstance(v, str) for v in values):
            raise RuleValidationError('Textual columns require string values')
        if numeric and not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            raise RuleValidationError('Numeric columns require numeric values')
        if isinstance(dtype, Boolean) and not all(isinstance(v, bool) for v in values):
            raise RuleValidationError('Boolean columns require boolean values')
        if not (textual or numeric or isinstance(dtype, Boolean)):
            raise RuleValidationError('allowed_values supports text, numeric and boolean columns')


class QualityRuleService:
    def __init__(self, db):
        self.db = db

    def list(self, source_id, schema=None, table=None, enabled_only=False):
        query = self.db.query(DatasetQualityRule).filter_by(source_id=source_id)
        if schema is not None: query = query.filter_by(schema_name=schema)
        if table is not None: query = query.filter_by(table_name=table)
        if enabled_only: query = query.filter_by(is_enabled=True)
        return query.order_by(DatasetQualityRule.id).all()

    def effective(self, source_id, schema, table):
        return [QualityRule(column=r.column_name, type=r.rule_type,
                            params=r.parameters if r.rule_type == 'allowed_values' else {},
                            value=r.parameters.get('value'))
                for r in self.list(source_id, schema, table, enabled_only=True)]

    def get(self, source_id, rule_id):
        return self.db.query(DatasetQualityRule).filter_by(id=rule_id, source_id=source_id).first()

    def validate_dataset(self, source, schema, table, column, rule_type, parameters):
        engine = PostgreSQLConnector(source.host, source.port, source.database, source.username, source.password).engine
        try:
            inspector = inspect(engine)
            if not inspector.has_table(table, schema=schema):
                raise RuleValidationError('Schema or table not found')
            found = next((c for c in inspector.get_columns(table, schema=schema) if c['name'] == column), None)
            if found is None:
                raise RuleValidationError('Column not found')
            validate_column(found, rule_type, parameters)
        finally:
            engine.dispose()

    def create(self, source, payload):
        self.validate_dataset(source, payload.schema_name, payload.table_name, payload.column_name,
                              payload.rule_type, payload.parameters)
        rule = DatasetQualityRule(source_id=source.id, **payload.model_dump())
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def patch(self, source, rule, payload):
        changes = payload.model_dump(exclude_unset=True)
        parameters = changes.get('parameters', rule.parameters)
        try:
            validate_parameters(rule.rule_type, parameters)
        except ValueError as error:
            raise RuleValidationError(str(error)) from None
        if 'parameters' in changes or changes.get('is_enabled') is True:
            self.validate_dataset(source, rule.schema_name, rule.table_name, rule.column_name, rule.rule_type, parameters)
        for name, value in changes.items(): setattr(rule, name, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, rule):
        self.db.delete(rule)
        self.db.commit()
