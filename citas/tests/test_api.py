import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from datetime import date, timedelta

Usuario = get_user_model()


@pytest.fixture
def test_client():
    return Client()


@pytest.fixture
def db_user(db):
    user = Usuario.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='test123',
        rol='admin'
    )
    return user


def test_register(test_client, db):
    response = test_client.post('/api/auth/register/', {
        'username': 'newuser',
        'first_name': 'Nuevo',
        'last_name': 'Usuario',
        'email': 'new@test.com',
        'password': 'pass123',
        'rol': 'paciente'
    })
    assert response.status_code == 201


def test_login_invalid(test_client, db):
    response = test_client.post('/api/token/', {
        'username': 'wrong@test.com',
        'password': 'wrong'
    })
    assert response.status_code == 401


def test_swagger(test_client):
    response = test_client.get('/swagger/')
    assert response.status_code in [200, 301, 401]