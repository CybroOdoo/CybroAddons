# -*- coding: utf-8 -*-
import json
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from odoo.tests.common import HttpCase


class TestRestApiErrors(HttpCase):
    """Tests para manejo de errores de la REST API"""

    def setUp(self):
        super().setUp()
        self.base_url = '/api/v1'

        # Crear configuración de API para res.partner
        model_partner = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.api_config = self.env['connection.api'].create({
            'name': 'Test Partners API',
            'model_id': model_partner.id,
            'active': True,
            'is_get': True,
            'is_post': True,
            'is_put': True,
            'is_delete': True,
            'max_records_limit': 10
        })

    def _get_auth_token(self):
        """Helper para obtener token de autenticación"""
        auth_data = {
            'username': 'admin',
            'password': 'admin',
            'database': self.env.cr.dbname
        }

        response = self.url_open(
            f'{self.base_url}/auth',
            data=json.dumps(auth_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        response_data = json.loads(response.content.decode('utf-8'))
        return response_data['data']['access_token']

    def test_authentication_failed_no_token(self):
        """Test acceso sin token de autenticación"""
        response = self.url_open(f'{self.base_url}/res.partner')

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertEqual(response_data.get('error_code'), 'AUTHENTICATION_FAILED')
        self.assertIn('Token de autorización no proporcionado', response_data.get('message', ''))

    def test_authentication_failed_invalid_token(self):
        """Test con token inválido"""
        response = self.url_open(
            f'{self.base_url}/res.partner',
            headers={
                'Authorization': 'Bearer invalid_token_here',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertEqual(response_data.get('error_code'), 'AUTHENTICATION_FAILED')

    def test_authentication_failed_malformed_token(self):
        """Test con token mal formado"""
        response = self.url_open(
            f'{self.base_url}/res.partner',
            headers={
                'Authorization': 'InvalidFormat token_here',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertEqual(response_data.get('error_code'), 'AUTHENTICATION_FAILED')

    def test_model_not_found(self):
        """Test acceso a modelo que no existe"""
        token = self._get_auth_token()

        response = self.url_open(
            f'{self.base_url}/non.existent.model',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertEqual(response_data.get('error_code'), 'MODEL_NOT_CONFIGURED')

    def test_model_not_configured_for_api(self):
        """Test acceso a modelo no configurado para API"""
        token = self._get_auth_token()

        # res.country no tiene configuración de API en este test
        response = self.url_open(
            f'{self.base_url}/res.country',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertEqual(response_data.get('error_code'), 'MODEL_NOT_CONFIGURED')

    def test_method_not_allowed(self):
        """Test método no permitido para el modelo"""
        token = self._get_auth_token()

        # Desactivar POST para este test
        original_is_post = self.api_config.is_post
        self.api_config.is_post = False

        create_data = {
            'values': {
                'name': 'Test Partner',
                'email': 'test@example.com'
            }
        }

        response = self.url_open(
            f'{self.base_url}/res.partner',
            data=json.dumps(create_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertEqual(response_data.get('error_code'), 'METHOD_NOT_ALLOWED')

        # Restaurar configuración
        self.api_config.is_post = original_is_post

    def test_invalid_json_in_post(self):
        """Test POST con JSON inválido"""
        token = self._get_auth_token()

        response = self.url_open(
            f'{self.base_url}/res.partner',
            data=b'{"invalid": json syntax}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertEqual(response_data.get('error_code'), 'INVALID_REQUEST_DATA')

    def test_missing_values_in_post(self):
        """Test POST sin campo 'values'"""
        token = self._get_auth_token()

        invalid_data = {
            'name': 'Test Partner'  # Falta 'values' wrapper
        }

        response = self.url_open(
            f'{self.base_url}/res.partner',
            data=json.dumps(invalid_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('values', response_data.get('message', '').lower())

    def test_missing_values_in_put(self):
        """Test PUT sin campo 'values'"""
        token = self._get_auth_token()

        # Crear un partner para intentar actualizar
        test_partner = self.env['res.partner'].create({
            'name': 'Partner to Update',
            'email': 'update@example.com'
        })

        invalid_data = {
            'name': 'Updated Name'  # Falta 'values' wrapper
        }

        response = self.url_open(
            f'{self.base_url}/res.partner/{test_partner.id}',
            data=json.dumps(invalid_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('values', response_data.get('message', '').lower())

        # Limpiar
        test_partner.unlink()

    def test_put_without_record_id(self):
        """Test PUT sin especificar ID de registro"""
        token = self._get_auth_token()

        update_data = {
            'values': {
                'name': 'Updated Name'
            }
        }

        response = self.url_open(
            f'{self.base_url}/res.partner',  # Sin ID
            data=json.dumps(update_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('ID de registro requerido', response_data.get('message', ''))

    def test_put_nonexistent_record(self):
        """Test PUT en registro que no existe"""
        token = self._get_auth_token()

        update_data = {
            'values': {
                'name': 'Updated Name'
            }
        }

        non_existent_id = 999999

        response = self.url_open(
            f'{self.base_url}/res.partner/{non_existent_id}',
            data=json.dumps(update_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('Registro no encontrado', response_data.get('message', ''))

    def test_delete_without_record_id(self):
        """Test DELETE sin especificar ID de registro"""
        token = self._get_auth_token()

        response = self.url_open(
            f'{self.base_url}/res.partner',  # Sin ID
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('ID de registro requerido', response_data.get('message', ''))

    def test_delete_nonexistent_record(self):
        """Test DELETE en registro que no existe"""
        token = self._get_auth_token()

        non_existent_id = 999999

        response = self.url_open(
            f'{self.base_url}/res.partner/{non_existent_id}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('Registro no encontrado', response_data.get('message', ''))

    def test_invalid_domain_syntax(self):
        """Test GET con sintaxis de domain inválida"""
        token = self._get_auth_token()

        # Domain con sintaxis inválida
        invalid_domain = "invalid domain syntax"
        params = f'domain={invalid_domain}'

        response = self.url_open(
            f'{self.base_url}/res.partner?{params}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        # Debería procesar la request sin el domain (ignorándolo)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertTrue(response_data.get('success'))

    def test_limit_exceeds_maximum(self):
        """Test GET con limit que excede el máximo configurado"""
        token = self._get_auth_token()

        # El límite configurado es 10, solicitar más
        params = 'limit=100'

        response = self.url_open(
            f'{self.base_url}/res.partner?{params}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('success'))
        # Debería limitarse al máximo configurado
        if 'limit' in response_data:
            self.assertLessEqual(response_data['limit'], 10)

    def test_invalid_limit_value(self):
        """Test GET con valor de limit inválido"""
        token = self._get_auth_token()

        # Limit no numérico
        params = 'limit=invalid'

        response = self.url_open(
            f'{self.base_url}/res.partner?{params}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        # Debería procesar sin el limit (ignorándolo)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertTrue(response_data.get('success'))

    def test_validation_error_in_create(self):
        """Test POST con datos que causan error de validación"""
        token = self._get_auth_token()

        # Intentar crear partner sin name (campo requerido)
        invalid_data = {
            'values': {
                'email': 'test@example.com'
                # name faltante
            }
        }

        response = self.url_open(
            f'{self.base_url}/res.partner',
            data=json.dumps(invalid_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('Error creando registro', response_data.get('message', ''))

    def test_cors_headers_in_error_responses(self):
        """Test que las respuestas de error incluyen headers CORS"""
        # Test con error 401
        response = self.url_open(f'{self.base_url}/res.partner')

        self.assertEqual(response.status_code, 401)

        # Verificar headers CORS en respuesta de error
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo._logger')
    def test_internal_server_error_handling(self, mock_logger):
        """Test manejo de errores internos del servidor"""
        token = self._get_auth_token()

        # Simular error interno con mock
        with patch('odoo.http.request.env') as mock_env:
            mock_env.__getitem__.side_effect = Exception("Simulated internal error")

            response = self.url_open(
                f'{self.base_url}/res.partner',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
            )

            self.assertEqual(response.status_code, 500)
            response_data = json.loads(response.content.decode('utf-8'))

            self.assertTrue(response_data.get('error'))
            self.assertEqual(response_data.get('error_code'), 'INTERNAL_SERVER_ERROR')
            self.assertIn('Error interno del servidor', response_data.get('message', ''))