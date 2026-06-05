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
from psycopg2 import IntegrityError
from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import mute_logger


@tagged('post_install', '-at_install')
class TestStockLocation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockLocation, cls).setUpClass()
        cls.warehouse_loc = cls.env.ref('stock.stock_location_stock')

    def test_stock_location_custom_fields(self):
        """Test creating a stock.location with custom 3D dimension and coordinate fields"""
        location = self.env['stock.location'].create({
            'name': 'Test 3D Location A',
            'location_id': self.warehouse_loc.id,
            'length': 10.0,
            'width': 5.0,
            'height': 3.0,
            'pos_x': 100.0,
            'pos_y': 150.0,
            'pos_z': 200.0,
            'unique_code': 'LOC_3D_TEST_A',
            'max_capacity': 100,
        })
        
        self.assertTrue(location.exists())
        self.assertEqual(location.length, 10.0)
        self.assertEqual(location.width, 5.0)
        self.assertEqual(location.height, 3.0)
        self.assertEqual(location.pos_x, 100.0)
        self.assertEqual(location.pos_y, 150.0)
        self.assertEqual(location.pos_z, 200.0)
        self.assertEqual(location.unique_code, 'LOC_3D_TEST_A')
        self.assertEqual(location.max_capacity, 100)

    @mute_logger('odoo.sql_db')
    def test_stock_location_unique_code_constraint(self):
        """Test that unique_code SQL constraint prevents duplicate codes"""
        self.env['stock.location'].create({
            'name': 'Location 1',
            'location_id': self.warehouse_loc.id,
            'unique_code': 'DUPLICATE_CODE',
        })
        
        with self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.env['stock.location'].create({
                    'name': 'Location 2',
                    'location_id': self.warehouse_loc.id,
                    'unique_code': 'DUPLICATE_CODE',
                })

    def test_action_view_location_3d_button(self):
        """Test that action_view_location_3d_button returns correct client action tag"""
        location = self.env['stock.location'].create({
            'name': 'Test 3D Location B',
            'location_id': self.warehouse_loc.id,
            'unique_code': 'LOC_3D_TEST_B',
        })
        
        res = location.action_view_location_3d_button()
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'stock_3d_view.open_form_3d_view')
