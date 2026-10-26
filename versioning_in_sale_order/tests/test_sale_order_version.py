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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaleOrderVersion(TransactionCase):
    """Test suite for Sale Order Versions functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 2,
                'price_unit': 100.0,
            })],
        })

    def test_create_version(self):
        """Test creating a version for a sale order."""
        self.assertEqual(self.sale_order.version_count, 0)
        self.sale_order.action_create_versions()
        self.assertEqual(self.sale_order.version_count, 1)

        version = self.sale_order.version_ids[0]
        self.assertTrue(version.is_version)
        self.assertEqual(version.current_version_id, self.sale_order)
        self.assertEqual(version.origin, self.sale_order.name)
        self.assertEqual(version.state, 'draft')
        self.assertEqual(version.name, f"{self.sale_order.name}-1")

        # Check line note added for the version
        note_line = version.order_line.filtered(lambda l: l.display_type == 'line_note')
        self.assertTrue(note_line)
        self.assertIn("version 1", note_line.name)

    def test_create_multiple_versions(self):
        """Test creating multiple sequential versions."""
        self.sale_order.action_create_versions()
        self.sale_order.action_create_versions()
        self.assertEqual(self.sale_order.version_count, 2)
        version_names = self.sale_order.version_ids.mapped('name')
        self.assertIn(f"{self.sale_order.name}-1", version_names)
        self.assertIn(f"{self.sale_order.name}-2", version_names)

    def test_action_view_versions(self):
        """Test returning the window action for viewing versions."""
        self.sale_order.action_create_versions()
        action = self.sale_order.action_view_versions()
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['view_mode'], 'list,kanban,form')
        self.assertEqual(action['context']['default_current_version_id'], self.sale_order.id)
        self.assertTrue(action['context']['default_is_version'])
        self.assertIn(self.sale_order.version_ids[0].id, action['domain'][0][2])

    def test_confirm_main_order_cancels_versions(self):
        """Test that confirming the main order cancels all active versions."""
        self.sale_order.action_create_versions()
        self.sale_order.action_create_versions()
        v1 = self.sale_order.version_ids.filtered(lambda v: v.name.endswith('-1'))
        v2 = self.sale_order.version_ids.filtered(lambda v: v.name.endswith('-2'))

        # Pre-cancel v2 to cover already-cancelled branch
        v2._action_cancel()
        self.assertEqual(v2.state, 'cancel')

        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.state, 'sale')
        self.assertEqual(v1.state, 'cancel')
        self.assertEqual(v2.state, 'cancel')

    def test_confirm_version_promotes_order(self):
        """Test confirming a version promotes it, demoting parent and handling active & cancelled siblings."""
        original_name = self.sale_order.name
        self.sale_order.action_create_versions()
        self.sale_order.action_create_versions()
        self.sale_order.action_create_versions()

        v1 = self.sale_order.version_ids.filtered(lambda v: v.name.endswith('-1'))
        v2 = self.sale_order.version_ids.filtered(lambda v: v.name.endswith('-2'))
        v3 = self.sale_order.version_ids.filtered(lambda v: v.name.endswith('-3'))

        # Pre-cancel v3 to test sibling when already cancelled
        v3._action_cancel()

        v1_name = v1.name

        # Confirm v1
        v1.action_confirm()

        # v1 is promoted to main order
        self.assertFalse(v1.is_version)
        self.assertFalse(v1.current_version_id)
        self.assertEqual(v1.name, original_name)
        self.assertEqual(v1.state, 'sale')

        # original parent is demoted to a version of v1
        self.assertTrue(self.sale_order.is_version)
        self.assertEqual(self.sale_order.current_version_id, v1)
        self.assertEqual(self.sale_order.name, v1_name)
        self.assertEqual(self.sale_order.state, 'cancel')

        # Active sibling v2 cancelled and re-linked
        self.assertEqual(v2.state, 'cancel')
        self.assertEqual(v2.current_version_id, v1)

        # Cancelled sibling v3 re-linked
        self.assertEqual(v3.state, 'cancel')
        self.assertEqual(v3.current_version_id, v1)
