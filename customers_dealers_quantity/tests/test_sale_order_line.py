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
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderLine(TransactionCase):
    """Test cases for sale.order.line dealer display price logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.SaleOrder = cls.env['sale.order']
        cls.SaleOrderLine = cls.env['sale.order.line']

        cls.regular_partner = cls.Partner.create({
            'name': 'Regular Customer',
            'dealer': False,
        })
        cls.dealer_partner = cls.Partner.create({
            'name': 'Dealer Customer',
            'dealer': True,
        })

        cls.dealer_product = cls.Product.create({
            'name': 'Dealer Tier Product',
            'list_price': 100.0,
            'price': 65.0,
            'minimum_quantity': 5.0,
        })
        cls.regular_product = cls.Product.create({
            'name': 'Standard Product No Dealer Price',
            'list_price': 80.0,
            'price': 0.0,
            'minimum_quantity': 0.0,
        })

    def test_display_price_for_dealer_meeting_threshold(self):
        """Test dealer gets special price when quantity >= minimum_quantity."""
        order = self.SaleOrder.create({
            'partner_id': self.dealer_partner.id,
            'order_line': [Command.create({
                'product_id': self.dealer_product.id,
                'product_uom_qty': 5.0,
            })],
        })
        line = order.order_line
        display_price = line._get_display_price()
        self.assertEqual(
            display_price,
            65.0,
            "Dealer meeting minimum quantity threshold should receive the dealer price."
        )
        self.assertEqual(line.price_unit, 65.0)

    def test_display_price_for_dealer_exceeding_threshold(self):
        """Test dealer gets special price when quantity > minimum_quantity."""
        order = self.SaleOrder.create({
            'partner_id': self.dealer_partner.id,
            'order_line': [Command.create({
                'product_id': self.dealer_product.id,
                'product_uom_qty': 20.0,
            })],
        })
        line = order.order_line
        self.assertEqual(line._get_display_price(), 65.0)
        self.assertEqual(line.price_unit, 65.0)

    def test_display_price_for_dealer_below_threshold(self):
        """Test dealer receives standard list price when quantity < minimum_quantity."""
        order = self.SaleOrder.create({
            'partner_id': self.dealer_partner.id,
            'order_line': [Command.create({
                'product_id': self.dealer_product.id,
                'product_uom_qty': 4.0,
            })],
        })
        line = order.order_line
        self.assertEqual(
            line._get_display_price(),
            100.0,
            "Dealer below minimum quantity threshold should receive standard list price."
        )
        self.assertEqual(line.price_unit, 100.0)

    def test_display_price_for_non_dealer(self):
        """Test non-dealer customer receives standard list price even when quantity >= threshold."""
        order = self.SaleOrder.create({
            'partner_id': self.regular_partner.id,
            'order_line': [Command.create({
                'product_id': self.dealer_product.id,
                'product_uom_qty': 10.0,
            })],
        })
        line = order.order_line
        self.assertEqual(
            line._get_display_price(),
            100.0,
            "Non-dealer should always receive standard price regardless of quantity."
        )
        self.assertEqual(line.price_unit, 100.0)

    def test_display_price_product_without_dealer_price(self):
        """Test dealer customer with product that has 0.0 dealer price and 0.0 min qty."""
        order = self.SaleOrder.create({
            'partner_id': self.dealer_partner.id,
            'order_line': [Command.create({
                'product_id': self.regular_product.id,
                'product_uom_qty': 10.0,
            })],
        })
        line = order.order_line
        self.assertEqual(
            line._get_display_price(),
            80.0,
            "Product with no dealer pricing should fallback to standard price."
        )

    def test_quantity_update_triggers_price_change(self):
        """Test changing product_uom_qty from below threshold to above threshold."""
        order = self.SaleOrder.create({
            'partner_id': self.dealer_partner.id,
            'order_line': [Command.create({
                'product_id': self.dealer_product.id,
                'product_uom_qty': 2.0,
            })],
        })
        line = order.order_line
        self.assertEqual(line.price_unit, 100.0)

        # Update quantity to meet threshold
        line.product_uom_qty = 5.0
        line._compute_price_unit()
        self.assertEqual(
            line.price_unit,
            65.0,
            "Price unit should update to dealer price after quantity increases to meet threshold."
        )

    def test_display_price_currency_conversion(self):
        """Test dealer price currency conversion when order currency differs from company currency."""
        currency_eur = self.env.ref('base.EUR')
        currency_eur.rate_ids = [Command.create({
            'name': '2026-01-01',
            'company_rate': 0.8,
        })]
        pricelist_eur = self.env['product.pricelist'].create({
            'name': 'EUR Pricelist',
            'currency_id': currency_eur.id,
        })
        order = self.SaleOrder.create({
            'partner_id': self.dealer_partner.id,
            'pricelist_id': pricelist_eur.id,
            'order_line': [Command.create({
                'product_id': self.dealer_product.id,
                'product_uom_qty': 10.0,
            })],
        })
        line = order.order_line
        company_currency = line.company_id.currency_id or self.env.company.currency_id
        expected_price = company_currency._convert(
            self.dealer_product.price,
            currency_eur,
            line.company_id or self.env.company,
            order.date_order,
        )
        self.assertAlmostEqual(line._get_display_price(), expected_price)

    def test_display_price_product_with_zero_min_quantity(self):
        """Test product with dealer price > 0 and minimum_quantity == 0."""
        zero_min_product = self.Product.create({
            'name': 'Zero Min Product',
            'list_price': 100.0,
            'price': 60.0,
            'minimum_quantity': 0.0,
        })
        order = self.SaleOrder.create({
            'partner_id': self.dealer_partner.id,
            'order_line': [Command.create({
                'product_id': zero_min_product.id,
                'product_uom_qty': 1.0,
            })],
        })
        self.assertEqual(order.order_line._get_display_price(), 60.0)
