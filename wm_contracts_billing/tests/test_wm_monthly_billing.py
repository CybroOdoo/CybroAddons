# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_billing')
class TestWmMonthlyBilling(TransactionCase):
    """Unit tests verifying monthly billing execution run creation and invoice batching."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Monthly Billing Customer',
            'email': 'monthly@example.com',
        })
        cls.category_plastic = cls.env['wm.waste.category'].create({
            'name': 'Recyclable Plastic',
            'code': 'PLAST',
            'price': 5.0,
        })
        cls.category_paper = cls.env['wm.waste.category'].create({
            'name': 'Waste Paper',
            'code': 'PAPER',
            'price': 3.0,
        })
        cls.product_plastic = cls.env['product.product'].create({
            'name': 'Plastic Scrap Material',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category_plastic.id,
            'list_price': 5.0,
        })
        cls.product_paper = cls.env['product.product'].create({
            'name': 'Paper Waste Material',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category_paper.id,
            'list_price': 3.0,
        })
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Test Main Point',
            'partner_id': cls.partner.id,
        })

    def test_per_order_invoice_removed(self):
        """
        wm.collection.order must not have action_create_invoice method.
        """
        order = self.env['wm.collection.order'].new({})
        self.assertFalse(
            hasattr(order, 'action_create_invoice'),
            "action_create_invoice must be removed from collection order"
        )
        _logger.info('PASS: test_per_order_invoice_removed')

    def test_invoiced_state_removed(self):
        """
        'invoiced' must not be a valid state on wm.collection.order.
        """
        state_keys = [k for k, _ in self.env['wm.collection.order']._fields['state'].selection]
        self.assertNotIn('invoiced', state_keys)
        _logger.info('PASS: test_invoiced_state_removed')

    def test_monthly_invoice_aggregates_by_category(self):
        """
        Monthly invoice line count equals number of distinct categories across
        orders.
        """
        order1 = self.env['wm.collection.order'].create({
            'name': 'CO/001',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
            'scheduled_start': fields.Datetime.now(),
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order1.id,
            'category_id': self.category_plastic.id,
            'product_id': self.product_plastic.id,
            'weight': 100.0,
        })

        order2 = self.env['wm.collection.order'].create({
            'name': 'CO/002',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'signed',
            'scheduled_start': fields.Datetime.now(),
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order2.id,
            'category_id': self.category_plastic.id,
            'product_id': self.product_plastic.id,
            'weight': 150.0,
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order2.id,
            'category_id': self.category_paper.id,
            'product_id': self.product_paper.id,
            'weight': 200.0,
        })

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': fields.Date.today().replace(day=1),
            'date_to': fields.Date.today().replace(day=1) + relativedelta(months=1, days=-1),
            'order_ids': [(6, 0, [order1.id, order2.id])],
        })

        action = consolidated.action_generate_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])

        # 1 section header + 2 category lines + 1 note line = 4 invoice lines
        product_lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type in ('product', False))
        self.assertEqual(len(product_lines), 2, "Consolidated invoice should contain exactly 2 aggregated category lines")
        _logger.info('PASS: test_monthly_invoice_aggregates_by_category')

    def test_completed_orders_are_billable(self):
        """
        Orders in 'completed' state can be added to a monthly invoice.
        """
        order = self.env['wm.collection.order'].create({
            'name': 'CO/COMPLETED',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
            'scheduled_start': fields.Datetime.now(),
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category_plastic.id,
            'product_id': self.product_plastic.id,
            'weight': 50.0,
        })

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'order_ids': [(6, 0, [order.id])],
        })
        # Should not raise ValidationError
        consolidated._check_order_ids_state()
        self.assertEqual(len(consolidated.order_ids), 1)
        _logger.info('PASS: test_completed_orders_are_billable')

    def test_pricing_rule_priority(self):
        """
        Customer-specific pricing rule takes priority over general rule.
        """
        self.env['wm.pricing.rule'].create({
            'waste_category_id': self.category_plastic.id,
            'partner_id': False,  # General rule
            'price_per_kg': 5.0,
            'active': True,
        })
        self.env['wm.pricing.rule'].create({
            'waste_category_id': self.category_plastic.id,
            'partner_id': self.partner.id,  # Customer specific
            'price_per_kg': 7.0,
            'active': True,
        })

        order = self.env['wm.collection.order'].create({
            'name': 'CO/PRIORITY',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category_plastic.id,
            'product_id': self.product_plastic.id,
            'weight': 100.0,
        })

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'order_ids': [(6, 0, [order.id])],
        })
        action = consolidated.action_generate_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        line = invoice.invoice_line_ids.filtered(lambda l: l.display_type in ('product', False))[:1]
        self.assertEqual(line.price_unit, 7.0, "Customer-specific pricing rule (7.0) should override general rule (5.0)")
        _logger.info('PASS: test_pricing_rule_priority')

    def test_min_weight_floor_applied(self):
        """
        Pricing rule min_weight applied when actual weight is below minimum.
        """
        self.env['wm.pricing.rule'].create({
            'waste_category_id': self.category_paper.id,
            'partner_id': self.partner.id,
            'price_per_kg': 4.0,
            'min_weight': 100.0,
            'active': True,
        })

        order = self.env['wm.collection.order'].create({
            'name': 'CO/MINWEIGHT',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category_paper.id,
            'product_id': self.product_paper.id,
            'weight': 60.0,  # Below min_weight 100.0
        })

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'order_ids': [(6, 0, [order.id])],
        })
        action = consolidated.action_generate_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        line = invoice.invoice_line_ids.filtered(lambda l: l.display_type in ('product', False))[:1]
        self.assertEqual(line.quantity, 100.0, "Quantity should equal min_weight floor (100.0)")
        _logger.info('PASS: test_min_weight_floor_applied')

    def test_min_charge_applied(self):
        """
        Pricing rule min_charge applied when computed amount is below minimum.
        """
        self.env['wm.pricing.rule'].create({
            'waste_category_id': self.category_paper.id,
            'partner_id': self.partner.id,
            'price_per_kg': 2.0,
            'min_charge': 150.0,
            'active': True,
        })

        order = self.env['wm.collection.order'].create({
            'name': 'CO/MINCHARGE',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category_paper.id,
            'product_id': self.product_paper.id,
            'weight': 20.0,  # 20 * 2 = 40, below min_charge 150
        })

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'order_ids': [(6, 0, [order.id])],
        })
        action = consolidated.action_generate_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.amount_total, 150.0, "Invoice amount should equal min_charge (150.0)")
        _logger.info('PASS: test_min_charge_applied')

    def test_duplicate_monthly_invoice_blocked(self):
        """
        Cannot generate two invoiced monthly invoices for same partner and
        month.
        """
        date_from = fields.Date.today().replace(day=1)
        date_to = date_from + relativedelta(months=1, days=-1)

        order1 = self.env['wm.collection.order'].create({
            'name': 'CO/DUP1',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order1.id,
            'category_id': self.category_plastic.id,
            'product_id': self.product_plastic.id,
            'weight': 100.0,
        })

        inv1 = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': date_from,
            'date_to': date_to,
            'order_ids': [(6, 0, [order1.id])],
        })
        inv1.action_generate_invoice()

        order2 = self.env['wm.collection.order'].create({
            'name': 'CO/DUP2',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order2.id,
            'category_id': self.category_plastic.id,
            'product_id': self.product_plastic.id,
            'weight': 50.0,
        })

        inv2 = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': date_from,
            'date_to': date_to,
            'order_ids': [(6, 0, [order2.id])],
        })

        with self.assertRaises(ValidationError):
            inv2.action_generate_invoice()

        _logger.info('PASS: test_duplicate_monthly_invoice_blocked')

    def test_reset_to_draft_restores_orders(self):
        """
        Resetting consolidated invoice to draft unlinks orders without
        reverting order state.
        """
        order = self.env['wm.collection.order'].create({
            'name': 'CO/RESET',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category_plastic.id,
            'product_id': self.product_plastic.id,
            'weight': 100.0,
        })

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'order_ids': [(6, 0, [order.id])],
        })
        action = consolidated.action_generate_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])

        # Cancel move to allow reset to draft
        invoice.button_cancel()
        consolidated.action_reset_to_draft()

        self.assertFalse(order.consolidated_invoice_id, "Order consolidated_invoice_id should be False after reset to draft")
        self.assertEqual(order.state, 'completed', "Order state must remain completed after reset")
        _logger.info('PASS: test_reset_to_draft_restores_orders')

    def test_zero_price_warning_posted(self):
        """
        When no price found for a category, chatter warning is posted.
        """
        cat_noprice = self.env['wm.waste.category'].create({
            'name': 'No Price Category',
            'code': 'NOPRICE',
            'price': 0.0,
        })
        prod_noprice = self.env['product.product'].create({
            'name': 'Unpriced Waste Item',
            'is_waste_material': True,
            'wm_waste_category_id': cat_noprice.id,
            'list_price': 0.0,
        })

        order = self.env['wm.collection.order'].create({
            'name': 'CO/NOPRICE',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': cat_noprice.id,
            'product_id': prod_noprice.id,
            'weight': 100.0,
            'price': 0.0,
        })

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'order_ids': [(6, 0, [order.id])],
        })
        action = consolidated.action_generate_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])

        line = invoice.invoice_line_ids.filtered(lambda l: l.display_type in ('product', False))[:1]
        self.assertEqual(line.price_unit, 0.0, "Invoice line price should be 0.0")

        # Verify warning posted in chatter
        messages = consolidated.message_ids.mapped('body')
        self.assertTrue(any("No price resolved" in msg for msg in messages), "Chatter warning should be posted")
        _logger.info('PASS: test_zero_price_warning_posted')

    def test_account_lookup_uses_company_ids(self):
        """
        Odoo 19: account.account filter uses company_ids (M2M), not company_id.
        """
        account = self.env['account.account'].search([
            ('company_ids', 'in', self.env.company.id),
        ], limit=1)
        self.assertTrue(account, "account.account search should succeed using company_ids M2M filter")
        _logger.info('PASS: test_account_lookup_uses_company_ids')
