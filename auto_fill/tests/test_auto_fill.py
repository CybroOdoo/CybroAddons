# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
import json
from odoo.tests.common import TransactionCase, HttpCase, tagged
from odoo.addons.auto_fill.controllers.auto_fill import AutoFill


@tagged('post_install', '-at_install')
class TestAutoFillController(TransactionCase):

    def setUp(self):
        super().setUp()
        self.controller = AutoFill()
        # Create a test partner to ensure we have data
        self.partner = self.env['res.partner'].create({
            'name': 'AutoFillTestingPartnerNameXYZ',
        })
        self.env.flush_all()

    def test_get_matching_records_empty_value(self):
        """Test with empty search value, should return empty list"""
        mock_request = MagicMock()
        mock_request.cr = self.env.cr
        with patch('odoo.addons.auto_fill.controllers.auto_fill.request', mock_request):
            res = self.controller.get_matching_records(
                model='res.partner',
                field='name',
                value=''
            )
            self.assertEqual(res, [])

    def test_get_matching_records_with_matches(self):
        """Test with valid search value that matches our partner"""
        mock_request = MagicMock()
        mock_request.cr = self.env.cr
        with patch('odoo.addons.auto_fill.controllers.auto_fill.request', mock_request):
            res = self.controller.get_matching_records(
                model='res.partner',
                field='name',
                value='AutoFillTestingPartnerName'
            )
            self.assertTrue(len(res) > 0, "Should return at least one record")
            names = [r[0] for r in res]
            self.assertIn('AutoFillTestingPartnerNameXYZ', names)

    def test_get_matching_records_no_matches(self):
        """Test with valid search value that does not match any record"""
        mock_request = MagicMock()
        mock_request.cr = self.env.cr
        with patch('odoo.addons.auto_fill.controllers.auto_fill.request', mock_request):
            res = self.controller.get_matching_records(
                model='res.partner',
                field='name',
                value='NonExistentPartnerNameXYZabc'
            )
            names = [r[0] for r in res]
            self.assertNotIn('AutoFillTestingPartnerNameXYZ', names)

    def test_sql_injection_attempts(self):
        """Verify that SQL injection attempts in value, field, or model are safely neutralized"""
        mock_request = MagicMock()
        mock_request.cr = self.env.cr
        mock_request.env = self.env
        with patch('odoo.addons.auto_fill.controllers.auto_fill.request', mock_request):
            # Injection in value
            res_val = self.controller.get_matching_records(
                model='res.partner',
                field='name',
                value="' OR 1=1 --"
            )
            self.assertEqual(res_val, [], "SQL injection in value should not return all records")

            # Injection in field
            res_field = self.controller.get_matching_records(
                model='res.partner',
                field="name; DROP TABLE res_partner; --",
                value='AutoFill'
            )
            self.assertEqual(res_field, [], "SQL injection in field name should be rejected")

            # Injection in model
            res_model = self.controller.get_matching_records(
                model="res.partner; DROP TABLE res_partner; --",
                field='name',
                value='AutoFill'
            )
            self.assertEqual(res_model, [], "SQL injection in model name should be rejected")

            # Access to sensitive field
            res_sensitive = self.controller.get_matching_records(
                model='res.users',
                field='password',
                value='admin'
            )
            self.assertEqual(
                res_sensitive, [],
                "Access to sensitive fields like password should be blocked"
            )


@tagged('post_install', '-at_install')
class TestAutoFillHttp(HttpCase):

    def setUp(self):
        super().setUp()
        admin_user = self.env.ref('base.user_admin')
        admin_user.password = 'admin'
        self.partner = self.env['res.partner'].create({
            'name': 'AutoFillHttpPartnerXYZ',
        })

    def test_matching_records_endpoint_unauthenticated(self):
        """Pre-authentication requests must be blocked/rejected"""
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "res.partner",
                "field": "name",
                "value": "AutoFillHttpPartner"
            }
        }
        response = self.url_open(
            '/matching/records',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        res_json = response.json()
        # Since auth='user', unauthenticated calls should have an error
        # (e.g. SessionExpiredException / AccessDenied)
        self.assertTrue(
            'error' in res_json or response.status_code in (401, 403, 404, 303),
            "Unauthenticated pre-auth request must be rejected"
        )

    def test_matching_records_endpoint_authenticated(self):
        """Authenticated requests should work as expected"""
        self.authenticate('admin', 'admin')
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": "res.partner",
                "field": "name",
                "value": "AutoFillHttpPartner"
            }
        }

        response = self.url_open(
            '/matching/records',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertIn('result', res_json, "Response should contain 'result' key")

        result_data = res_json['result']
        names = [r[0] for r in result_data]
        self.assertIn('AutoFillHttpPartnerXYZ', names, "Should find the created partner")
