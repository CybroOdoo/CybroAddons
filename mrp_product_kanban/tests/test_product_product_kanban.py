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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestProductProductKanban(common.TransactionCase):
    """Test suite for Manufacturing Product Kanban module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test MRP Product',
            'is_storable': True,
        })
        cls.component = cls.env['product.product'].create({
            'name': 'Test Component',
            'is_storable': True,
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': cls.component.id,
                    'product_qty': 2.0,
                })
            ],
        })
        cls.production = cls.env['mrp.production'].create({
            'product_id': cls.product.id,
            'product_qty': 1.0,
            'bom_id': cls.bom.id,
        })
        cls.workcenter = cls.env['mrp.workcenter'].create({
            'name': 'Test Assembly Workcenter',
        })
        cls.workorder = cls.env['mrp.workorder'].create({
            'name': 'Assemble Test Product',
            'production_id': cls.production.id,
            'workcenter_id': cls.workcenter.id,
            'product_id': cls.product.id,
        })
        cls.empty_product = cls.env['product.product'].create({
            'name': 'Empty Product without Orders',
            'is_storable': True,
        })

    def test_compute_counts_with_records(self):
        """Test compute methods for mrp_count, work_count, and bom_count with data."""
        self.product._compute_mrp_count()
        self.product._compute_work_count()
        self.product._compute_bom_count()
        self.assertEqual(self.product.mrp_count, 1)
        self.assertEqual(self.product.work_count, 1)
        self.assertEqual(self.product.bom_count, 1)

    def test_compute_counts_empty_product(self):
        """Test compute methods when product has no associated manufacturing records."""
        self.empty_product._compute_mrp_count()
        self.empty_product._compute_work_count()
        self.empty_product._compute_bom_count()
        self.assertEqual(self.empty_product.mrp_count, 0)
        self.assertEqual(self.empty_product.work_count, 0)
        self.assertEqual(self.empty_product.bom_count, 0)

    def test_action_mrp_orders(self):
        """Test action_mrp_orders returns expected action dictionary."""
        action = self.product.action_mrp_orders()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'mrp.production')
        self.assertEqual(action.get('domain'), [('product_id', '=', self.product.id)])
        self.assertEqual(action.get('context'), {'create': False})

    def test_action_work_orders(self):
        """Test action_work_orders returns expected action dictionary."""
        action = self.product.action_work_orders()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'mrp.workorder')
        self.assertEqual(action.get('domain'), [('product_id', '=', self.product.id)])
        self.assertEqual(action.get('context'), {'create': False})

    def test_action_un_build_orders(self):
        """Test action_un_build_orders returns expected action dictionary."""
        action = self.product.action_un_build_orders()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'mrp.unbuild')
        self.assertEqual(action.get('domain'), [('product_id', '=', self.product.id)])
        self.assertEqual(action.get('context'), {'create': False})

    def test_action_scrap_orders(self):
        """Test action_scrap_orders returns expected scrap action dictionary."""
        action = self.product.action_scrap_orders()
        self.assertEqual(action.get('name'), 'Scrap Orders')
        self.assertIn(('product_id', '=', self.product.id), action.get('domain'))
        self.assertEqual(action['context'].get('default_product_id'), self.product.id)
        self.assertFalse(action['context'].get('create'))

    def test_action_bom(self):
        """Test action_bom returns expected BOM action dictionary."""
        action = self.product.action_bom()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'mrp.bom')
        self.assertEqual(
            action.get('domain'),
            [('product_tmpl_id', '=', self.product.product_tmpl_id.id)],
        )
        self.assertEqual(action.get('context'), {'create': False})

    def test_actions_ensure_one(self):
        """Test that action methods raise an exception when called on multiple records."""
        multi_products = self.product | self.empty_product
        with self.assertRaises(ValueError):
            multi_products.action_mrp_orders()
        with self.assertRaises(ValueError):
            multi_products.action_work_orders()
        with self.assertRaises(ValueError):
            multi_products.action_un_build_orders()
        with self.assertRaises(ValueError):
            multi_products.action_scrap_orders()
        with self.assertRaises(ValueError):
            multi_products.action_bom()
