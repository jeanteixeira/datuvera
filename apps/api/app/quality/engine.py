from typing import List, Optional, Union
import json
from app.quality.models import CheckResult, QualityResult
from app.quality import rules
from app.profiling.engine import profile_table_from_source
from app.quality.scoring import check_score, severity_from_percentage, compute_dimension_score, weighted_score


DEFAULT_WEIGHTS = {'completeness': 1.0, 'uniqueness': 1.0, 'validity': 1.0}


def _check(rule: str, failed_count: int, failed_percentage: float, column: Optional[str] = None,
           columns: Optional[List[str]] = None, message: Optional[str] = None) -> CheckResult:
    status = severity_from_percentage(failed_percentage)
    return CheckResult(column=column, columns=columns, rule=rule, status=status,
                       passed=status == 'passed', failed_count=failed_count,
                       failed_percentage=failed_percentage, score=check_score(failed_percentage), message=message)


def run_quality(source, schema: str, table: str, connector,
                quality_rules: Optional[List[Union[rules.QualityRule, dict]]] = None) -> QualityResult:
    profile = profile_table_from_source(source, schema, table)
    columns = profile['columns']
    column_names = {column.name for column in columns}
    completeness_checks = [
        _check('not_null', col.null_count, col.null_percentage, column=col.name)
        for col in columns
    ]
    uniqueness_checks = []
    validity_checks = []
    pk = connector.get_primary_key_columns(schema, table)
    constraints = ([{'column_names': pk}] if pk else []) + connector.get_unique_constraints(schema, table)
    configured_rules = quality_rules or []
    seen = {('not_null', (c.name,)) for c in columns}

    with connector.engine.connect() as conn:
        for constraint in constraints:
            names = constraint.get('column_names', [])
            if not names or not set(names).issubset(column_names):
                continue
            nulls_not_distinct = constraint.get('dialect_options', {}).get('postgresql_nulls_not_distinct', False)
            key = ('unique', tuple(sorted(names)))
            if key in seen:
                continue
            seen.add(key)
            result = rules.evaluate_unique(conn, schema, table, names, nulls_not_distinct)
            invalid, total = result['invalid'], result['total']
            percentage = invalid / total * 100 if total else 0.0
            uniqueness_checks.append(_check('unique', invalid, percentage,
                                            column=names[0] if len(names) == 1 else None,
                                            columns=names if len(names) > 1 else None,
                                            message=f'{invalid} rows belong to duplicate key combinations.' if invalid else None))

        for configured_rule in configured_rules:
            rule = rules.QualityRule.model_validate(configured_rule)
            if rule.column not in column_names:
                continue
            if rule.rule_type in ('not_null', 'unique'):
                key = (rule.rule_type, (rule.column,))
                if key in seen:
                    continue
                seen.add(key)
                col = next(c for c in columns if c.name == rule.column)
                if rule.rule_type == 'not_null':
                    completeness_checks.append(_check('not_null', col.null_count, col.null_percentage, column=col.name))
                else:
                    result = rules.evaluate_unique(conn, schema, table, [rule.column])
                    invalid, total = result['invalid'], result['total']
                    uniqueness_checks.append(_check('unique', invalid, invalid / total * 100 if total else 0.0, column=rule.column,
                                                    message=f'{invalid} rows belong to duplicate key combinations.' if invalid else None))
                continue
            key = (rule.rule_type, rule.column, json.dumps(rule.params, sort_keys=True), rule.value)
            if key in seen:
                continue
            seen.add(key)
            if rule.rule_type == 'email_format':
                result = rules.evaluate_email_format(conn, schema, table, rule.column)
                invalid = result['invalid']
                message = f'{invalid} values do not match the expected email format.'
            elif rule.rule_type == 'allowed_values':
                result = rules.evaluate_allowed_values(conn, schema, table, rule.column, rule.params.get('values', []))
                invalid = result['outside']
                message = f'{invalid} values are outside the allowed set.'
            else:
                if rule.value is None:
                    raise ValueError(f'{rule.rule_type} requires a value')
                result = rules.evaluate_value_bound(conn, schema, table, rule.column, rule.value, rule.rule_type)
                invalid = result['invalid']
                message = f'{invalid} values violate {rule.rule_type} bound {rule.value}.'
            total = result['total']
            percentage = invalid / total * 100 if total else 0.0
            validity_checks.append(_check(rule.rule_type, invalid, percentage, column=rule.column,
                                          message=message if invalid else None))

    dimensions = {
        name: compute_dimension_score([check.dict() for check in checks])
        for name, checks in [('completeness', completeness_checks), ('uniqueness', uniqueness_checks), ('validity', validity_checks)]
    }
    checks = completeness_checks + uniqueness_checks + validity_checks
    return QualityResult(
        dataset={'source_id': source.id, 'schema': schema, 'table': table},
        score=round(weighted_score(dimensions, DEFAULT_WEIGHTS), 2),
        dimensions={name: round(score, 2) if score is not None else None for name, score in dimensions.items()},
        summary={'checks': len(checks), 'passed': sum(c.status == 'passed' for c in checks),
                 'warnings': sum(c.status == 'warning' for c in checks), 'failed': sum(c.status == 'failed' for c in checks)},
        checks=checks,
    )
