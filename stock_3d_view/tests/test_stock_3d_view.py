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

from unittest.mock import MagicMock
from odoo import models
from odoo.exceptions import AccessError
from odoo.tests import common, tagged
import odoo.addons.stock_3d_view.controllers.stock_3d_view as ctrl_module
from odoo.addons.stock_3d_view.controllers.stock_3d_view import Stock3DView


@tagged('post_install', '-at_install')
class TestStock3DView(common.TransactionCase):
    """Test suite for Stock 3D View models and controller logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = Stock3DView()
        cls.company = cls.env.company

        # Ensure active user has Inventory User permissions
        stock_group = cls.env.ref('stock.group_stock_user')
        if 'group_ids' in cls.env.user._fields:
            cls.env.user.group_ids |= stock_group
        elif 'groups_id' in cls.env.user._fields:
            cls.env.user.groups_id |= stock_group

        # Find or create warehouse
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.company.id)], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Test Main Warehouse',
                'code': 'TWH',
                'company_id': cls.company.id,
            })

        cls.parent_location = cls.warehouse.lot_stock_id

        # Create test locations with 3D properties
        cls.loc_1 = cls.env['stock.location'].create({
            'name': 'Shelf 01',
            'location_id': cls.parent_location.id,
            'usage': 'internal',
            'company_id': cls.company.id,
            'unique_code': 'TEST-LOC-01',
            'max_capacity': 100,
            'length': 4.0,
            'width': 2.0,
            'height': 1.5,
            'pos_x': 50.0,
            'pos_y': 0.0,
            'pos_z': 30.0,
        })

        cls.loc_2 = cls.env['stock.location'].create({
            'name': 'Shelf 02',
            'location_id': cls.parent_location.id,
            'usage': 'internal',
            'company_id': cls.company.id,
            'unique_code': 'TEST-LOC-02',
            'max_capacity': 50,
            'length': 4.0,
            'width': 2.0,
            'height': 1.5,
            'pos_x': 50.0,
            'pos_y': 24.0,
            'pos_z': 30.0,
        })

        cls.loc_empty = cls.env['stock.location'].create({
            'name': 'Shelf Empty',
            'location_id': cls.parent_location.id,
            'usage': 'internal',
            'company_id': cls.company.id,
            'unique_code': 'TEST-LOC-EMPTY',
            'max_capacity': 80,
            'length': 4.0,
            'width': 2.0,
            'height': 1.5,
            'pos_x': -50.0,
            'pos_y': 0.0,
            'pos_z': 30.0,
        })

        cls.loc_no_capacity = cls.env['stock.location'].create({
            'name': 'Shelf No Cap',
            'location_id': cls.parent_location.id,
            'usage': 'internal',
            'company_id': cls.company.id,
            'unique_code': 'TEST-LOC-NOCAP',
            'max_capacity': 0,
            'length': 4.0,
            'width': 2.0,
            'height': 1.5,
            'pos_x': -50.0,
            'pos_y': 24.0,
            'pos_z': 30.0,
        })

        # Create a storable test product compatible across Odoo versions
        product_vals = {
            'name': 'Test 3D Component',
            'default_code': 'COMP-3D-TEST',
        }
        if 'is_storable' in cls.env['product.product']._fields:
            product_vals['is_storable'] = True
        else:
            product_vals['type'] = 'product'
        cls.product = cls.env['product.product'].create(product_vals)

        # Create stock.quant records
        # loc_1 has 30 units (30% load -> Free Space)
        cls.quant_1 = cls.env['stock.quant'].create({
            'product_id': cls.product.id,
            'location_id': cls.loc_1.id,
            'quantity': 30.0,
        })

        # loc_2 has 65 units (130% load -> Overload)
        cls.quant_2 = cls.env['stock.quant'].create({
            'product_id': cls.product.id,
            'location_id': cls.loc_2.id,
            'quantity': 65.0,
        })

        # loc_no_capacity has 10 units (capacity=0, load=-1)
        cls.quant_nocap = cls.env['stock.quant'].create({
            'product_id': cls.product.id,
            'location_id': cls.loc_no_capacity.id,
            'quantity': 10.0,
        })

    def setUp(self):
        super().setUp()
        # Direct reference swap to avoid Werkzeug LocalProxy inspect in Python 3.12 unittest.mock.patch
        self._orig_request = ctrl_module.request
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        ctrl_module.request = self.mock_request

    def tearDown(self):
        ctrl_module.request = self._orig_request
        super().tearDown()

    def test_01_stock_location_3d_fields(self):
        """Verify 3D dimension, coordinate, and capacity fields on stock.location."""
        self.assertEqual(self.loc_1.length, 4.0)
        self.assertEqual(self.loc_1.width, 2.0)
        self.assertEqual(self.loc_1.height, 1.5)
        self.assertEqual(self.loc_1.pos_x, 50.0)
        self.assertEqual(self.loc_1.pos_y, 0.0)
        self.assertEqual(self.loc_1.pos_z, 30.0)
        self.assertEqual(self.loc_1.unique_code, 'TEST-LOC-01')
        self.assertEqual(self.loc_1.max_capacity, 100)

    def test_02_action_view_location_3d_button(self):
        """Verify the 3D button client action returned from stock.location."""
        action = self.loc_1.action_view_location_3d_button()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'stock_3d_view.open_form_3d_view')
        self.assertEqual(action.get('name'), '3D View')

    def test_03_controller_warehouse_data(self):
        """Verify /3Dstock/warehouse returns active warehouses for company."""
        res = self.controller.get_warehouse_data(self.company.id)
        self.assertIsInstance(res, list)
        warehouse_ids = [wh[0] for wh in res]
        self.assertIn(self.warehouse.id, warehouse_ids)

    def test_04_controller_stock_data(self):
        """Verify /3Dstock/data returns locations with converted dimensions and positions."""
        res = self.controller.get_stock_data(company_id=self.company.id, wh_id=self.warehouse.id)
        self.assertIsInstance(res, dict)
        self.assertIn('TEST-LOC-01', res)

        loc_1_data = res['TEST-LOC-01']
        expected_length = int(self.loc_1.length * 3.779 * 2)
        expected_width = int(self.loc_1.width * 3.779 * 2)
        expected_height = int(self.loc_1.height * 3.779 * 2)

        self.assertEqual(loc_1_data[0], 50.0)             # pos_x
        self.assertEqual(loc_1_data[1], 0.0)              # pos_y
        self.assertEqual(loc_1_data[2], 30.0)             # pos_z
        self.assertEqual(loc_1_data[3], expected_length)  # length
        self.assertEqual(loc_1_data[4], expected_width)   # width
        self.assertEqual(loc_1_data[5], expected_height)  # height
        self.assertEqual(loc_1_data[6], self.loc_1.id)    # loc.id

    def test_05_controller_standalone_stock_data(self):
        """Verify /3Dstock/data/standalone returns warehouse locations including selected loc.id."""
        res = self.controller.get_standalone_stock_data(company_id=self.company.id, loc_id=self.loc_1.id)
        self.assertIsInstance(res, dict)
        self.assertIn('TEST-LOC-01', res)
        self.assertEqual(res['TEST-LOC-01'][6], self.loc_1.id)

    def test_06_controller_stock_count_data(self):
        """Verify /3Dstock/data/quantity load calculation (Free space, Overload, Empty, No-capacity)."""
        # loc_1: 30 units in 100 capacity -> (100, 30) (Free space <= 50%)
        quant_data_1 = self.controller.get_stock_count_data(loc_code='TEST-LOC-01', loc_id=self.loc_1.id)
        self.assertEqual(quant_data_1, (100, 30))

        # loc_2: 65 units in 50 capacity -> (50, 130) (Overload > 100%)
        quant_data_2 = self.controller.get_stock_count_data(loc_code='TEST-LOC-02', loc_id=self.loc_2.id)
        self.assertEqual(quant_data_2, (50, 130))

        # loc_empty: 0 units in 80 capacity -> (80, 0) (Empty)
        quant_data_empty = self.controller.get_stock_count_data(loc_code='TEST-LOC-EMPTY', loc_id=self.loc_empty.id)
        self.assertEqual(quant_data_empty, (80, 0))

        # loc_no_capacity: 10 units in 0 capacity -> (0, -1) (Stock exists without capacity limit)
        quant_data_nocap = self.controller.get_stock_count_data(loc_code='TEST-LOC-NOCAP', loc_id=self.loc_no_capacity.id)
        self.assertEqual(quant_data_nocap, (0, -1))

    def test_07_controller_stock_product_data(self):
        """Verify /3Dstock/data/product product list, total capacity, and remaining space."""
        # loc_1 product details
        prod_data = self.controller.get_stock_product_data(loc_code='TEST-LOC-01', loc_id=self.loc_1.id)
        self.assertIsInstance(prod_data, dict)
        self.assertEqual(prod_data.get('capacity'), 100)
        self.assertEqual(prod_data.get('space'), 70.0)    # 100 - 30 = 70
        self.assertEqual(len(prod_data.get('product_list')), 1)
        self.assertEqual(prod_data['product_list'][0], (self.product.display_name, 30.0))

        # Empty location product details
        empty_data = self.controller.get_stock_product_data(loc_code='TEST-LOC-EMPTY', loc_id=self.loc_empty.id)
        self.assertEqual(empty_data.get('capacity'), 80)
        self.assertEqual(empty_data.get('space'), 80.0)
        self.assertEqual(len(empty_data.get('product_list')), 0)

    def test_08_access_denied_without_stock_user(self):
        """Verify access is denied for a user lacking stock.group_stock_user."""
        groups_field = 'group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'
        non_stock_user = self.env['res.users'].create({
            'name': 'Non Stock User',
            'login': 'non_stock_user_test',
            'email': 'non_stock_user_test@test.com',
            groups_field: [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.mock_request.env = self.env(user=non_stock_user)
        with self.assertRaises(AccessError):
            self.controller.get_warehouse_data(self.company.id)
        with self.assertRaises(AccessError):
            self.controller.get_stock_data(self.company.id, self.warehouse.id)
        with self.assertRaises(AccessError):
            self.controller.get_stock_count_data(loc_id=self.loc_1.id)
        with self.assertRaises(AccessError):
            self.controller.get_stock_product_data(loc_id=self.loc_1.id)
        with self.assertRaises(AccessError):
            self.controller.get_standalone_stock_data(self.company.id, self.loc_1.id)

    def test_09_unique_code_constraint_registration(self):
        """Verify _unique_code constraint is an instance of models.Constraint, not a tuple."""
        constraint = getattr(self.env['stock.location'].__class__, '_unique_code', None)
        self.assertIsInstance(constraint, models.Constraint)
