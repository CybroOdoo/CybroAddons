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

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderTender(TransactionCase):
    """Test suite covering SaleOrder, SaleOrderGroup, and SaleOrderLine tender logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'SO Test Partner',
            'company_id': cls.company.id,
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Alternative Partner 2',
            'company_id': cls.company.id,
        })

        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.uom_dozen = cls.env.ref('uom.product_uom_dozen')

        cls.product_a = cls.env['product.product'].create({
            'name': 'Product A',
            'list_price': 100.0,
            'uom_id': cls.uom_unit.id,
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Product B',
            'list_price': 50.0,
            'uom_id': cls.uom_unit.id,
        })

        # Tender types
        cls.type_exclusive_copy = cls.env['sale.tender.type'].create({
            'name': 'Exclusive Full Copy',
            'exclusive': 'exclusive',
            'quantity_copy': 'copy',
            'line_copy': 'copy',
        })
        cls.type_no_line_copy = cls.env['sale.tender.type'].create({
            'name': 'No Line Copy',
            'exclusive': 'multiple',
            'quantity_copy': 'none',
            'line_copy': 'none',
        })
        cls.type_copy_lines_no_qty = cls.env['sale.tender.type'].create({
            'name': 'Copy Lines Zero Qty',
            'exclusive': 'multiple',
            'quantity_copy': 'none',
            'line_copy': 'copy',
        })

    def test_onchange_company_id_warning(self):
        """Test warning when changing company on draft quotation with lines and no tender."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })
        # Without tender: warning returned
        res = so._onchange_company_id_warning()
        self.assertIsInstance(res, dict)
        self.assertIn('warning', res)

        # With tender: no warning returned
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.type_exclusive_copy.id,
        })
        so.tender_id = tender
        res_with_tender = so._onchange_company_id_warning()
        self.assertFalse(res_with_tender)

    def test_sale_order_group_and_alternatives(self):
        """Test grouping orders via context and managing alternative SOs."""
        # 1. Create origin order
        origin_so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 5.0,
                'price_unit': 100.0,
            })],
        })
        self.assertFalse(origin_so.sale_group_id)

        # 2. Create alternative order with origin_so_id in context
        alt_so_1 = self.env['sale.order'].with_context(origin_so_id=origin_so.id).create({
            'partner_id': self.partner_2.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 5.0,
                'price_unit': 95.0,
            })],
        })
        self.assertTrue(origin_so.sale_group_id)
        self.assertEqual(origin_so.sale_group_id, alt_so_1.sale_group_id)
        self.assertIn(alt_so_1, origin_so.alternative_so_ids)
        self.assertIn(origin_so, alt_so_1.alternative_so_ids)

        # 3. Create a 3rd order with origin_so_id when origin already has a group
        alt_so_2 = self.env['sale.order'].with_context(origin_so_id=origin_so.id).create({
            'partner_id': self.partner_2.id,
        })
        self.assertEqual(alt_so_2.sale_group_id, origin_so.sale_group_id)
        self.assertEqual(len(origin_so.sale_group_id.order_ids), 3)

        # 4. Test SaleOrderGroup.write unlinking when order_ids <= 1
        group = origin_so.sale_group_id
        group.write({'order_ids': [Command.set([origin_so.id])]})
        self.assertFalse(group.exists(), "Group should be unlinked when order_ids <= 1")
        self.assertFalse(origin_so.sale_group_id)

    def test_sale_order_write_alternatives_creation_and_removal(self):
        """Test write(vals) auto-creating, merging, and auto-clearing sale.order.group."""
        so1 = self.env['sale.order'].create({'partner_id': self.partner.id})
        so2 = self.env['sale.order'].create({'partner_id': self.partner_2.id})
        so3 = self.env['sale.order'].create({'partner_id': self.partner.id})
        so4 = self.env['sale.order'].create({'partner_id': self.partner_2.id})

        # 1. Linking alternative_so_ids creates group 1 with so1 and so2
        so1.write({'alternative_so_ids': [Command.set([so2.id])]})
        group1 = so1.sale_group_id
        self.assertTrue(group1)
        self.assertEqual(so1.sale_group_id, so2.sale_group_id)

        # 2. Linking alternative_so_ids creates group 2 with so3 and so4
        so3.write({'alternative_so_ids': [Command.set([so4.id])]})
        group2 = so3.sale_group_id
        self.assertTrue(group2)
        self.assertNotEqual(group1, group2)

        # 3. Merging groups: move so3 to group1 -> group2 remaining order (so4) is merged into group1
        so3.write({'sale_group_id': group1.id})
        self.assertEqual(so3.sale_group_id, group1)
        self.assertIn(so4, group1.order_ids)
        self.assertFalse(group2.exists(), "group2 should be unlinked upon merge")

        # 4. Clearing alternative_so_ids on so1 unlinks group when only 1 order remains
        so2.write({'alternative_so_ids': [Command.set([])]})
        so3.write({'alternative_so_ids': [Command.set([])]})
        so1.write({'alternative_so_ids': [Command.set([])]})
        self.assertFalse(so1.sale_group_id)

    def test_exclusive_tender_confirmation(self):
        """Test confirming an order linked to an exclusive tender cancels other orders."""
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.type_exclusive_copy.id,
            'line_ids': [Command.create({
                'product_id': self.product_a.id,
                'product_qty': 10.0,
                'price_unit': 120.0,
            })],
        })
        tender.action_in_progress()

        so1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'tender_id': tender.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 10.0,
                'price_unit': 120.0,
            })],
        })
        so2 = self.env['sale.order'].create({
            'partner_id': self.partner_2.id,
            'tender_id': tender.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 10.0,
                'price_unit': 115.0,
            })],
        })

        self.assertEqual(so1.state, 'draft')
        self.assertEqual(so2.state, 'draft')

        # Confirm so1
        so1.action_confirm()
        self.assertEqual(so1.state, 'sale')
        self.assertEqual(so2.state, 'cancel', "Other SO in exclusive tender must be cancelled")
        self.assertEqual(tender.state, 'done', "Tender must transition to done when winning SO confirmed")

    def test_onchange_tender_id_copy_variations(self):
        """Test _onchange_tender_id with line_copy, quantity_copy, and UoM conversion."""
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.type_exclusive_copy.id,
            'description': '<p>Terms and conditions note</p>',
            'line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_qty': 2.0,
                    'product_uom_id': self.uom_dozen.id,  # 2 Dozen = 24 Units
                    'price_unit': 1200.0,
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_qty': 5.0,
                    'product_uom_id': self.uom_unit.id,
                    'price_unit': 50.0,
                }),
            ],
        })
        tender.action_in_progress()

        so = self.env['sale.order'].new({'partner_id': self.partner.id})
        so.tender_id = tender
        so._onchange_tender_id()

        self.assertEqual(so.partner_id, self.partner)
        self.assertEqual(so.company_id, tender.company_id)
        self.assertEqual(so.currency_id, tender.currency_id)
        self.assertIn(tender.name, so.origin)
        self.assertEqual(so.note, tender.description)
        self.assertEqual(len(so.order_line), 2)

        # Test UoM conversion for line with Dozen -> computed price and quantity
        line_a = so.order_line.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(line_a.product_uom_qty, 24.0)

        # Test with line_copy != 'copy'
        tender_no_copy = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.type_no_line_copy.id,
            'line_ids': [Command.create({
                'product_id': self.product_a.id,
                'product_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        so_no_copy = self.env['sale.order'].new({'partner_id': self.partner.id})
        so_no_copy.tender_id = tender_no_copy
        so_no_copy._onchange_tender_id()
        self.assertEqual(len(so_no_copy.order_line), 0)

        # Test with line_copy == 'copy' and quantity_copy != 'copy' (zero quantity)
        tender_zero_qty = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.type_copy_lines_no_qty.id,
            'line_ids': [Command.create({
                'product_id': self.product_b.id,
                'product_qty': 10.0,
                'price_unit': 45.0,
            })],
        })
        so_zero_qty = self.env['sale.order'].new({'partner_id': self.partner.id})
        so_zero_qty.tender_id = tender_zero_qty
        so_zero_qty._onchange_tender_id()
        self.assertEqual(len(so_zero_qty.order_line), 1)
        self.assertEqual(so_zero_qty.order_line[0].product_uom_qty, 0.0)

        # Test _onchange_tender_id when tender_id is False
        so_empty = self.env['sale.order'].new({'partner_id': self.partner.id})
        so_empty.tender_id = False
        so_empty._onchange_tender_id()

    def test_actions_compare_and_create_alternative(self):
        """Test action_compare_alternative_lines and action_create_alternative."""
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })

        # Compare action
        compare_action = so.action_compare_alternative_lines()
        self.assertEqual(compare_action['res_model'], 'sale.order.line')
        self.assertEqual(compare_action['view_mode'], 'list')
        self.assertIn(('order_id', 'in', so.ids), compare_action['domain'])

        # Create alternative action
        alt_action = so.action_create_alternative()
        self.assertEqual(alt_action['res_model'], 'sale.tender.create.alternative')
        self.assertEqual(alt_action['target'], 'new')
        self.assertEqual(alt_action['context']['default_origin_so_id'], so.id)

    def test_get_tender_best_lines_single_and_multi_currency(self):
        """Test get_tender_best_lines under single and multi-currency conditions."""
        so1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 10.0,
                    'price_unit': 100.0,  # Subtotal = 1000.0
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 5.0,
                    'price_unit': 20.0,   # Subtotal = 100.0
                }),
            ],
        })
        # Alternative SO with higher price for Product A and Product B
        so2 = self.env['sale.order'].with_context(origin_so_id=so1.id).create({
            'partner_id': self.partner_2.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 10.0,
                    'price_unit': 120.0,  # Subtotal = 1200.0 (Higher)
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 2.0,
                    'price_unit': 60.0,   # Unit Price = 60 (Higher), Subtotal = 120 (Higher)
                }),
            ],
        })

        best_lines, best_units = so1.get_tender_best_lines()
        line_a_so2 = so2.order_line.filtered(lambda l: l.product_id == self.product_a)
        line_b_so2 = so2.order_line.filtered(lambda l: l.product_id == self.product_b)

        self.assertIn(line_a_so2.id, best_lines)
        self.assertIn(line_b_so2.id, best_lines)
        self.assertIn(line_a_so2.id, best_units)
        self.assertIn(line_b_so2.id, best_units)

        # Multi-currency test
        eur_currency = self.env.ref('base.EUR')
        so2.currency_id = eur_currency
        best_lines_mc, best_units_mc = so1.get_tender_best_lines()
        self.assertTrue(best_lines_mc)
        self.assertTrue(best_units_mc)

    def test_sale_order_line_actions_clear_and_choose(self):
        """Test action_clear_quantities and action_choose on alternative lines."""
        so1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 10.0,
                'price_unit': 100.0,
            })],
        })
        so2 = self.env['sale.order'].with_context(origin_so_id=so1.id).create({
            'partner_id': self.partner_2.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 10.0,
                'price_unit': 90.0,
            })],
        })

        line1 = so1.order_line[0]
        line2 = so2.order_line[0]

        # Choosing line1 should zero out line2's product_uom_qty
        self.assertEqual(line2.product_uom_qty, 10.0)
        res_choose = line1.action_choose()
        self.assertFalse(res_choose)
        self.assertEqual(line2.product_uom_qty, 0.0)
        self.assertEqual(line1.product_uom_qty, 10.0)

        # Calling action_choose when nothing to clear returns notification
        res_nothing = line1.action_choose()
        self.assertIsInstance(res_nothing, dict)
        self.assertEqual(res_nothing['params']['title'], "Nothing to clear")

        # Calling action_clear_quantities directly
        line1.action_clear_quantities()
        self.assertEqual(line1.product_uom_qty, 0.0)

        # Clearing quantities on confirmed/cancelled lines triggers partial clear notification
        so1.action_confirm()
        res_partial = line1.action_clear_quantities()
        self.assertIsInstance(res_partial, dict)
        self.assertEqual(res_partial['params']['title'], "Some not cleared")

    def test_onchange_tender_id_with_sale_description(self):
        """Test _onchange_tender_id with product sale description."""
        self.product_a.description_sale = 'Sale specification text'
        tender = self.env['sale.tender'].create({
            'customer_id': self.partner.id,
            'type_id': self.type_exclusive_copy.id,
            'line_ids': [Command.create({
                'product_id': self.product_a.id,
                'product_qty': 2.0,
                'price_unit': 100.0,
            })],
        })
        so = self.env['sale.order'].new({
            'partner_id': self.partner.id,
        })
        so.tender_id = tender
        so._onchange_tender_id()
        self.assertEqual(len(so.order_line), 1)
        self.assertIn('Sale specification text', so.order_line[0].name)

        # Trigger _onchange_sale_order_template_id when tender_id is present
        so._onchange_sale_order_template_id()

    def test_get_tender_best_lines_equal_and_lower_prices_and_skipped_lines(self):
        """Test get_tender_best_lines with equal prices, lower prices, and skipped lines."""
        so1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 10.0,
                    'price_unit': 100.0,
                }),
                Command.create({
                    'product_id': self.product_b.id,
                    'product_uom_qty': 0.0,  # Skipped because qty=0
                    'price_unit': 50.0,
                }),
            ],
        })
        # so2 with equal subtotal and unit price for product A
        so2 = self.env['sale.order'].with_context(origin_so_id=so1.id).create({
            'partner_id': self.partner_2.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 10.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        best_lines, best_units = so1.get_tender_best_lines()
        self.assertIn(so1.order_line[0].id, best_lines)
        self.assertIn(so2.order_line[0].id, best_lines)

        # Separate comparison where so1 has higher price than an alternative so3
        so_base = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 10.0,
                    'price_unit': 100.0,
                }),
            ],
        })
        so_lower = self.env['sale.order'].with_context(origin_so_id=so_base.id).create({
            'partner_id': self.partner_2.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 5.0,
                    'price_unit': 80.0,  # Lower subtotal and unit price
                }),
            ],
        })
        base_best_lines, base_best_units = so_base.get_tender_best_lines()
        self.assertIn(so_base.order_line[0].id, base_best_lines)
        self.assertNotIn(so_lower.order_line[0].id, base_best_lines)

    def test_unlink_sale_group_when_alternative_unlinked(self):
        """Test unlinking group when alternative_so_ids reduced to 1 or 0."""
        so1 = self.env['sale.order'].create({'partner_id': self.partner.id})
        so2 = self.env['sale.order'].create({'partner_id': self.partner_2.id})
        so1.write({'alternative_so_ids': [Command.set([so2.id])]})
        group = so1.sale_group_id
        self.assertTrue(group)

        # Remove so2 from alternatives
        so1.write({'alternative_so_ids': [Command.unlink(so2.id)]})
        self.assertFalse(group.exists())


