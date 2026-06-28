# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, HttpCase, tagged
from odoo.addons.auto_fill.controllers.auto_fill import AutoFill
from unittest.mock import MagicMock, patch
import json

@tagged('post_install', '-at_install')
class TestAutoFillController(TransactionCase):

    def setUp(self):
        super(TestAutoFillController, self).setUp()
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


@tagged('post_install', '-at_install')
class TestAutoFillHttp(HttpCase):

    def setUp(self):
        super(TestAutoFillHttp, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'AutoFillHttpPartnerXYZ',
        })

    def test_matching_records_endpoint(self):
        """Test the actual HTTP jsonrpc endpoint /matching/records"""
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
