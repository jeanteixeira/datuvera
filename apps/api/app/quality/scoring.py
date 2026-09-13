from typing import List, Dict, Optional

WARNING_PERCENT = 5.0


def severity_from_percentage(percent: float) -> str:
    if percent == 0:
        return 'passed'
    if 0 < percent <= WARNING_PERCENT:
        return 'warning'
    return 'failed'


def check_score(failed_percentage: float) -> float:
    return max(0.0, min(100.0, 100.0 - failed_percentage))


def compute_dimension_score(checks: List[Dict]) -> Optional[float]:
    if not checks:
        return None
    return sum(check_score(c['failed_percentage']) for c in checks) / len(checks)


def weighted_score(dim_scores: Dict[str, Optional[float]], weights: Dict[str, float]) -> float:
    items = [(d, s) for d, s in dim_scores.items() if s is not None]
    if not items:
        return 0.0
    return sum(s * weights.get(d, 1.0) for d, s in items) / sum(weights.get(d, 1.0) for d, _ in items)
