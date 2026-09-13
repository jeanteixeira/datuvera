from typing import List, Dict, Any, Optional
from sqlalchemy import text
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


EMAIL_REGEX = r'^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'


class QualityRule(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    column: str
    rule_type: Literal['email_format', 'allowed_values', 'min_value', 'max_value'] = Field(alias='type')
    params: Dict[str, Any] = Field(default_factory=dict)
    value: Optional[float] = None


def demo_rules_for_table(schema: str, table: str) -> List[QualityRule]:
    # For demo dataset public.customers
    if schema == 'public' and table == 'customers':
        return [
            QualityRule(column='email', type='email_format'),
            QualityRule(column='state', type='allowed_values', params={'values': ['AL', 'PE', 'BA', 'SP', 'RJ']}),
        ]
    return []


def evaluate_email_format(conn, schema: str, table: str, column: str) -> Dict[str, Any]:
    preparer = conn.dialect.identifier_preparer
    column = preparer.quote_identifier(column)
    schema = preparer.quote_identifier(schema)
    table = preparer.quote_identifier(table)
    sql = text(f"SELECT COUNT(*) AS total, SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) AS nulls, SUM(CASE WHEN {column} IS NOT NULL AND {column} !~ :regex THEN 1 ELSE 0 END) AS invalid FROM {schema}.{table}")
    res = conn.execute(sql, {'regex': EMAIL_REGEX}).mappings().first()
    total = res['total'] or 0
    nulls = res['nulls'] or 0
    invalid = res['invalid'] or 0
    return {'total': total, 'nulls': nulls, 'invalid': invalid}


def evaluate_allowed_values(conn, schema: str, table: str, column: str, values: List[str]) -> Dict[str, Any]:
    preparer = conn.dialect.identifier_preparer
    column = preparer.quote_identifier(column)
    schema = preparer.quote_identifier(schema)
    table = preparer.quote_identifier(table)
    if not values:
        sql = text(f"SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE {column} IS NULL) AS nulls, COUNT({column}) AS outside FROM {schema}.{table}")
        return dict(conn.execute(sql).mappings().one())
    placeholders = ','.join([f':v{i}' for i in range(len(values))])
    params = {f'v{i}': v for i, v in enumerate(values)}
    sql = text(f"SELECT COUNT(*) AS total, SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) AS nulls, SUM(CASE WHEN {column} IS NOT NULL AND {column} NOT IN ({placeholders}) THEN 1 ELSE 0 END) AS outside FROM {schema}.{table}")
    res = conn.execute(sql, params).mappings().first()
    total = res['total'] or 0
    nulls = res['nulls'] or 0
    outside = res['outside'] or 0
    return {'total': total, 'nulls': nulls, 'outside': outside}


def evaluate_value_bound(conn, schema: str, table: str, column: str, value: float, rule_type: str) -> Dict[str, Any]:
    operators = {'min_value': '<', 'max_value': '>'}
    operator = operators[rule_type]
    quote = conn.dialect.identifier_preparer.quote_identifier
    sql = text(f"SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE {quote(column)} {operator} :value) AS invalid FROM {quote(schema)}.{quote(table)}")
    return dict(conn.execute(sql, {'value': value}).mappings().one())


def evaluate_unique(conn, schema: str, table: str, columns: List[str], nulls_not_distinct: bool = False) -> Dict[str, Any]:
    # All rows in a duplicate group fail. Ordinary UNIQUE ignores tuples with any NULL.
    quote = conn.dialect.identifier_preparer.quote_identifier
    relation = f"{quote(schema)}.{quote(table)}"
    identifiers = ', '.join(quote(column) for column in columns)
    where = '' if nulls_not_distinct else ' WHERE ' + ' AND '.join(f'{quote(column)} IS NOT NULL' for column in columns)
    sql = text(f"SELECT (SELECT COUNT(*) FROM {relation}) AS total, COALESCE(SUM(n), 0) AS invalid FROM (SELECT COUNT(*) AS n FROM {relation}{where} GROUP BY {identifiers} HAVING COUNT(*) > 1) AS duplicates")
    result = conn.execute(sql).mappings().one()
    return {key: int(value) for key, value in result.items()}
