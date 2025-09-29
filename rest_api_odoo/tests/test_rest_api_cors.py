# -*- coding: utf-8 -*-
import json
from odoo.tests.common import HttpCase


class TestRestApiCors(HttpCase):
    """Tests para soporte CORS de la REST API"""

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
            'max_records_limit': 100
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

    def test_cors_headers_in_auth_response(self):
        """Test que las respuestas de auth incluyen headers CORS"""
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

        # Verificar headers CORS
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertIn('GET', response.headers['Access-Control-Allow-Methods'])
        self.assertIn('POST', response.headers['Access-Control-Allow-Methods'])

        self.assertIn('Access-Control-Allow-Headers', response.headers)
        self.assertIn('Authorization', response.headers['Access-Control-Allow-Headers'])

    def test_options_preflight_auth_endpoint(self):
        """Test petición OPTIONS al endpoint de autenticación"""
        response = self.opener.options(f'{self.base_url}/auth')

        self.assertEqual(response.status_code, 200)

        # Verificar headers CORS específicos para preflight
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        self.assertIn('Access-Control-Allow-Methods', response.headers)
        methods = response.headers['Access-Control-Allow-Methods']
        self.assertIn('POST', methods)
        self.assertIn('OPTIONS', methods)

        self.assertIn('Access-Control-Allow-Headers', response.headers)
        headers = response.headers['Access-Control-Allow-Headers']
        self.assertIn('Content-Type', headers)
        self.assertIn('Authorization', headers)

        self.assertIn('Access-Control-Max-Age', response.headers)

    def test_options_preflight_api_endpoint(self):
        """Test petición OPTIONS a endpoint de API"""
        response = self.opener.options(f'{self.base_url}/res.partner')

        self.assertEqual(response.status_code, 200)

        # Verificar headers CORS
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertIn('Access-Control-Allow-Headers', response.headers)

        methods = response.headers['Access-Control-Allow-Methods']
        self.assertIn('GET', methods)
        self.assertIn('POST', methods)
        self.assertIn('PUT', methods)
        self.assertIn('DELETE', methods)
        self.assertIn('OPTIONS', methods)

    def test_cors_headers_in_api_responses(self):
        """Test que las respuestas de API incluyen headers CORS"""
        token = self._get_auth_token()

        response = self.url_open(
            f'{self.base_url}/res.partner',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)

        # Verificar headers CORS en respuesta de datos
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertIn('Access-Control-Allow-Headers', response.headers)

    def test_cors_headers_in_error_responses(self):
        """Test que las respuestas de error incluyen headers CORS"""
        # Petición sin token (debe fallar con 401)
        response = self.url_open(f'{self.base_url}/res.partner')

        self.assertEqual(response.status_code, 401)

        # Verificar que incluso las respuestas de error tienen headers CORS
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

    def test_cors_with_custom_origin(self):
        """Test CORS con header Origin personalizado"""
        token = self._get_auth_token()

        response = self.url_open(
            f'{self.base_url}/res.partner',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Origin': 'https://example.com'
            }
        )

        self.assertEqual(response.status_code, 200)

        # Verificar que permite cualquier origen
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], '*')

    def test_axios_compatible_headers(self):
        """Test compatibilidad con headers típicos de axios"""
        token = self._get_auth_token()

        # Headers típicos que envía axios
        axios_headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'User-Agent': 'axios/1.12.2',
            'Accept-Encoding': 'gzip, compress, deflate, br'
        }

        response = self.url_open(
            f'{self.base_url}/res.partner',
            headers=axios_headers
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertTrue(response_data.get('success'))

    def test_alternative_auth_headers(self):
        """Test headers de autenticación alternativos (X-API-Key, api-key)"""
        token = self._get_auth_token()

        # Test con X-API-Key
        response1 = self.url_open(
            f'{self.base_url}/res.partner',
            headers={
                'X-API-Key': token,
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response1.status_code, 200)

        # Test con api-key
        response2 = self.url_open(
            f'{self.base_url}/res.partner',
            headers={
                'api-key': token,
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response2.status_code, 200)

    def test_options_with_custom_headers(self):
        """Test OPTIONS con headers personalizados en preflight"""
        headers = {
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type, Authorization, X-Custom-Header',
            'Origin': 'https://example.com'
        }

        response = self.opener.options(f'{self.base_url}/auth', headers=headers)

        self.assertEqual(response.status_code, 200)

        # Verificar que responde adecuadamente a preflight complejo
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertIn('Access-Control-Allow-Headers', response.headers)

    def test_cors_expose_headers(self):
        """Test que se exponen los headers correctos"""
        token = self._get_auth_token()

        response = self.url_open(
            f'{self.base_url}/res.partner',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)

        # Verificar Access-Control-Expose-Headers
        self.assertIn('Access-Control-Expose-Headers', response.headers)
        exposed_headers = response.headers['Access-Control-Expose-Headers']
        self.assertIn('Content-Type', exposed_headers)
        self.assertIn('Authorization', exposed_headers)