# -*- coding: utf-8 -*-
import json
import jwt
from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase
from odoo.tests.common import HttpCase
from odoo import http


class TestRestApiAuth(HttpCase):
    """Tests para autenticación JWT de la REST API"""

    def setUp(self):
        super().setUp()
        self.api_base_url = '/api/v1'
        self.admin_user = self.env.ref('base.user_admin')
        self.demo_user = self.env.ref('base.user_demo')

        # Limpiar configuraciones existentes de API para res.users
        model_users = self.env['ir.model'].search([('model', '=', 'res.users')], limit=1)
        existing_configs = self.env['connection.api'].search([('model_id', '=', model_users.id)])
        if existing_configs:
            existing_configs.unlink()

        # Crear configuración de API para res.users
        self.api_config = self.env['connection.api'].create({
            'model_id': model_users.id,
            'active': True,
            'is_get': True,
            'is_post': True,
            'is_put': True,
            'is_delete': False,
            'max_records_limit': 100
        })

    def test_auth_endpoint_success(self):
        """Test autenticación exitosa"""
        auth_data = {
            'username': 'admin',
            'password': 'admin',
            'database': self.env.cr.dbname,
            'expires_in_hours': 24
        }

        response = self.url_open(
            f'{self.api_base_url}/auth',
            data=json.dumps(auth_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('success'))
        self.assertIn('data', response_data)
        self.assertIn('access_token', response_data['data'])
        self.assertIn('user_id', response_data['data'])
        self.assertEqual(response_data['data']['username'], 'admin')
        self.assertEqual(response_data['data']['token_type'], 'Bearer')

    def test_auth_endpoint_invalid_credentials(self):
        """Test autenticación con credenciales inválidas"""
        auth_data = {
            'username': 'admin',
            'password': 'wrong_password',
            'database': self.env.cr.dbname
        }

        response = self.url_open(
            f'{self.api_base_url}/auth',
            data=json.dumps(auth_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('Credenciales inválidas', response_data.get('message', ''))

    def test_auth_endpoint_missing_data(self):
        """Test autenticación sin datos requeridos"""
        auth_data = {
            'username': 'admin'
            # password faltante
        }

        response = self.url_open(
            f'{self.api_base_url}/auth',
            data=json.dumps(auth_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('Username y password son requeridos', response_data.get('message', ''))

    def test_auth_endpoint_invalid_json(self):
        """Test autenticación con JSON inválido"""
        response = self.url_open(
            f'{self.api_base_url}/auth',
            data=b'invalid json data',
            headers={'Content-Type': 'application/json'}
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('JSON inválido', response_data.get('message', ''))

    def test_jwt_token_validation(self):
        """Test validación de JWT token"""
        # Primero obtener un token válido
        auth_data = {
            'username': 'admin',
            'password': 'admin',
            'database': self.env.cr.dbname
        }

        auth_response = self.url_open(
            f'{self.api_base_url}/auth',
            data=json.dumps(auth_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        auth_data_response = json.loads(auth_response.content.decode('utf-8'))
        token = auth_data_response['data']['access_token']

        # Usar el token para hacer una petición
        response = self.url_open(
            f'{self.api_base_url}/res.users',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertTrue(response_data.get('success'))

    def test_expired_token(self):
        """Test con token expirado"""
        # Crear un token expirado manualmente
        from datetime import datetime, timedelta
        from odoo.addons.rest_api_odoo.controllers.jwt_auth import JWTAuthMixin

        jwt_mixin = JWTAuthMixin()
        secret = jwt_mixin._get_jwt_secret()

        # Token que expira en el pasado
        expired_payload = {
            'user_id': self.admin_user.id,
            'iat': datetime.utcnow() - timedelta(hours=25),
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iss': 'odoo-rest-api',
            'aud': 'odoo-client'
        }

        expired_token = jwt.encode(expired_payload, secret, algorithm='HS256')

        response = self.url_open(
            f'{self.api_base_url}/res.users',
            headers={
                'Authorization': f'Bearer {expired_token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertTrue(response_data.get('error'))
        self.assertIn('Token expirado', response_data.get('message', ''))

    def test_refresh_token_endpoint(self):
        """Test endpoint de refresh token"""
        # Primero obtener un token válido
        auth_data = {
            'username': 'admin',
            'password': 'admin',
            'database': self.env.cr.dbname
        }

        auth_response = self.url_open(
            f'{self.api_base_url}/auth',
            data=json.dumps(auth_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        auth_data_response = json.loads(auth_response.content.decode('utf-8'))
        original_token = auth_data_response['data']['access_token']

        # Refrescar el token
        refresh_data = {'expires_in_hours': 48}

        refresh_response = self.url_open(
            f'{self.api_base_url}/refresh',
            data=json.dumps(refresh_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {original_token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(refresh_response.status_code, 200)
        refresh_data_response = json.loads(refresh_response.content.decode('utf-8'))

        self.assertTrue(refresh_data_response.get('success'))
        self.assertIn('access_token', refresh_data_response['data'])
        self.assertNotEqual(
            original_token,
            refresh_data_response['data']['access_token']
        )

    def test_health_check_endpoint(self):
        """Test endpoint de health check"""
        response = self.url_open(f'{self.api_base_url}/health')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response_data.get('status'), 'healthy')
        self.assertIn('database', response_data)
        self.assertIn('active_models', response_data)
        self.assertIn('jwt_configured', response_data)
        self.assertTrue(response_data.get('jwt_configured'))

    def test_models_list_endpoint(self):
        """Test endpoint de listado de modelos disponibles"""
        # Primero autenticarse
        auth_data = {
            'username': 'admin',
            'password': 'admin',
            'database': self.env.cr.dbname
        }

        auth_response = self.url_open(
            f'{self.api_base_url}/auth',
            data=json.dumps(auth_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        auth_data_response = json.loads(auth_response.content.decode('utf-8'))
        token = auth_data_response['data']['access_token']

        # Obtener lista de modelos
        response = self.url_open(
            f'{self.api_base_url}/models',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('success'))
        self.assertIn('data', response_data)
        self.assertIn('documentation', response_data)
        self.assertIn('authentication', response_data)

        # Verificar que nuestro modelo de test está en la lista
        models = response_data['data']
        model_names = [model['model'] for model in models]
        self.assertIn('res.users', model_names)