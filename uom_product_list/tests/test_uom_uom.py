# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase


class TestUomProductList(TransactionCase):
    """Test cases for UOM Product List."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        cls.uom_unit = cls.env.ref('uom.product_uom_unit')

        # Fix: 'uom_po_id' was removed in Odoo 19 — removed from both creates
        cls.product_1 = cls.env['product.template'].create({
            'name': 'Test Product 1',
            'uom_id': cls.uom_unit.id,
            'list_price': 100.0,
        })

        cls.product_2 = cls.env['product.template'].create({
            'name': 'Test Product 2',
            'uom_id': cls.uom_unit.id,
            'list_price': 150.0,
        })


    def test_compute_product_count(self):
        """Test computed product count in UOM."""
        self.uom_unit.invalidate_recordset()

        expected = self.env['product.template'].search_count(
            [('uom_id', '=', self.uom_unit.id)]
        )

        self.assertEqual(
            self.uom_unit.products_uom,
            expected,
            "products_uom must match the actual count of products using this UOM."
        )

        self.assertGreaterEqual(
            self.uom_unit.products_uom, 2,
            "Count must be at least 2 since we created two test products."
        )


    def test_action_view_products(self):
        """Test smart button action for viewing products."""

        action = self.uom_unit.action_view_products()

        self.assertEqual(
            action['type'],
            'ir.actions.act_window',
            "The action type should be ir.actions.act_window."
        )

        self.assertEqual(
            action['res_model'],
            'product.template',
            "The action model should be product.template."
        )

        self.assertEqual(
            action['view_mode'],
            'kanban,form',
            "The view mode should be kanban,form."
        )
        self.assertEqual(
            action['name'],
            'Products',
            "The action name should be 'Products'."
        )

        self.assertEqual(
            action['domain'],
            [('uom_id', '=', self.uom_unit.id)],
            "The domain should filter products by selected UOM."
        )

        self.assertIn(
            'create',
            str(action.get('context', '')),
            "Context must contain 'create' key to disable record creation."
        )
