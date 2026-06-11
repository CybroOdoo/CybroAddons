# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import HttpCase, tagged

@tagged('post_install', '-at_install')
class TestStock3DView(HttpCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        
        # create warehouse and location
        self.warehouse = self.env['stock.warehouse'].create({
            'name': 'Test 3D Warehouse',
            'code': 'T3D',
            'company_id': self.company.id,
        })
        self.location = self.env['stock.location'].create({
            'name': 'Test 3D Location',
            'usage': 'internal',
            'company_id': self.company.id,
            'location_id': self.warehouse.view_location_id.id,
            'max_capacity': 100,
            'length': 10.0,
            'width': 10.0,
            'height': 10.0,
            'pos_x': 0.0,
            'pos_y': 0.0,
            'pos_z': 0.0,
            'unique_code': 'LOC3D-TEST',
        })
        
        # create product and quant
        self.product = self.env['product.product'].create({
            'name': 'Test 3D Product',
            'type': 'product',
        })
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.location.id,
            'quantity': 25,
        })

        # create test user
        self.test_user = self.env['res.users'].create({
            'name': 'Test 3D User',
            'login': 'test_3d_user',
            'password': 'test_password',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('stock.group_stock_user').id])],
        })

    def test_01_get_warehouse_data(self):
        self.authenticate('test_3d_user', 'test_password')
        response = self.make_jsonrpc_request('/3Dstock/warehouse', {'company_id': self.company.id})
        self.assertTrue(any(wh[0] == self.warehouse.id for wh in response))

    def test_02_get_stock_data(self):
        self.authenticate('test_3d_user', 'test_password')
        response = self.make_jsonrpc_request('/3Dstock/data', {'company_id': self.company.id, 'wh_id': self.warehouse.id})
        self.assertIn('LOC3D-TEST', response)
        # Check dimension calculation (10 * 3.779 * 2) = 75
        self.assertEqual(response['LOC3D-TEST'][3], int(10 * 3.779 * 2))

    def test_03_get_stock_count_data(self):
        self.authenticate('test_3d_user', 'test_password')
        response = self.make_jsonrpc_request('/3Dstock/data/quantity', {'loc_code': 'LOC3D-TEST'})
        # Capacity is 100, qty is 25. Load % is 25
        self.assertEqual(response[0], 100)
        self.assertEqual(response[1], 25)

    def test_04_get_stock_product_data(self):
        self.authenticate('test_3d_user', 'test_password')
        response = self.make_jsonrpc_request('/3Dstock/data/product', {'loc_code': 'LOC3D-TEST'})
        self.assertEqual(response['capacity'], 100)
        self.assertEqual(response['space'], 75)
        self.assertTrue(any(p[0] == self.product.display_name and p[1] == 25 for p in response['product_list']))

    def test_05_get_standalone_stock_data(self):
        self.authenticate('test_3d_user', 'test_password')
        response = self.make_jsonrpc_request('/3Dstock/data/standalone', {'company_id': self.company.id, 'loc_id': self.location.id})
        self.assertIn('LOC3D-TEST', response)
        self.assertEqual(response['LOC3D-TEST'][6], self.location.id)

    def test_06_action_view_location_3d_button(self):
        action = self.location.action_view_location_3d_button()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'stock_3d_view.open_form_3d_view')
