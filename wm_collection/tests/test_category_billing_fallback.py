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

from odoo.tests import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_collection')
class TestCategoryBillingFallback(TransactionCase):
    """Unit tests verifying billing rate fallback hierarchy on collection orders."""

    @classmethod
    def setUpClass(cls):
        """
        Set up test class fixtures and environment.
        """
        super().setUpClass()
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Test Category Price Stream',
            'code': 'TCPRICE',
            'price': 0.75,
        })
        cls.product_no_price = cls.env['product.product'].create({
            'name': 'Zero Price Product',
            'is_waste_material': True,
            'wm_waste_category_id': cls.category.id,
            'list_price': 0.0,
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Test Billing Partner'})
        cls.point = cls.env['wm.collection.point'].create({
            'name': 'Test Billing Point',
            'partner_id': cls.partner.id,
        })

    def test_category_billing_fallback(self):
        """
        Invoice uses category price when line product has no list_price or
        product_id is not set.
        """
        order = self.env['wm.collection.order'].create({
            'name': 'ORD-BILL-TEST-001',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'company_id': self.env.company.id,
            'state': 'completed',
        })
        line_no_prod = self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category.id,
            'weight': 100.0,
        })
        self.assertEqual(line_no_prod.price, 0.75, "Price per kg should fallback to category price (0.75) when product_id is not set")

        line_prod_zero = self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category.id,
            'product_id': self.product_no_price.id,
            'weight': 50.0,
        })
        self.assertEqual(line_prod_zero.price, 0.75, "Price per kg should fallback to category price (0.75) when product list_price is 0")

        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'order_ids': [(6, 0, [order.id])],
        })
        action = consolidated.action_generate_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertTrue(invoice, "Invoice should be created")

        _logger.info('PASS: test_category_billing_fallback')

    def test_category_billing_rule_precedence(self):
        """
        Partner-specific billing rule overrides generic category billing rule
        and fallback.
        """
        self.env['wm.category.billing.rule'].create({
            'category_id': self.category.id,
            'price': 1.50,
            'billing_basis': 'per_kg',
        })
        order_generic = self.env['wm.collection.order'].create({
            'name': 'ORD-GENERIC-RULE',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'company_id': self.env.company.id,
        })
        line_generic = self.env['wm.collection.order.line'].create({
            'order_id': order_generic.id,
            'category_id': self.category.id,
            'weight': 10.0,
        })
        self.assertEqual(line_generic.price, 1.50, "Generic category billing rule price should be applied")

        partner_specific = self.env['res.partner'].create({'name': 'Special Rate Partner'})
        self.env['wm.category.billing.rule'].create({
            'category_id': self.category.id,
            'partner_id': partner_specific.id,
            'price': 2.00,
            'billing_basis': 'per_kg',
        })
        point_spec = self.env['wm.collection.point'].create({
            'name': 'Special Point',
            'partner_id': partner_specific.id,
        })
        order_spec = self.env['wm.collection.order'].create({
            'name': 'ORD-SPEC-RULE',
            'partner_id': partner_specific.id,
            'collection_point_id': point_spec.id,
            'company_id': self.env.company.id,
        })
        line_spec = self.env['wm.collection.order.line'].create({
            'order_id': order_spec.id,
            'category_id': self.category.id,
            'weight': 10.0,
        })
        self.assertEqual(line_spec.price, 2.00, "Partner specific rule (2.00) should override generic rule (1.50)")

    def test_category_billing_rule_min_charge(self):
        """
        Minimum charge is enforced on invoice line when calculated amount is
        lower.
        """
        self.env['wm.pricing.rule'].create({
            'waste_category_id': self.category.id,
            'partner_id': self.partner.id,
            'price_per_kg': 1.00,
            'min_charge': 50.00,
            'active': True,
        })
        order = self.env['wm.collection.order'].create({
            'name': 'ORD-MIN-CHARGE',
            'partner_id': self.partner.id,
            'collection_point_id': self.point.id,
            'company_id': self.env.company.id,
            'state': 'completed',
        })
        self.env['wm.collection.order.line'].create({
            'order_id': order.id,
            'category_id': self.category.id,
            'weight': 10.0,  # 10 kg * $1.00 = $10, lower than min_charge $50
        })
        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'order_ids': [(6, 0, [order.id])],
        })
        action = consolidated.action_generate_invoice()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.amount_total, 50.00, "Invoice total should equal minimum charge ($50.00)")
