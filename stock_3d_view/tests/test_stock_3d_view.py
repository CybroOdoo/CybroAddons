# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import odoo.tests
from odoo.tests.common import HttpCase
from odoo.tools.json import scriptsafe as json_safe


@odoo.tests.tagged('post_install', '-at_install')
class TestStock3DViewController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super(TestStock3DViewController, cls).setUpClass()
        
        cls.company = cls.env.company
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Warehouse 3D',
            'code': 'WH3D',
            'company_id': cls.company.id,
        })
        
        cls.location = cls.env['stock.location'].create({
            'name': 'Bin 3D A',
            'location_id': cls.warehouse.lot_stock_id.id,
            'usage': 'internal',
            'length': 2.0,
            'width': 2.0,
            'height': 2.0,
            'pos_x': 10.0,
            'pos_y': 20.0,
            'pos_z': 30.0,
            'unique_code': 'UNIQUE_3D_CODE_A',
            'max_capacity': 50,
            'company_id': cls.company.id,
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Test Product 3D',
            'type': 'consu',
            'is_storable': True,
        })
        cls.env['stock.quant']._update_available_quantity(cls.product, cls.location, 10.0)

    def _jsonrpc(self, route, params=None):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 0,
            "params": params or {},
        }
        return self.url_open(
            route,
            headers={"Content-Type": "application/json"},
            data=json_safe.dumps(payload),
        ).json()

    def test_get_warehouse_data(self):
        """Test get_warehouse_data returns warehouses filtered by company"""
        res = self._jsonrpc('/3Dstock/warehouse', {'company_id': self.company.id})
        self.assertNotIn('error', res)
        warehouse_ids = [w[0] for w in res['result']]
        self.assertIn(self.warehouse.id, warehouse_ids)

    def test_get_stock_data(self):
        """Test get_stock_data returns dictionary of locations with dimensions and positions"""
        res = self._jsonrpc('/3Dstock/data', {'company_id': self.company.id, 'wh_id': self.warehouse.id})
        self.assertNotIn('error', res)
        data = res['result']
        self.assertIn('UNIQUE_3D_CODE_A', data)
        expected_dimensions = [10.0, 20.0, 30.0, 15, 15, 15]
        self.assertEqual(data['UNIQUE_3D_CODE_A'], expected_dimensions)

    def test_get_stock_count_data(self):
        """Test get_stock_count_data returns correct capacity and computed stock load percent"""
        res = self._jsonrpc('/3Dstock/data/quantity', {'loc_code': 'UNIQUE_3D_CODE_A'})
        self.assertNotIn('error', res)
        self.assertEqual(tuple(res['result']), (50, 20))

    def test_get_stock_product_data(self):
        """Test get_stock_product_data returns correct product details and remaining space"""
        res = self._jsonrpc('/3Dstock/data/product', {'loc_code': 'UNIQUE_3D_CODE_A'})
        self.assertNotIn('error', res)
        data = res['result']
        self.assertEqual(data['capacity'], 50)
        self.assertEqual(data['space'], 40.0)  # 50 - 10.0
        self.assertIn((self.product.display_name, 10.0), [tuple(x) for x in data['product_list']])

    def test_get_standalone_stock_data(self):
        """Test get_standalone_stock_data returns coordinates and dimensions for standalone location"""
        res = self._jsonrpc('/3Dstock/data/standalone', {'company_id': self.company.id, 'loc_id': self.location.id})
        self.assertNotIn('error', res)
        data = res['result']
        self.assertIn('UNIQUE_3D_CODE_A', data)
        self.assertEqual(data['UNIQUE_3D_CODE_A'][-1], self.location.id)
