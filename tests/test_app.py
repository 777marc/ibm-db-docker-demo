import json
import os

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_ping(client):
    rv = client.get('/ping')
    assert rv.status_code == 200
    assert rv.get_json() == {'status': 'pong'}


def test_query_missing_sql(client):
    rv = client.post('/query', json={})
    assert rv.status_code == 400
    assert 'missing sql' in rv.get_json().get('error')


def test_query_non_select(client):
    rv = client.post('/query', json={'sql': 'DROP TABLE foo'})
    assert rv.status_code == 400
    assert 'only SELECT allowed' in rv.get_json().get('error')
