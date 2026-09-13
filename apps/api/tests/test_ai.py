import copy
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.ai.context import build_safe_context
from app.ai.engine import generate_insights
from app.ai.config import ai_status, get_ai_provider
from app.ai.models import AIInsightResult
from app.ai.providers.base import AIProvider, AIProviderError
from app.api.v1 import endpoints
from app.core.config import settings
from app.main import app
from app.profiling.models import DatasetProfile, ColumnProfile, ColumnTopValue
from app.quality.models import QualityResult, CheckResult


@pytest.fixture
def results():
    profile = {
        'dataset': DatasetProfile(source_id=1, schema='public', table='customers', row_count=500,
                                  column_count=2, estimated_size_bytes=1024, generated_at=datetime(2026, 1, 1)),
        'columns': [
            ColumnProfile(name='email', data_type='TEXT', nullable=True, null_count=15, null_percentage=3,
                          distinct_count=476, distinct_percentage=95.2, min='private@example.com',
                          top_values=[ColumnTopValue(value='private@example.com', count=1)]),
            ColumnProfile(name='lifetime_value', data_type='NUMERIC', nullable=True, null_count=12,
                          null_percentage=2.4, distinct_count=488, distinct_percentage=97.6,
                          min=Decimal('1.23'), max=Decimal('615'), mean=307.8277),
        ],
        'raw_rows': [{'email': 'private@example.com', 'name': 'Private Customer'}],
        'password': 'source-password-marker',
    }
    quality = QualityResult(dataset={'source_id': 1, 'password': 'source-password-marker'}, score=99.11,
                            dimensions={'completeness': 99.33, 'uniqueness': 100, 'validity': 98},
                            summary={'checks': 1, 'warnings': 1, 'failed': 0, 'passed': 0},
                            checks=[CheckResult(column='email', rule='not_null', status='warning', passed=False,
                                                failed_count=15, failed_percentage=3, score=97,
                                                message='private@example.com source-password-marker')])
    return profile, quality


@pytest.fixture
def insight_json():
    return {
        'summary': 'The supplied results report a 99.11 quality score, with missing email values.',
        'risk_level': 'low',
        'findings': [{'severity': 'medium', 'title': 'Missing email values',
                      'description': '15 of 500 rows have NULL email values (3%).', 'column': 'email'}],
        'suggested_checks': [{'column': 'lifetime_value', 'rule': 'min_value',
                              'reason': 'Consider this check if negative lifetime values are invalid in your business domain.',
                              'parameters': {'value': 0, 'values': None}}],
    }


class FakeProvider:
    def __init__(self, result):
        self.result = result
        self.context = None

    def generate_insights(self, context):
        self.context = context
        return self.result


@pytest.fixture(autouse=True)
def offline_ai(monkeypatch):
    monkeypatch.setattr(settings, 'DATUVERA_AI_ENABLED', False)
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', None)
    # Accidental use of the live SDK is a test failure, not a billable request.
    import app.ai.providers.openai as provider_module
    monkeypatch.setattr(provider_module, 'OpenAI', MagicMock(side_effect=AssertionError('Live SDK forbidden in tests')))


def test_safe_context_allowlist_and_sensitive_values(results):
    context = build_safe_context(*results)
    serialized = context.model_dump_json(by_alias=True, exclude_none=True)
    for forbidden in ['top_values', 'raw_rows', 'private@example.com', 'Private Customer', 'source-password-marker',
                      'password', 'generated_at', 'source_id', 'message']:
        assert forbidden not in serialized
    assert context.dataset.row_count == 500
    assert context.columns[0].null_percentage == 3
    assert context.columns[0].min is None
    assert context.columns[1].min == 1.23
    assert context.columns[1].mean == 307.8277
    assert context.quality.score == 99.11
    assert context.quality.issues[0].failed_count == 15


def test_fake_provider_abstraction_and_core_unchanged(results, insight_json):
    before = copy.deepcopy(results)
    provider: AIProvider = FakeProvider(insight_json)
    output = generate_insights(*results, provider)
    assert isinstance(output, AIInsightResult)
    assert output.model_dump() == insight_json
    assert provider.context.quality.score == 99.11
    assert results == before


@pytest.mark.parametrize('mutation', ['rule', 'severity', 'risk', 'too_many', 'extra', 'parameters'])
def test_structured_output_rejects_invalid_values(insight_json, mutation):
    if mutation == 'rule': insight_json['suggested_checks'][0]['rule'] = 'execute_sql'
    if mutation == 'severity': insight_json['findings'][0]['severity'] = 'critical'
    if mutation == 'risk': insight_json['risk_level'] = 'critical'
    if mutation == 'too_many': insight_json['findings'] *= 6
    if mutation == 'extra': insight_json['quality_score'] = 0
    if mutation == 'parameters': insight_json['suggested_checks'][0]['parameters']['value'] = None
    with pytest.raises(ValidationError):
        AIInsightResult.model_validate(insight_json)


@pytest.mark.parametrize('field', ['findings', 'suggested_checks'])
def test_engine_rejects_invented_columns(results, insight_json, field):
    insight_json[field][0]['column'] = 'invented'
    with pytest.raises(AIProviderError):
        generate_insights(*results, FakeProvider(insight_json))


@pytest.mark.parametrize('enabled,key', [(False, 'key-marker'), (True, None), (True, ''), (True, '  ')])
def test_unconfigured_status_and_provider(enabled, key, monkeypatch):
    monkeypatch.setattr(settings, 'DATUVERA_AI_ENABLED', enabled)
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', SecretStr(key) if key is not None else None)
    assert ai_status().model_dump() == {'enabled': False, 'provider': None, 'model': None}
    assert get_ai_provider() is None


def test_enabled_status_hides_api_key(monkeypatch):
    monkeypatch.setattr(settings, 'DATUVERA_AI_ENABLED', True)
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', SecretStr('key-marker'))
    with TestClient(app) as client:
        response = client.get('/api/v1/ai/status')
    assert response.json() == {'enabled': True, 'provider': 'openai', 'model': settings.DATUVERA_AI_MODEL}
    assert 'key-marker' not in response.text
    assert 'key-marker' not in repr(settings)


def test_disabled_endpoint_never_profiles(monkeypatch):
    profile = MagicMock()
    monkeypatch.setattr(endpoints, 'profile_table_from_source', profile)
    with TestClient(app) as client:
        assert client.get('/api/v1/ai/status').json()['enabled'] is False
        response = client.post('/api/v1/sources/1/insights', json={'schema': 'public', 'table': 'customers'})
    assert response.status_code == 503
    assert response.json() == {'detail': 'AI Insights is not configured.'}
    profile.assert_not_called()


@pytest.fixture
def fake_endpoint(results, insight_json, monkeypatch):
    profile, quality = results
    monkeypatch.setattr(settings, 'DATUVERA_AI_ENABLED', True)
    monkeypatch.setattr(settings, 'OPENAI_API_KEY', SecretStr('key-marker'))
    provider = FakeProvider(insight_json)
    app.dependency_overrides[get_ai_provider] = lambda: provider
    app.dependency_overrides[endpoints.get_db] = lambda: object()
    source = SimpleNamespace(host='unused', port=5432, database='demo', username='demo', password='source-password-marker')
    monkeypatch.setattr(endpoints.DataSourceService, 'get', lambda *args: source)
    monkeypatch.setattr(endpoints, 'profile_table_from_source', lambda *args: profile)
    monkeypatch.setattr(endpoints, 'run_quality', lambda *args: quality)
    monkeypatch.setattr(endpoints.QualityRuleService, 'effective', lambda *args: [])
    try:
        yield TestClient(app), provider
    finally:
        app.dependency_overrides.pop(get_ai_provider, None)
        app.dependency_overrides.pop(endpoints.get_db, None)


def test_insights_endpoint_fake_structured_result(fake_endpoint, insight_json):
    client, provider = fake_endpoint
    response = client.post('/api/v1/sources/1/insights', json={'schema': 'public', 'table': 'customers'})
    assert response.status_code == 200
    assert client.get('/api/v1/ai/status').json()['enabled'] is True
    assert response.json() == insight_json
    assert 'source-password-marker' not in response.text
    assert 'top_values' not in provider.context.model_dump_json()


def test_provider_failure_safe_response_and_logs(fake_endpoint, caplog):
    client, provider = fake_endpoint
    provider.generate_insights = MagicMock(side_effect=RuntimeError('key-marker raw-response-marker private@example.com'))
    response = client.post('/api/v1/sources/1/insights', json={'schema': 'public', 'table': 'customers'})
    assert response.status_code == 502
    assert response.json() == {'detail': 'AI provider failed to generate valid insights.'}
    for marker in ['key-marker', 'raw-response-marker', 'private@example.com']:
        assert marker not in response.text + caplog.text


def test_invalid_provider_output_mapped_to_502(fake_endpoint):
    client, provider = fake_endpoint
    provider.result = {'summary': 'invalid'}
    assert client.post('/api/v1/sources/1/insights', json={'schema': 'public', 'table': 'customers'}).status_code == 502


def test_insights_missing_source_and_invalid_payload(fake_endpoint, monkeypatch):
    client, _ = fake_endpoint
    monkeypatch.setattr(endpoints.DataSourceService, 'get', lambda *args: None)
    assert client.post('/api/v1/sources/1/insights', json={'schema': 'public', 'table': 'customers'}).status_code == 404
    assert client.post('/api/v1/sources/1/insights', json={'schema': 'public'}).status_code == 422


def test_openai_sdk_structured_call_is_safe(results, insight_json, monkeypatch):
    import app.ai.providers.openai as module
    client = MagicMock()
    client.responses.parse.return_value = SimpleNamespace(status='completed', output_parsed=AIInsightResult.model_validate(insight_json))
    factory = MagicMock()
    factory.return_value.__enter__.return_value = client
    monkeypatch.setattr(module, 'OpenAI', factory)
    result = module.OpenAIProvider('key-marker', 'gpt-5.4-mini').generate_insights(build_safe_context(*results))
    assert result.summary == insight_json['summary']
    kwargs = client.responses.parse.call_args.kwargs
    assert kwargs['text_format'] is AIInsightResult
    assert kwargs['store'] is False
    assert 'tools' not in kwargs
    for marker in ['top_values', 'private@example.com', 'source-password-marker', 'key-marker']:
        assert marker not in str(kwargs)
    assert factory.call_args.kwargs['max_retries'] == 0


@pytest.mark.parametrize('status,parsed', [('incomplete', None), ('completed', None)])
def test_openai_refusal_or_incomplete_result(results, status, parsed, monkeypatch):
    import app.ai.providers.openai as module
    factory = MagicMock()
    factory.return_value.__enter__.return_value.responses.parse.return_value = SimpleNamespace(status=status, output_parsed=parsed)
    monkeypatch.setattr(module, 'OpenAI', factory)
    with pytest.raises(AIProviderError):
        module.OpenAIProvider('key-marker', 'model').generate_insights(build_safe_context(*results))


def test_official_sdk_parses_structured_response_offline(results, insight_json, monkeypatch):
    import json
    import httpx
    from openai import OpenAI as SDKClient
    import app.ai.providers.openai as module
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            'id': 'resp_offline', 'object': 'response', 'created_at': 0, 'status': 'completed',
            'model': 'gpt-5.4-mini',
            'output': [{'id': 'msg_offline', 'type': 'message', 'role': 'assistant', 'status': 'completed',
                        'content': [{'type': 'output_text', 'text': json.dumps(insight_json), 'annotations': []}]}],
        })

    monkeypatch.setattr(module, 'OpenAI', lambda **kwargs: SDKClient(
        **kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond))))
    result = module.OpenAIProvider('fake-test-key', 'gpt-5.4-mini').generate_insights(build_safe_context(*results))
    assert result.model_dump() == insight_json
    assert len(requests) == 1
    payload = requests[0]
    schema = payload['text']['format']
    assert schema['type'] == 'json_schema' and schema['strict'] is True
    assert schema['schema']['additionalProperties'] is False
    assert schema['schema']['properties']['findings']['maxItems'] == 5
    assert schema['schema']['properties']['suggested_checks']['maxItems'] == 5
    assert payload['store'] is False
    assert 'top_values' not in str(payload) and 'private@example.com' not in str(payload)
