# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
"""Unit tests for sale_delivery_address module."""
# pylint: disable=protected-access,line-too-long
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'sale_delivery_address')
class TestSaleDeliveryAddress(TransactionCase):
    """Test suite for Multiple Delivery Addresses for Sale Order module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Main Customer',
        })
        cls.delivery_addr_1 = cls.env['res.partner'].create({
            'name': 'Delivery Warehouse North',
            'parent_id': cls.customer.id,
            'type': 'delivery',
            'street': '123 North St',
            'city': 'North City',
            'zip': '12345',
        })
        cls.delivery_addr_2 = cls.env['res.partner'].create({
            'name': 'Delivery Warehouse South',
            'parent_id': cls.customer.id,
            'type': 'delivery',
            'street': '456 South St',
            'city': 'South City',
            'zip': '67890',
        })
        cls.product_goods_1 = cls.env['product.product'].create({
            'name': 'Goods Item 1',
            'type': 'consu',
            'list_price': 100.0,
        })
        cls.product_goods_2 = cls.env['product.product'].create({
            'name': 'Goods Item 2',
            'type': 'consu',
            'list_price': 150.0,
        })
        cls.product_service = cls.env['product.product'].create({
            'name': 'Consulting Service',
            'type': 'service',
            'list_price': 80.0,
        })

    def test_01_is_address_readonly_computation(self):
        """Test is_address_readonly computed field based on product type."""
        order = self.env['sale.order'].create({'partner_id': self.customer.id})
        line_goods = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_goods_1.id,
            'product_uom_qty': 2.0,
        })
        line_service = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_service.id,
            'product_uom_qty': 1.0,
        })

        self.assertFalse(line_goods.is_address_readonly,
                         "Address should not be readonly for goods product.")
        self.assertTrue(line_service.is_address_readonly,
                        "Address should be readonly for service product.")

    def test_02_sale_order_line_delivery_address_assignment(self):
        """Test assigning delivery addresses to sale order lines."""
        order = self.env['sale.order'].create({'partner_id': self.customer.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_goods_1.id,
            'product_uom_qty': 4.0,
            'delivery_addr_id': self.delivery_addr_1.id,
        })
        self.assertEqual(line.delivery_addr_id, self.delivery_addr_1,
                         "Delivery address was not correctly set on order line.")

    def test_03_separate_pickings_created_per_delivery_address(self):
        """Test confirming a sale order with different delivery addresses generates separate transfers."""
        order = self.env['sale.order'].create({'partner_id': self.customer.id})
        line_1 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_goods_1.id,
            'product_uom_qty': 5.0,
            'delivery_addr_id': self.delivery_addr_1.id,
        })
        line_2 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_goods_2.id,
            'product_uom_qty': 3.0,
            'delivery_addr_id': self.delivery_addr_2.id,
        })

        order.action_confirm()

        # Check pickings created
        pickings = order.picking_ids
        self.assertEqual(len(pickings), 2,
                         "Two separate pickings should be generated for two distinct delivery addresses.")

        picking_partners = pickings.mapped('partner_id')
        self.assertIn(self.delivery_addr_1, picking_partners,
                      "Picking for Delivery Address 1 was not created.")
        self.assertIn(self.delivery_addr_2, picking_partners,
                      "Picking for Delivery Address 2 was not created.")

        # Ensure moves correspond to the right pickings
        picking_1 = pickings.filtered(lambda p: p.partner_id == self.delivery_addr_1)
        picking_2 = pickings.filtered(lambda p: p.partner_id == self.delivery_addr_2)
        self.assertEqual(picking_1.move_ids.sale_line_id, line_1)
        self.assertEqual(picking_2.move_ids.sale_line_id, line_2)

    def test_04_default_shipping_address_fallback(self):
        """Test that picking uses order shipping address when line delivery_addr_id is not set."""
        order = self.env['sale.order'].create({'partner_id': self.customer.id})
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_goods_1.id,
            'product_uom_qty': 2.0,
        })

        order.action_confirm()
        self.assertEqual(len(order.picking_ids), 1)
        self.assertEqual(order.picking_ids.partner_id, order.partner_shipping_id)

    def test_05_stock_move_direct_methods(self):
        """Test _get_new_picking_values and _assign_picking edge cases directly."""
        order = self.env['sale.order'].create({'partner_id': self.customer.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_goods_1.id,
            'product_uom_qty': 1.0,
            'delivery_addr_id': self.delivery_addr_1.id,
        })
        order.action_confirm()

        # Test _get_new_picking_values on move
        move_sale = order.picking_ids.move_ids.filtered(lambda m: m.sale_line_id == line)
        self.assertTrue(move_sale)
        picking_vals = move_sale._get_new_picking_values()
        self.assertEqual(picking_vals.get('partner_id'), self.delivery_addr_1.id)

        # Test _assign_picking when sale_moves is empty
        empty_moves = self.env['stock.move']
        self.assertTrue(empty_moves._assign_picking())

        # Test _assign_picking with other_moves (moves without sale_line_id)
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        if picking_type:
            internal_picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            })
            move_internal = self.env['stock.move'].create({
                'product_id': self.product_goods_1.id,
                'product_uom': self.product_goods_1.uom_id.id,
                'product_uom_qty': 1.0,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'picking_id': internal_picking.id,
            })
            self.assertTrue(move_internal._assign_picking())

    def test_06_views_and_templates_rendering(self):
        """Test view inheritance and report / portal template rendering."""
        # 1. Sale order form view
        view = self.env.ref('sale_delivery_address.view_order_form')
        self.assertTrue(view.active)
        self.assertEqual(view.inherit_id, self.env.ref('sale.view_order_form'))
        self.assertIn('delivery_addr_id', view.arch_base)

        # 2. Portal and Report templates
        portal_view = self.env.ref('sale_delivery_address.sale_order_portal_content_inherit')
        self.assertTrue(portal_view.active)
        self.assertEqual(portal_view.inherit_id, self.env.ref('sale.sale_order_portal_content'))

        report_view = self.env.ref('sale_delivery_address.report_saleorder_document_add_delivery_address')
        self.assertTrue(report_view.active)
        self.assertEqual(report_view.inherit_id, self.env.ref('sale.report_saleorder_document'))

        # Render report with an order containing delivery address
        order = self.env['sale.order'].create({'partner_id': self.customer.id})
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_goods_1.id,
            'product_uom_qty': 2.0,
            'delivery_addr_id': self.delivery_addr_1.id,
        })

        rendered_portal = self.env['ir.qweb']._render('sale.sale_order_portal_content', {
            'sale_order': order,
        })
        self.assertIn('Delivery Address', rendered_portal)

        rendered_report = self.env['ir.qweb']._render('sale.report_saleorder_document', {
            'doc': order,
        })
        self.assertIn('Delivery Address', rendered_report)
        self.assertIn('Delivery Warehouse North', rendered_report)

    def test_07_access_rules(self):
        """Verify access rules for sale.order.line and stock.move."""
        group_sale_user = self.env.ref('sales_team.group_sale_salesman')
        group_stock_user = self.env.ref('stock.group_stock_user')

        access_sale = self.env['ir.access'].search([
            ('model_id.model', '=', 'sale.order.line'),
            ('group_id', '=', group_sale_user.id),
        ])
        self.assertTrue(access_sale, "Access rule for sale.order.line must exist.")

        access_stock = self.env['ir.access'].search([
            ('model_id.model', '=', 'stock.move'),
            ('group_id', '=', group_stock_user.id),
        ])
        self.assertTrue(access_stock, "Access rule for stock.move must exist.")
