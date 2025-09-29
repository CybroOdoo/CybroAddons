# -*- coding: utf-8 -*-
import json
from odoo.tests.common import HttpCase


class TestRestApiCrud(HttpCase):
    """Tests para operaciones CRUD de la REST API"""

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

        # Crear algunos partners de prueba
        self.test_partner1 = self.env['res.partner'].create({
            'name': 'Test Partner 1',
            'email': 'test1@example.com',
            'phone': '123456789',
            'is_company': False
        })

        self.test_partner2 = self.env['res.partner'].create({
            'name': 'Test Partner 2',
            'email': 'test2@example.com',
            'phone': '987654321',
            'is_company': True
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

    def test_get_all_records(self):
        """Test GET para obtener todos los registros"""
        token = self._get_auth_token()

        response = self.url_open(
            f'{self.base_url}/res.partner',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('success'))
        self.assertIn('data', response_data)
        self.assertIn('count', response_data)
        self.assertIsInstance(response_data['data'], list)
        self.assertGreater(response_data['count'], 0)

    def test_get_specific_record(self):
        """Test GET para obtener un registro específico"""
        token = self._get_auth_token()

        response = self.url_open(
            f'{self.base_url}/res.partner/{self.test_partner1.id}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('success'))
        self.assertEqual(response_data['count'], 1)

        partner_data = response_data['data'][0]
        self.assertEqual(partner_data['id'], self.test_partner1.id)

    def test_get_with_fields_filter(self):
        """Test GET con filtro de campos específicos"""
        token = self._get_auth_token()

        # Solo solicitar campos específicos
        params = 'fields=id,name,email'
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

        if response_data['data']:
            partner_data = response_data['data'][0]
            # Verificar que solo tiene los campos solicitados (más id siempre presente)
            expected_fields = {'id', 'name', 'email'}
            actual_fields = set(partner_data.keys())
            # Los campos solicitados deben estar presentes
            self.assertTrue(expected_fields.issubset(actual_fields))

    def test_get_with_domain_filter(self):
        """Test GET con filtro de dominio"""
        token = self._get_auth_token()

        # Filtrar por companies
        domain = json.dumps([('is_company', '=', True)])
        params = f'domain={domain}'

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
        # Debería encontrar al menos nuestro test_partner2 que es company
        self.assertGreater(response_data['count'], 0)

    def test_get_with_pagination(self):
        """Test GET con paginación"""
        token = self._get_auth_token()

        # Primera página
        params = 'limit=1&offset=0'
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
        self.assertEqual(response_data['count'], 1)
        self.assertIn('limit', response_data)
        self.assertIn('offset', response_data)
        self.assertEqual(response_data['limit'], 1)
        self.assertEqual(response_data['offset'], 0)

    def test_post_create_record(self):
        """Test POST para crear un nuevo registro"""
        token = self._get_auth_token()

        new_partner_data = {
            'values': {
                'name': 'New Test Partner',
                'email': 'newtest@example.com',
                'phone': '555666777',
                'is_company': False
            }
        }

        response = self.url_open(
            f'{self.base_url}/res.partner',
            data=json.dumps(new_partner_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('success'))
        self.assertIn('data', response_data)
        self.assertEqual(response_data['count'], 1)

        # Verificar que el registro fue creado
        created_partner = response_data['data'][0]
        self.assertEqual(created_partner['name'], 'New Test Partner')

        # Limpiar: eliminar el partner creado
        partner_to_delete = self.env['res.partner'].browse(created_partner['id'])
        partner_to_delete.unlink()

    def test_put_update_record(self):
        """Test PUT para actualizar un registro"""
        token = self._get_auth_token()

        # Crear un partner para actualizar
        test_partner = self.env['res.partner'].create({
            'name': 'Partner to Update',
            'email': 'update@example.com'
        })

        update_data = {
            'values': {
                'name': 'Updated Partner Name',
                'phone': '999888777'
            }
        }

        response = self.url_open(
            f'{self.base_url}/res.partner/{test_partner.id}',
            data=json.dumps(update_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('success'))

        # Verificar que el registro fue actualizado
        updated_partner = response_data['data'][0]
        self.assertEqual(updated_partner['name'], 'Updated Partner Name')

        # Verificar en la base de datos
        test_partner.refresh()
        self.assertEqual(test_partner.name, 'Updated Partner Name')
        self.assertEqual(test_partner.phone, '999888777')

        # Limpiar
        test_partner.unlink()

    def test_delete_record(self):
        """Test DELETE para eliminar un registro"""
        token = self._get_auth_token()

        # Crear un partner para eliminar
        test_partner = self.env['res.partner'].create({
            'name': 'Partner to Delete',
            'email': 'delete@example.com'
        })
        partner_id = test_partner.id

        response = self.url_open(
            f'{self.base_url}/res.partner/{partner_id}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('success'))
        self.assertIn('deleted_record', response_data)
        self.assertEqual(response_data['deleted_record']['id'], partner_id)

        # Verificar que el registro ya no existe
        self.assertFalse(self.env['res.partner'].browse(partner_id).exists())

    def test_get_with_order(self):
        """Test GET con ordenamiento"""
        token = self._get_auth_token()

        # Ordenar por nombre descendente
        params = 'order=name desc&limit=5'
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

        # Verificar que hay datos y están ordenados
        if len(response_data['data']) > 1:
            names = [partner['name'] for partner in response_data['data']]
            # Verificar orden descendente
            self.assertTrue(all(names[i] >= names[i+1] for i in range(len(names)-1)))

    def test_method_not_allowed(self):
        """Test que métodos no permitidos devuelven error 405"""
        token = self._get_auth_token()

        # Desactivar DELETE para este test
        self.api_config.is_delete = False

        response = self.url_open(
            f'{self.base_url}/res.partner/{self.test_partner1.id}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertTrue(response_data.get('error'))
        self.assertIn('METHOD_NOT_ALLOWED', response_data.get('error_code', ''))

        # Restaurar configuración
        self.api_config.is_delete = True

    def test_record_not_found(self):
        """Test GET de registro inexistente"""
        token = self._get_auth_token()

        # ID que no existe
        non_existent_id = 999999

        response = self.url_open(
            f'{self.base_url}/res.partner/{non_existent_id}',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode('utf-8'))

        # Debería devolver lista vacía
        self.assertTrue(response_data.get('success'))
        self.assertEqual(response_data['count'], 0)
        self.assertEqual(len(response_data['data']), 0)

    def test_model_not_configured(self):
        """Test acceso a modelo no configurado para API"""
        token = self._get_auth_token()

        # Intentar acceder a un modelo que no tiene configuración de API
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
        self.assertIn('MODEL_NOT_CONFIGURED', response_data.get('error_code', ''))