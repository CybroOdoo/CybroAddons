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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import json

from odoo.tests.common import HttpCase


class TestControllers(HttpCase):
    def setUp(self):
        super().setUp()
        self.authenticate(self.env.ref('base.user_admin').login, 'admin')

    def test_json_routes(self):
        # Test a couple of public json routes
        # Note: We just verify they don't crash and return expected structures
        
        # /get_operation_types
        res = self.make_jsonrpc_request('/get_operation_types', {})
        self.assertTrue(isinstance(res, list)) # returns multiple dicts
        
        # /get_the_top_products
        res = self.make_jsonrpc_request('/get_the_top_products', {})
        self.assertIn('products', res)
        self.assertIn('count', res)

        # /get_stock_moves
        res = self.make_jsonrpc_request('/get_stock_moves', {})
        self.assertIn('name', res)
        self.assertIn('count', res)

        # /get_product_moves
        res = self.make_jsonrpc_request('/get_product_moves', {})
        self.assertTrue(isinstance(res, list))

        # /get_product_category
        res = self.make_jsonrpc_request('/get_product_category', {})
        self.assertIn('name', res)
        self.assertIn('count', res)

        # /get_locations
        res = self.make_jsonrpc_request('/get_locations', {})
        self.assertTrue(isinstance(res, dict))

    def make_jsonrpc_request(self, route, params):
        url = self.env['ir.config_parameter'].sudo().get_str('web.base.url') + route
        res = self.url_open(
            url,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': params, 'id': 1}),
            headers={'Content-Type': 'application/json'}
        )
        return res.json().get('result')
