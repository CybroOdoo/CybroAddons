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
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductSalesByLocation(TransactionCase):
    """Test suite covering model constraints, stock rule propagation, and templates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.product_a = cls.env['product.product'].create({
            'name': 'Test Storable Product A',
            'type': 'consu',
            'is_storable': True,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Test Storable Product B',
            'type': 'consu',
            'is_storable': True,
        })

        warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.stock_location = warehouse.lot_stock_id

        cls.custom_location_1 = cls.env['stock.location'].create({
            'name': 'Shelf 1',
            'usage': 'internal',
            'location_id': cls.stock_location.id,
        })
        cls.custom_location_2 = cls.env['stock.location'].create({
            'name': 'Shelf 2',
            'usage': 'internal',
            'location_id': cls.stock_location.id,
        })

    def test_sale_order_line_location_assignment(self):
        """Verify that line_location_id is correctly assigned to sale order lines."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2.0,
                    'line_location_id': self.custom_location_1.id,
                }),
            ],
        })
        self.assertEqual(order.order_line.line_location_id, self.custom_location_1)

    def test_duplicate_product_same_location_raises_validation_error(self):
        """Verify that adding the same product with the same location raises a ValidationError."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'line_location_id': self.custom_location_1.id,
                }),
            ],
        })
        with self.assertRaises(ValidationError):
            order.write({
                'order_line': [
                    Command.create({
                        'product_id': self.product_a.id,
                        'product_uom_qty': 3.0,
                        'line_location_id': self.custom_location_1.id,
                    }),
                ],
            })

    def test_duplicate_product_different_locations_allowed(self):
        """Verify that adding the same product with different locations is permitted."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                    'line_location_id': self.custom_location_1.id,
                }),
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2.0,
                    'line_location_id': self.custom_location_2.id,
                }),
            ],
        })
        self.assertEqual(len(order.order_line), 2)

    def test_duplicate_product_without_location_allowed(self):
        """Verify that multiple lines of the same product without specific locations are permitted."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1.0,
                }),
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2.0,
                }),
            ],
        })
        self.assertEqual(len(order.order_line), 2)

    def test_stock_rule_get_stock_move_values(self):
        """Verify that stock.rule._get_stock_move_values applies line_location_id."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 5.0,
                    'line_location_id': self.custom_location_1.id,
                }),
            ],
        })
        line = order.order_line
        rule = self.env['stock.rule'].search([
            ('action', '=', 'pull'),
            ('picking_type_id', '!=', False),
            ('location_src_id', '!=', False),
        ], limit=1)
        if not rule:
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
            rule = self.env['stock.rule'].create({
                'name': 'Test Rule',
                'action': 'pull',
                'picking_type_id': warehouse.out_type_id.id,
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.partner.property_stock_customer.id,
            })

        values = {
            'sale_line_id': line.id,
            'date_planned': order.date_order,
        }
        res = rule._get_stock_move_values(
            self.product_a, 5.0, self.product_a.uom_id,
            self.partner.property_stock_customer, 'Test Move', order.name,
            self.env.company, values,
        )
        self.assertEqual(res.get('location_id'), self.custom_location_1.id)

    def test_sale_order_confirmation_creates_move_with_location(self):
        """Verify that confirming a sale order assigns line_location_id to generated stock moves."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2.0,
                    'line_location_id': self.custom_location_1.id,
                }),
            ],
        })
        order.action_confirm()
        self.assertTrue(order.picking_ids)
        move = order.picking_ids.move_ids.filtered(lambda m: m.product_id == self.product_a)
        self.assertTrue(move)
        self.assertEqual(move.location_id, self.custom_location_1)

    def test_report_and_portal_templates_rendering(self):
        """Verify that portal and report templates render without error when locations are present."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2.0,
                    'line_location_id': self.custom_location_1.id,
                }),
            ],
        })
        report = self.env['ir.actions.report']._get_report_from_name('sale.report_saleorder')
        html_content = report._render_qweb_html('sale.report_saleorder', [order.id])[0]
        self.assertIn(b'Shelf 1', html_content)

        portal_html = self.env['ir.qweb']._render(
            'sale.sale_order_portal_content',
            {
                'sale_order': order,
                'object': order,
                'lines_to_report': order.order_line,
                'report_type': 'html',
            },
        )
        self.assertIn('Shelf 1', portal_html)
