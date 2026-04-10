from fastapi.testclient import TestClient
from src.app import app, estimate_food_metrics


def test_estimate_food_metrics_branches():
    assert estimate_food_metrics('rice_bowl.png') == ('rice', 206.0, 0.1)
    assert estimate_food_metrics('APPLE.jpeg') == ('apple', 95.0, 19.0)
    assert estimate_food_metrics('unknown_food.jpg') == ('mixed_food', 250.0, 8.0)


def test_healthz_ok():
    client = TestClient(app)
    r = client.get('/healthz')
    assert r.status_code == 200
    assert r.json() == {'status': 'ok'}
