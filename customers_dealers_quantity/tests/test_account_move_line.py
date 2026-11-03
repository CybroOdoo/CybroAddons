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
class TestAccountMoveLine(TransactionCase):
    """Test cases for account.move.line dealer pricing computation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.AccountMove = cls.env['account.move']

        cls.regular_partner = cls.Partner.create({
            'name': 'Regular Customer',
            'dealer': False,
        })
        cls.dealer_partner = cls.Partner.create({
            'name': 'Dealer Customer',
            'dealer': True,
        })

        cls.dealer_product = cls.Product.create({
            'name': 'Invoice Dealer Product',
            'list_price': 120.0,
            'price': 85.0,
            'minimum_quantity': 10.0,
        })
        cls.regular_product = cls.Product.create({
            'name': 'Standard Product No Dealer Price',
            'list_price': 90.0,
            'price': 0.0,
            'minimum_quantity': 0.0,
        })

    def test_invoice_line_dealer_meeting_threshold(self):
        """Test dealer customer receives dealer price on customer invoice when quantity >= threshold."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 10.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(
            line.price_unit,
            85.0,
            "Dealer customer should get dealer price on invoice when meeting quantity threshold."
        )

    def test_invoice_line_dealer_exceeding_threshold(self):
        """Test dealer customer receives dealer price when quantity > threshold."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 25.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(line.price_unit, 85.0)

    def test_invoice_line_dealer_below_threshold(self):
        """Test dealer customer receives standard price when quantity < threshold."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 9.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(
            line.price_unit,
            120.0,
            "Dealer below threshold should receive standard list price on invoice."
        )

    def test_invoice_line_non_dealer(self):
        """Test non-dealer receives standard price even when quantity exceeds dealer threshold."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 50.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(
            line.price_unit,
            120.0,
            "Non-dealer should always receive standard price on invoice."
        )

    def test_vendor_bill_does_not_apply_dealer_price(self):
        """Test dealer price is never applied on vendor bills (in_invoice)."""
        move = self.AccountMove.create({
            'move_type': 'in_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 20.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertNotEqual(
            line.price_unit,
            85.0,
            "Dealer pricing must not be applied to vendor bills."
        )

    def test_invoice_line_quantity_change_recomputes_price(self):
        """Test updating line quantity triggers update of unit price via onchange."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 5.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(line.price_unit, 120.0)

        line.quantity = 15.0
        line._onchange_quantity_dealer_price()
        self.assertEqual(
            line.price_unit,
            85.0,
            "Price unit should update to dealer price after quantity reaches threshold via onchange."
        )

    def test_quantity_edit_does_not_overwrite_manual_price_non_dealer(self):
        """Test quantity edits do not overwrite manual prices for non-dealers."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 5.0,
                'price_unit': 77.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(line.price_unit, 77.0)

        # Quantity change on line must not overwrite manual price
        line.quantity = 25.0
        line._onchange_quantity_dealer_price()
        self.assertEqual(
            line.price_unit,
            77.0,
            "Manual unit price must not be overwritten when quantity is edited for non-dealer."
        )

    def test_quantity_edit_does_not_overwrite_vendor_bill(self):
        """Test quantity edits do not overwrite vendor bill line prices."""
        move = self.AccountMove.create({
            'move_type': 'in_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 5.0,
                'price_unit': 42.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(line.price_unit, 42.0)

        line.quantity = 50.0
        line._onchange_quantity_dealer_price()
        self.assertEqual(
            line.price_unit,
            42.0,
            "Vendor bill unit price must not be overwritten when quantity is edited."
        )

    def test_product_without_dealer_pricing(self):
        """Test product with 0.0 dealer price and 0.0 min qty retains standard price."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.regular_product.id,
                'quantity': 20.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(
            line.price_unit,
            90.0,
            "Product with no dealer pricing should maintain its standard price."
        )

    def test_invoice_line_dealer_currency_conversion(self):
        """Test dealer price currency conversion during line compute when invoice is in foreign currency."""
        currency_eur = self.env.ref('base.EUR')
        currency_eur.rate_ids = [Command.create({
            'name': '2026-01-01',
            'company_rate': 0.8,
        })]
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'currency_id': currency_eur.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 15.0,
            })],
        })
        line = move.invoice_line_ids
        company_currency = line.company_id.currency_id or self.env.company.currency_id
        expected_price = company_currency._convert(
            self.dealer_product.price,
            currency_eur,
            line.company_id or self.env.company,
            move.invoice_date or move.date,
        )
        self.assertAlmostEqual(line.price_unit, expected_price)

    def test_invoice_line_with_sale_order_line_not_overwritten(self):
        """Test invoice line linked to a sale order is not overwritten when quantity changes or onchange runs."""
        so = self.env['sale.order'].create({
            'partner_id': self.dealer_partner.id,
            'order_line': [Command.create({
                'product_id': self.dealer_product.id,
                'product_uom_qty': 15.0,
                'price_unit': 95.0,
            })],
        })
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 15.0,
                'price_unit': 95.0,
                'sale_line_ids': [Command.link(so.order_line.id)],
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(line.price_unit, 95.0)

        # Quantity change on line does not overwrite price, and onchange skips lines linked to SO
        line.quantity = 25.0
        line._onchange_quantity_dealer_price()
        self.assertEqual(
            line.price_unit,
            95.0,
            "Invoice line linked to sale order must retain its agreed sale price."
        )

    def test_onchange_quantity_reverts_to_list_price_when_below_threshold(self):
        """Test dealer price reverts to product price when quantity drops below minimum quantity."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 15.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(line.price_unit, 85.0)

        # Drop below threshold
        line.quantity = 3.0
        line._onchange_quantity_dealer_price()
        self.assertEqual(
            line.price_unit,
            120.0,
            "Price unit should revert to standard list price when quantity drops below threshold."
        )

    def test_onchange_quantity_preserves_manual_price_when_below_threshold(self):
        """Test dealer line with manual price does not revert when quantity changes."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 15.0,
                'price_unit': 70.0,
            })],
        })
        line = move.invoice_line_ids
        self.assertEqual(line.price_unit, 70.0)

        line.quantity = 3.0
        line._onchange_quantity_dealer_price()
        self.assertEqual(
            line.price_unit,
            70.0,
            "Custom manual price must not be overwritten when quantity drops below threshold."
        )

    def test_onchange_quantity_dealer_vendor_bill_no_op(self):
        """Test onchange quantity on vendor bill for a dealer partner never applies dealer price."""
        move = self.AccountMove.create({
            'move_type': 'in_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.dealer_product.id,
                'quantity': 5.0,
                'price_unit': 50.0,
            })],
        })
        line = move.invoice_line_ids
        line.quantity = 50.0
        line._onchange_quantity_dealer_price()
        self.assertEqual(
            line.price_unit,
            50.0,
            "Vendor bill lines for dealer partners must never be modified by dealer onchange."
        )

    def test_onchange_quantity_section_line_safely_skipped(self):
        """Test onchange quantity ignores section and note lines without product_id."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'display_type': 'line_section',
                'name': 'Section Header',
                'quantity': 5.0,
            })],
        })
        line = move.invoice_line_ids
        line.quantity = 25.0
        # Should not raise exception
        line._onchange_quantity_dealer_price()
        self.assertFalse(line.product_id)
