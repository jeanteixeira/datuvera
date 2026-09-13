from math import isfinite
from app.quality.types import RuleType


def validate_parameters(rule: RuleType, parameters: dict) -> dict:
    if rule in ('not_null', 'unique', 'email_format'):
        if parameters:
            raise ValueError('This rule accepts no parameters')
    elif rule in ('min_value', 'max_value'):
        value = parameters.get('value')
        if set(parameters) != {'value'} or isinstance(value, bool) or not isinstance(value, (int, float)) or (isinstance(value, float) and not isfinite(value)):
            raise ValueError('A finite numeric value is required')
    elif rule == 'allowed_values':
        values = parameters.get('values')
        if set(parameters) != {'values'} or not isinstance(values, list) or not values:
            raise ValueError('A non-empty values list is required')
        if any(value is None or not isinstance(value, (str, int, float, bool)) or
               (isinstance(value, float) and not isfinite(value)) for value in values):
            raise ValueError('Values must be non-null JSON scalars')
    return parameters
