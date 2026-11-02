# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for REST API controller methods and endpoints."""
import json
from unittest.mock import MagicMock, patch
import odoo.http
from odoo.fields import Command
from odoo.http import Response
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.rest_api_odoo.controllers.rest_api_odoo import RestApi


@tagged('post_install', '-at_install')
class TestRestApiOdoo(TransactionCase):
    """Test cases for RestApi controller methods and endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = RestApi()
        cls.partner_model = cls.env['ir.model'].search(
            [('model', '=', 'res.partner')], limit=1
        )

        admin_group = cls.env.ref('base.group_system')
        user_group = cls.env.ref('base.group_user')
        cls.user = cls.env['res.users'].create({
            'name': 'API Controller Test User',
            'login': 'api_controller_user',
            'email': 'api_controller_user@example.com',
            'group_ids': [Command.set([user_group.id, admin_group.id])],
        })
        cls.valid_api_key = cls.user.generate_api(cls.user.login)

        # Create test partner record
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'API Test Partner',
            'email': 'partner_test@example.com',
        })

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        self.mock_request.db = self.env.cr.dbname
        self.mock_request.session = MagicMock()
        self.mock_request.session.db = self.env.cr.dbname
        self.mock_request.session.uid = self.user.id
        self.mock_request.make_response.side_effect = (
            lambda data, headers=None, cookies=None: Response(data, headers=headers)
        )
        self.request_token = odoo.http.request_var.set(self.mock_request)

    def tearDown(self):
        odoo.http.request_var.reset(self.request_token)
        super().tearDown()

    def _set_request(self, method='GET', data=None, headers=None):
        """Helper to set mock httprequest attributes."""
        self.mock_request.httprequest.method = method
        if data is not None:
            if isinstance(data, (dict, list)):
                self.mock_request.httprequest.data = json.dumps(data)
            else:
                self.mock_request.httprequest.data = data
        else:
            self.mock_request.httprequest.data = ""
        self.mock_request.httprequest.headers = headers or {}

    def _get_response_text(self, res):
        """Extract text from a Response object or string."""
        if isinstance(res, Response):
            return res.get_data(as_text=True)
        return str(res)

    def _get_response_json(self, res):
        """Extract parsed JSON from a Response object or string."""
        text = self._get_response_text(res)
        return json.loads(text)

    # -------------------------------------------------------------------------
    # Tests for auth_api_key
    # -------------------------------------------------------------------------

    def test_01_auth_api_key_valid(self):
        """Test auth_api_key returns True for a valid existing API key."""
        result = self.controller.auth_api_key(self.valid_api_key)
        self.assertIs(result, True, "auth_api_key should return True for valid API key.")

    def test_02_auth_api_key_invalid(self):
        """Test auth_api_key returns error HTML for an invalid API key."""
        result = self.controller.auth_api_key('invalid-non-existent-key')
        self.assertIsInstance(result, str)
        self.assertIn("Invalid <i>API Key</i>", result)

    def test_03_auth_api_key_none(self):
        """Test auth_api_key returns error HTML when API key is None."""
        result_none = self.controller.auth_api_key(None)
        self.assertIsInstance(result_none, str)
        self.assertIn("No <i>API Key</i> Provided", result_none)

    def test_04_auth_api_key_other_user(self):
        """Test auth_api_key returns error HTML when key belongs to another user."""
        other_user = self.env['res.users'].create({
            'name': 'Other API Test User',
            'login': 'other_api_test_user',
            'email': 'other_user@example.com',
        })
        other_key = other_user.generate_api(other_user.login)
        result = self.controller.auth_api_key(other_key, user=self.user)
        self.assertIsInstance(result, str)
        self.assertIn("Invalid <i>API Key</i>", result)

    # -------------------------------------------------------------------------
    # Tests for generate_response validations (No option, No fields)
    # -------------------------------------------------------------------------

    def test_04_generate_response_no_option_for_model(self):
        """Test generate_response when no connection.api record exists for model."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        payload = {'fields': ['id', 'name']}
        self._set_request(method='GET', data=payload)

        res = self.controller.generate_response('GET', self.partner_model.id, 0)
        text = self._get_response_text(res)
        self.assertIn("No Record Created for the model", text)

    def test_05_generate_response_no_fields_selected(self):
        """Test generate_response returns error HTML when fields list is empty."""
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
        })
        payload = {'fields': []}
        self._set_request(method='GET', data=payload)

        res = self.controller.generate_response('GET', self.partner_model.id, 0)
        text = self._get_response_text(res)
        self.assertIn("No fields selected for the model", text)

    # -------------------------------------------------------------------------
    # Tests for generate_response: GET method
    # -------------------------------------------------------------------------

    def test_06_generate_response_get_method_not_allowed(self):
        """Test GET request when is_get is False on connection.api."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': False,
        })
        payload = {'fields': ['id', 'name']}
        self._set_request(method='GET', data=payload)

        res = self.controller.generate_response('GET', self.partner_model.id, 0)
        text = self._get_response_text(res)
        self.assertIn("Method Not Allowed", text)

    def test_07_generate_response_get_single_record(self):
        """Test GET request with a specific rec_id returns that record's data."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
        })
        payload = {'fields': ['id', 'name', 'email']}
        self._set_request(method='GET', data=payload)

        res = self.controller.generate_response('GET', self.partner_model.id, self.test_partner.id)
        self.assertIsInstance(res, Response)
        parsed = self._get_response_json(res)
        records = parsed.get('records', [])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['id'], self.test_partner.id)
        self.assertEqual(records[0]['name'], self.test_partner.name)
        self.assertEqual(records[0]['email'], self.test_partner.email)

    def test_08_generate_response_get_all_records(self):
        """Test GET request with rec_id=0 returns multiple records."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
        })
        payload = {'fields': ['id', 'name']}
        self._set_request(method='GET', data=payload)

        res = self.controller.generate_response('GET', self.partner_model.id, 0)
        self.assertIsInstance(res, Response)
        parsed = self._get_response_json(res)
        records = parsed.get('records', [])
        partner_ids = [r['id'] for r in records]
        self.assertIn(self.test_partner.id, partner_ids)

    def test_09_generate_response_get_datetime_handling(self):
        """Test GET request serializes datetime and date fields to ISO strings."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
        })
        payload = {'fields': ['id', 'name', 'create_date']}
        self._set_request(method='GET', data=payload)

        res = self.controller.generate_response('GET', self.partner_model.id, self.test_partner.id)
        parsed = self._get_response_json(res)
        records = parsed.get('records', [])
        self.assertEqual(len(records), 1)
        # create_date should be formatted as a string (ISO format)
        self.assertIsInstance(records[0]['create_date'], str)

    def test_10_generate_response_get_invalid_fields_error(self):
        """Test GET request with non-existent field raises and returns Invalid JSON Data error."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
        })
        payload = {'fields': ['non_existent_field_xyz']}
        self._set_request(method='GET', data=payload)

        res = self.controller.generate_response('GET', self.partner_model.id, 0)
        text = self._get_response_text(res)
        self.assertIn("Invalid JSON Data", text)

    # -------------------------------------------------------------------------
    # Tests for generate_response: POST method
    # -------------------------------------------------------------------------

    def test_11_generate_response_post_method_not_allowed(self):
        """Test POST request when is_post is False."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_post': False,
        })
        payload = {'values': {'name': 'New Partner'}, 'fields': ['id', 'name']}
        self._set_request(method='POST', data=payload)

        res = self.controller.generate_response('POST', self.partner_model.id, 0)
        text = self._get_response_text(res)
        self.assertIn("Method Not Allowed", text)

    def test_12_generate_response_post_success(self):
        """Test POST request successfully creates a new record and returns it."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_post': True,
        })
        payload = {
            'values': {'name': 'Brand New Created Partner', 'email': 'brand_new@example.com'},
            'fields': ['id', 'name', 'email'],
        }
        self._set_request(method='POST', data=payload)

        res = self.controller.generate_response('POST', self.partner_model.id, 0)
        self.assertIsInstance(res, Response)
        parsed = self._get_response_json(res)
        new_resource = parsed.get('New resource', [])
        self.assertEqual(len(new_resource), 1)
        self.assertEqual(new_resource[0]['name'], 'Brand New Created Partner')
        self.assertEqual(new_resource[0]['email'], 'brand_new@example.com')

        # Verify record exists in database
        created = self.env['res.partner'].browse(new_resource[0]['id'])
        self.assertTrue(created.exists())

    def test_13_generate_response_post_invalid_json(self):
        """Test POST request with invalid values raises catch and returns Invalid JSON Data."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_post': True,
        })
        # Missing 'values' key
        payload = {'fields': ['id', 'name']}
        self._set_request(method='POST', data=payload)

        res = self.controller.generate_response('POST', self.partner_model.id, 0)
        text = self._get_response_text(res)
        self.assertIn("Invalid JSON Data", text)

    # -------------------------------------------------------------------------
    # Tests for generate_response: PUT method
    # -------------------------------------------------------------------------

    def test_14_generate_response_put_method_not_allowed(self):
        """Test PUT request when is_put is False."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_put': False,
        })
        payload = {'values': {'name': 'Updated Name'}, 'fields': ['id', 'name']}
        self._set_request(method='PUT', data=payload)

        res = self.controller.generate_response('PUT', self.partner_model.id, self.test_partner.id)
        text = self._get_response_text(res)
        self.assertIn("Method Not Allowed", text)

    def test_15_generate_response_put_no_id(self):
        """Test PUT request with rec_id=0 returns No ID Provided."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_put': True,
        })
        payload = {'values': {'name': 'Updated Name'}, 'fields': ['id', 'name']}
        self._set_request(method='PUT', data=payload)

        res = self.controller.generate_response('PUT', self.partner_model.id, 0)
        text = self._get_response_text(res)
        self.assertIn("No ID Provided", text)

    def test_16_generate_response_put_resource_not_found(self):
        """Test PUT request with non-existent rec_id returns Resource not found."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_put': True,
        })
        payload = {'values': {'name': 'Updated Name'}, 'fields': ['id', 'name']}
        self._set_request(method='PUT', data=payload)

        res = self.controller.generate_response('PUT', self.partner_model.id, 99999999)
        text = self._get_response_text(res)
        self.assertIn("Resource not found", text)

    def test_17_generate_response_put_success(self):
        """Test PUT request successfully updates existing resource."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_put': True,
        })
        payload = {
            'values': {'name': 'Partner Name Updated Via API'},
            'fields': ['id', 'name'],
        }
        self._set_request(method='PUT', data=payload)

        res = self.controller.generate_response('PUT', self.partner_model.id, self.test_partner.id)
        self.assertIsInstance(res, Response)
        parsed = self._get_response_json(res)
        updated_resource = parsed.get('Updated resource', [])
        self.assertEqual(len(updated_resource), 1)
        self.assertEqual(updated_resource[0]['name'], 'Partner Name Updated Via API')
        self.assertEqual(self.test_partner.name, 'Partner Name Updated Via API')

    def test_18_generate_response_put_invalid_json(self):
        """Test PUT request with corrupted payload returns Invalid JSON Data."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_put': True,
        })
        # Missing 'values' in payload
        payload = {'fields': ['id', 'name']}
        self._set_request(method='PUT', data=payload)

        res = self.controller.generate_response('PUT', self.partner_model.id, self.test_partner.id)
        text = self._get_response_text(res)
        self.assertIn("Invalid JSON Data", text)

    # -------------------------------------------------------------------------
    # Tests for generate_response: DELETE method
    # -------------------------------------------------------------------------

    def test_19_generate_response_delete_method_not_allowed(self):
        """Test DELETE request when is_delete is False."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_delete': False,
        })
        self._set_request(method='DELETE')

        res = self.controller.generate_response(
            'DELETE', self.partner_model.id, self.test_partner.id
        )
        text = self._get_response_text(res)
        self.assertIn("Method Not Allowed", text)

    def test_20_generate_response_delete_no_id(self):
        """Test DELETE request with rec_id=0 returns No ID Provided."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_delete': True,
        })
        self._set_request(method='DELETE')

        res = self.controller.generate_response('DELETE', self.partner_model.id, 0)
        text = self._get_response_text(res)
        self.assertIn("No ID Provided", text)

    def test_21_generate_response_delete_resource_not_found(self):
        """Test DELETE request with non-existent rec_id returns Resource not found."""
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_delete': True,
        })
        self._set_request(method='DELETE')

        res = self.controller.generate_response('DELETE', self.partner_model.id, 99999999)
        text = self._get_response_text(res)
        self.assertIn("Resource not found", text)

    def test_22_generate_response_delete_success(self):
        """Test DELETE request successfully unlinks record."""
        partner_to_delete = self.env['res.partner'].create({'name': 'To Be Deleted Partner'})
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_delete': True,
        })
        self._set_request(method='DELETE')

        res = self.controller.generate_response(
            'DELETE', self.partner_model.id, partner_to_delete.id
        )
        self.assertIsInstance(res, Response)
        parsed = self._get_response_json(res)
        self.assertIn('Resource deleted', parsed)
        self.assertFalse(partner_to_delete.exists(), "Partner should be unlinked.")

    # -------------------------------------------------------------------------
    # Tests for /send_request route handler (fetch_data)
    # -------------------------------------------------------------------------

    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.authenticate')
    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.save_session')
    def test_23_fetch_data_invalid_model(self, _mock_save, mock_auth):
        """Test fetch_data returns error HTML when given model does not exist."""
        mock_auth.return_value = {'uid': self.user.id}
        headers = {
            'api-key': self.valid_api_key,
            'login': self.user.login,
            'password': 'password',
            'db': self.env.cr.dbname,
        }
        self._set_request(method='GET', headers=headers)

        res = self.controller.fetch_data(model='non.existent.model.name')
        text = self._get_response_text(res)
        self.assertIn("Invalid model", text)

    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.authenticate')
    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.save_session')
    def test_24_fetch_data_invalid_api_key(self, _mock_save, mock_auth):
        """Test fetch_data returns error HTML when provided API key is invalid."""
        mock_auth.return_value = {'uid': self.user.id}
        headers = {
            'api-key': 'wrong_api_key_123',
            'login': self.user.login,
            'password': 'password',
            'db': self.env.cr.dbname,
        }
        payload = {'fields': ['id', 'name']}
        self._set_request(method='GET', data=payload, headers=headers)

        res = self.controller.fetch_data(model='res.partner')
        text = self._get_response_text(res)
        self.assertIn("Invalid <i>API Key</i>", text)

    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.authenticate')
    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.save_session')
    def test_25_fetch_data_success(self, _mock_save, mock_auth):
        """Test fetch_data executes successfully when authentication and parameters are valid."""
        mock_auth.return_value = {'uid': self.user.id}
        self.env['connection.api'].search([('model_id', '=', self.partner_model.id)]).unlink()
        self.env['connection.api'].create({
            'model_id': self.partner_model.id,
            'is_get': True,
        })
        headers = {
            'api-key': self.valid_api_key,
            'login': self.user.login,
            'password': 'password',
            'db': self.env.cr.dbname,
        }
        payload = {'fields': ['id', 'name']}
        self._set_request(method='GET', data=payload, headers=headers)

        res = self.controller.fetch_data(model='res.partner', Id=str(self.test_partner.id))
        self.assertIsInstance(res, Response)
        parsed = self._get_response_json(res)
        records = parsed.get('records', [])
        self.assertEqual(records[0]['id'], self.test_partner.id)

    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.authenticate')
    def test_25b_fetch_data_invalid_credentials(self, mock_auth):
        """Test fetch_data returns error HTML when authentication fails."""
        mock_auth.side_effect = Exception("Access Denied: Invalid credentials")
        headers = {
            'login': self.user.login,
            'password': 'wrong_password',
            'db': self.env.cr.dbname,
            'api-key': self.valid_api_key,
        }
        self._set_request(method='GET', headers=headers)

        res = self.controller.fetch_data(model='res.partner')
        text = self._get_response_text(res)
        self.assertIn("wrong login credentials", text)

    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.authenticate')
    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.save_session')
    def test_25c_fetch_data_other_user_api_key(self, _mock_save, mock_auth):
        """Test fetch_data returns Invalid API Key when caller uses another user's key."""
        mock_auth.return_value = {'uid': self.user.id}
        other_user = self.env['res.users'].create({
            'name': 'Second Test User',
            'login': 'second_test_user',
            'email': 'second_test_user@example.com',
        })
        other_key = other_user.generate_api(other_user.login)
        headers = {
            'api-key': other_key,
            'login': self.user.login,
            'password': 'password',
            'db': self.env.cr.dbname,
        }
        payload = {'fields': ['id', 'name']}
        self._set_request(method='GET', data=payload, headers=headers)

        res = self.controller.fetch_data(model='res.partner')
        text = self._get_response_text(res)
        self.assertIn("Invalid <i>API Key</i>", text)

    # -------------------------------------------------------------------------
    # Tests for /odoo_connect route handler (odoo_connect)
    # -------------------------------------------------------------------------

    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.authenticate')
    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.save_session')
    def test_26_odoo_connect_success(self, _mock_save, mock_auth):
        """Test odoo_connect successfully authenticates and returns user's API key."""
        mock_auth.return_value = {'uid': self.user.id}
        headers = {
            'login': self.user.login,
            'password': 'correct_password',
            'db': self.env.cr.dbname,
        }
        self._set_request(method='GET', headers=headers)

        res = self.controller.odoo_connect()
        self.assertIsInstance(res, Response)
        parsed = self._get_response_json(res)
        self.assertEqual(parsed.get('Status'), 'auth successful')
        self.assertEqual(parsed.get('User'), self.user.name)
        self.assertEqual(parsed.get('api-key'), self.valid_api_key)

    @patch('odoo.addons.rest_api_odoo.controllers.rest_api_odoo.authenticate')
    def test_27_odoo_connect_invalid_credentials(self, mock_auth):
        """Test odoo_connect returns error HTML when authentication fails."""
        mock_auth.side_effect = Exception("Access Denied: Invalid credentials")
        headers = {
            'login': self.user.login,
            'password': 'wrong_password',
            'db': self.env.cr.dbname,
        }
        self._set_request(method='GET', headers=headers)

        res = self.controller.odoo_connect()
        text = self._get_response_text(res)
        self.assertIn("wrong login credentials", text)
