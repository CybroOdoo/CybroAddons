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
#############################################################################
"""Unit tests for models extended by website_multi_product_return_management."""
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRelatedModels(TransactionCase):
    """Test cases for sale.order, res.partner, and stock.picking extensions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_partner = cls.env['res.partner'].create({
            'name': 'Corporate Client Inc.',
            'is_company': True,
            'vat': 'US123456789',
            'email': 'corp@client.com',
        })
        cls.individual_partner = cls.env['res.partner'].create({
            'name': 'John Doe',
            'is_company': False,
            'parent_id': cls.company_partner.id,
            'email': 'john@client.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Sample Returnable Item',
            'type': 'consu',
            'list_price': 150.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.company_partner.id,
            'order_line': [
                Command.create({
                    'product_id': cls.product.id,
                    'product_uom_qty': 4,
                    'price_unit': 150.0,
                }),
            ],
        })
        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.env.company.id)
        ], limit=1)
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.stock_location = cls.warehouse.lot_stock_id

    def test_01_sale_order_return_order_count(self):
        """Test calculation of return_order_count on sale.order."""
        self.assertEqual(self.sale_order.return_order_count, 0)

        # Create return order for this sale order
        return_order_1 = self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.company_partner.id,
        })
        self.sale_order._compute_return_order_count()
        self.assertEqual(self.sale_order.return_order_count, 1)

        # Create second return order
        self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.company_partner.id,
        })
        self.sale_order._compute_return_order_count()
        self.assertEqual(self.sale_order.return_order_count, 2)

    def test_02_sale_order_action_open_returns(self):
        """Test action_open_returns returns expected action and domain for sale.order."""
        action = self.sale_order.action_open_returns()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'sale.return')
        self.assertEqual(action.get('domain'), [('sale_order_id', '=', self.sale_order.id)])
        self.assertEqual(action.get('context', {}).get('search_default_order'), 1)

    def test_03_sale_order_line_return_order_line_count(self):
        """Test return_order_line_count field on sale.order.line."""
        line = self.sale_order.order_line[0]
        self.assertEqual(line.return_order_line_count, 0)
        line.return_order_line_count = 3
        self.assertEqual(line.return_order_line_count, 3)

    def test_04_partner_return_order_count_and_hierarchy(self):
        """Test calculation of return_order_count on res.partner including child contacts."""
        self.assertEqual(self.company_partner.return_order_count, 0)
        self.assertEqual(self.individual_partner.return_order_count, 0)

        # 1. Return order directly for company partner
        self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.company_partner.id,
        })
        self.company_partner._compute_return_order_count()
        self.individual_partner._compute_return_order_count()
        self.assertEqual(self.company_partner.return_order_count, 1)
        self.assertEqual(self.individual_partner.return_order_count, 0)

        # 2. Return order for individual child partner
        child_so = self.env['sale.order'].create({
            'partner_id': self.individual_partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.env['sale.return'].create({
            'sale_order_id': child_so.id,
            'partner_id': self.individual_partner.id,
        })
        self.company_partner._compute_return_order_count()
        self.individual_partner._compute_return_order_count()
        # Company partner includes child returns (child_of)
        self.assertEqual(self.company_partner.return_order_count, 2)
        self.assertEqual(self.individual_partner.return_order_count, 1)

    def test_05_partner_action_open_returns(self):
        """Test action_open_returns for both individual and company partners."""
        # Individual partner
        individual_action = self.individual_partner.action_open_returns()
        self.assertEqual(individual_action.get('type'), 'ir.actions.act_window')
        self.assertEqual(individual_action.get('res_model'), 'sale.return')
        self.assertEqual(
            individual_action.get('domain'),
            [('partner_id.id', '=', self.individual_partner.id)],
        )
        self.assertEqual(individual_action.get('context', {}).get('search_default_customer'), 1)

        # Company partner
        company_action = self.company_partner.action_open_returns()
        self.assertEqual(
            company_action.get('domain'),
            [('partner_id.commercial_partner_id.id', '=', self.company_partner.id)],
        )

    def test_06_stock_picking_button_validate_return_completion(self):
        """Test button_validate updates return order state to done when all pickings are done."""
        return_order = self.env['sale.return'].create({
            'sale_order_id': self.sale_order.id,
            'partner_id': self.company_partner.id,
            'state': 'confirm',
        })

        # Create two return pickings
        picking_1 = self.env['stock.picking'].create({
            'partner_id': self.company_partner.id,
            'picking_type_id': self.warehouse.in_type_id.id,
            'location_id': self.customer_location.id,
            'location_dest_id': self.stock_location.id,
            'return_order_pick_id': return_order.id,
            'return_order_picking': True,
            'move_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'location_id': self.customer_location.id,
                    'location_dest_id': self.stock_location.id,
                }),
            ],
        })
        picking_2 = self.env['stock.picking'].create({
            'partner_id': self.company_partner.id,
            'picking_type_id': self.warehouse.in_type_id.id,
            'location_id': self.customer_location.id,
            'location_dest_id': self.stock_location.id,
            'return_order_pick_id': return_order.id,
            'return_order_picking': True,
            'move_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'location_id': self.customer_location.id,
                    'location_dest_id': self.stock_location.id,
                }),
            ],
        })

        picking_1.action_confirm()
        picking_1.action_assign()
        picking_1.move_ids[0].quantity = 1
        picking_1.move_ids[0].picked = True
        picking_1.button_validate()

        # picking_2 is still pending, so return order should remain in 'confirm'
        self.assertEqual(return_order.state, 'confirm', "Return order must not be marked 'done' while other pickings are pending")

        # Validate picking_2
        picking_2.action_confirm()
        picking_2.action_assign()
        picking_2.move_ids[0].quantity = 1
        picking_2.move_ids[0].picked = True
        picking_2.button_validate()

        self.assertEqual(return_order.state, 'done', "Return order must be marked 'done' once all pickings are completed")

    def test_07_stock_picking_button_validate_standard_picking(self):
        """Test button_validate behaves normally for pickings without return order reference."""
        standard_picking = self.env['stock.picking'].create({
            'partner_id': self.company_partner.id,
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'move_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'location_id': self.stock_location.id,
                    'location_dest_id': self.customer_location.id,
                }),
            ],
        })
        standard_picking.action_confirm()
        standard_picking.action_assign()
        standard_picking.move_ids[0].quantity = 1
        standard_picking.move_ids[0].picked = True
        res = standard_picking.button_validate()
        self.assertEqual(standard_picking.state, 'done')
        self.assertFalse(standard_picking.return_order_pick_id)
