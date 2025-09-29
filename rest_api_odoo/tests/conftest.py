# -*- coding: utf-8 -*-
"""
Configuración de pytest para tests de REST API
"""

import pytest
import os
import sys

# Agregar el directorio del módulo al path
module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, module_dir)


@pytest.fixture(scope="session")
def odoo_env():
    """
    Fixture para configurar el entorno de Odoo para tests
    """
    # Esta fixture se puede usar si se ejecutan tests fuera del framework de Odoo
    pass


@pytest.fixture
def api_client():
    """
    Fixture para cliente HTTP de pruebas
    """
    import requests

    class ApiClient:
        def __init__(self, base_url="http://localhost:8069/api/v1"):
            self.base_url = base_url
            self.session = requests.Session()
            self.token = None

        def authenticate(self, username="admin", password="admin", database="test"):
            """Autenticar y obtener token"""
            auth_data = {
                'username': username,
                'password': password,
                'database': database
            }

            response = self.session.post(
                f"{self.base_url}/auth",
                json=auth_data
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data['data']['access_token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.token}'
                })
                return True
            return False

        def get(self, endpoint, **kwargs):
            """GET request"""
            return self.session.get(f"{self.base_url}/{endpoint}", **kwargs)

        def post(self, endpoint, **kwargs):
            """POST request"""
            return self.session.post(f"{self.base_url}/{endpoint}", **kwargs)

        def put(self, endpoint, **kwargs):
            """PUT request"""
            return self.session.put(f"{self.base_url}/{endpoint}", **kwargs)

        def delete(self, endpoint, **kwargs):
            """DELETE request"""
            return self.session.delete(f"{self.base_url}/{endpoint}", **kwargs)

        def options(self, endpoint, **kwargs):
            """OPTIONS request"""
            return self.session.options(f"{self.base_url}/{endpoint}", **kwargs)

    return ApiClient


@pytest.fixture
def sample_partner_data():
    """
    Fixture con datos de ejemplo para partners
    """
    return {
        'values': {
            'name': 'Test Partner',
            'email': 'test@example.com',
            'phone': '123456789',
            'is_company': False,
            'street': '123 Test Street',
            'city': 'Test City',
            'zip': '12345'
        }
    }


@pytest.fixture
def jwt_secret():
    """
    Fixture con clave secreta JWT para tests
    """
    return "test_jwt_secret_key_for_tests_only"


# Configuración de pytest
def pytest_configure(config):
    """
    Configuración global de pytest
    """
    # Agregar marcadores personalizados
    config.addinivalue_line(
        "markers", "slow: marca tests como lentos"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "unit: marca tests unitarios"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modificar items de la colección de tests
    """
    # Agregar marcador 'slow' a tests que tomen más tiempo
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)