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

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleTender(TransactionCase):
    """Test suite covering sale.tender and sale.tender.line models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Tender Customer',
            'email': 'customer@testtender.com',
            'company_id': cls.company.id,
        })
        cls.product_uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Tender Test Product 1',
            'list_price': 150.0,
            'uom_id': cls.product_uom_unit.id,
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Tender Test Product 2',
            'list_price': 250.0,
            'uom_id': cls.product_uom_unit.id,
        })

        cls.tender_type_exclusive = cls.env['sale.tender.type'].create({
            'name': 'Exclusive Agreement',
            'exclusive': 'exclusive',
            'quantity_copy': 'copy',
            'line_copy': 'copy',
        })
        cls.tender_type_multiple = cls.env['sale.tender.type'].create({
            'name': 'Multiple Agreement',
            'exclusive': 'multiple',
            'quantity_copy': 'none',
            'line_copy': 'none',
        })

    def test_tender_creation_and_defaults(self):
        """Test default values on sale tender agreement."""
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.tender_type_exclusive.id,
            'description': '<p>Tender Description</p>',
        })
        self.assertEqual(tender.state, 'draft')
        self.assertEqual(tender.name, 'New')
        self.assertEqual(tender.order_count, 0)
        self.assertEqual(tender.exclusive, 'exclusive')

    def test_tender_action_in_progress_validations(self):
        """Test validation rules when transitioning tender to in_progress."""
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.tender_type_exclusive.id,
        })

        # 1. No product lines
        with self.assertRaises(UserError) as cm:
            tender.action_in_progress()
        self.assertIn("there is no product line", str(cm.exception))

        # 2. Line with unit price <= 0.0
        line_zero_price = self.env['sale.tender.line'].create({
            'tender_id': tender.id,
            'product_id': self.product_1.id,
            'product_qty': 5.0,
            'price_unit': 0.0,
        })
        with self.assertRaises(UserError) as cm:
            tender.action_in_progress()
        self.assertIn("without price", str(cm.exception))

        # 3. Line with quantity <= 0.0
        line_zero_price.price_unit = 100.0
        line_zero_price.product_qty = 0.0
        with self.assertRaises(UserError) as cm:
            tender.action_in_progress()
        self.assertIn("without quantity", str(cm.exception))

        # 4. Successful confirmation
        line_zero_price.product_qty = 10.0
        tender.action_in_progress()
        self.assertEqual(tender.state, 'in_progress')
        self.assertNotEqual(tender.name, 'New')
        self.assertTrue(tender.name.startswith('ST'))

    def test_tender_lifecycle_transitions(self):
        """Test state transitions: open, cancel, reset to draft."""
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.tender_type_multiple.id,
            'line_ids': [Command.create({
                'product_id': self.product_1.id,
                'product_qty': 2.0,
                'price_unit': 80.0,
            })],
        })

        tender.action_in_progress()
        self.assertEqual(tender.state, 'in_progress')

        tender.action_open()
        self.assertEqual(tender.state, 'open')

        tender.action_cancel()
        self.assertEqual(tender.state, 'cancel')

        tender.action_reset_to_draft()
        self.assertEqual(tender.state, 'draft')

    def test_tender_action_done_validation_and_success(self):
        """Test closing tender validates orders are not in draft/sent state."""
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.tender_type_multiple.id,
            'line_ids': [Command.create({
                'product_id': self.product_1.id,
                'product_qty': 5.0,
                'price_unit': 50.0,
            })],
        })
        tender.action_in_progress()

        # Create draft sale order linked to tender
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'tender_id': tender.id,
        })
        self.assertEqual(tender.order_count, 1)

        # Closing tender while an order is in draft must raise UserError
        with self.assertRaises(UserError) as cm:
            tender.action_done()
        self.assertIn(
            "must be either confirmed or canceled", str(cm.exception)
        )

        # Cancel the draft order and close
        so.action_cancel()
        tender.action_done()
        self.assertEqual(tender.state, 'done')

    def test_tender_line_onchange_and_prepare_line(self):
        """Test line onchange, auto UoM, and _prepare_sale_order_line."""
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.tender_type_exclusive.id,
        })

        # Test line creation without explicit product_uom_id
        line = self.env['sale.tender.line'].create({
            'tender_id': tender.id,
            'product_id': self.product_2.id,
            'price_unit': 200.0,
            'product_qty': 4.0,
            'product_description_variants': 'Variant Specific Note',
        })
        self.assertEqual(line.product_uom_id, self.product_2.uom_id)

        # Test onchange_product_id
        line._onchange_product_id()
        self.assertEqual(line.price_unit, self.product_2.list_price)
        self.assertEqual(line.product_qty, 1)

        # Test _prepare_sale_order_line
        line_vals = line._prepare_sale_order_line(
            name="Custom Name",
            product_qty=3.0,
            price_unit=180.0,
            taxes_ids=[1],
        )
        self.assertIn("Custom Name", line_vals['name'])
        self.assertIn("Variant Specific Note", line_vals['name'])
        self.assertEqual(line_vals['product_id'], self.product_2.id)
        self.assertEqual(line_vals['product_uom_qty'], 3.0)
        self.assertEqual(line_vals['price_unit'], 180.0)

    def test_tender_line_create_zero_price_validation(self):
        """Test zero price validation when quantity_copy is 'none'."""
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.tender_type_multiple.id,  # quantity_copy == 'none'
            'line_ids': [Command.create({
                'product_id': self.product_1.id,
                'price_unit': 100.0,
                'product_qty': 1.0,
            })],
        })
        tender.action_in_progress()
        self.assertEqual(tender.state, 'in_progress')

        # Creating line with price_unit <= 0 should raise UserError
        with self.assertRaises(UserError):
            self.env['sale.tender.line'].create({
                'tender_id': tender.id,
                'product_id': self.product_1.id,
                'price_unit': 0.0,
                'product_qty': 1.0,
            })

        # Creating line with positive price should succeed
        line = self.env['sale.tender.line'].create({
            'tender_id': tender.id,
            'product_id': self.product_1.id,
            'price_unit': 50.0,
            'product_qty': 1.0,
        })
        self.assertTrue(line.id)

    def test_sale_tender_type_views_and_action(self):
        """Test validity of sale.tender.type action, views, and menu."""
        action = self.env.ref(
            'tender_management_sales.sale_tender_type_action'
        )
        self.assertEqual(action.res_model, 'sale.tender.type')
        tree_view = self.env.ref(
            'tender_management_sales.view_sale_tender_type_tree'
        )
        self.assertEqual(tree_view.model, 'sale.tender.type')
        form_view = self.env.ref(
            'tender_management_sales.view_sale_tender_type_form'
        )
        self.assertEqual(form_view.model, 'sale.tender.type')
        menu = self.env.ref(
            'tender_management_sales.menu_sale_tender_type'
        )
        self.assertEqual(menu.action.id, action.id)
