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
class TestAccountMove(TransactionCase):
    """Test cases for account.move onchange_partner_id dealer pricing recomputation."""

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

        cls.product = cls.Product.create({
            'name': 'Invoice Test Product',
            'list_price': 100.0,
            'price': 55.0,
            'minimum_quantity': 10.0,
        })

    def test_onchange_partner_id_to_dealer(self):
        """Test changing invoice partner from regular to dealer updates line price unit."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 10.0,
            })],
        })
        self.assertEqual(move.invoice_line_ids.price_unit, 100.0)

        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        self.assertEqual(
            move.invoice_line_ids.price_unit,
            55.0,
            "Invoice line price unit should update to dealer price when partner changes to dealer."
        )

    def test_onchange_partner_id_to_non_dealer(self):
        """Test changing invoice partner from dealer to regular reverts line price unit."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.dealer_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 10.0,
            })],
        })
        self.assertEqual(move.invoice_line_ids.price_unit, 55.0)

        move.partner_id = self.regular_partner
        move._onchange_partner_id()
        self.assertEqual(
            move.invoice_line_ids.price_unit,
            100.0,
            "Invoice line price unit should revert to standard list price when partner is non-dealer."
        )

    def test_onchange_partner_id_empty_lines(self):
        """Test calling _onchange_partner_id on invoice with no lines executes without error."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
        })
        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        self.assertFalse(move.invoice_line_ids)

    def test_onchange_partner_id_preserves_manual_price_non_dealer(self):
        """Test changing partner does not overwrite manual prices on lines without dealer price."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 10.0,
                'price_unit': 80.0,
            })],
        })
        self.assertEqual(move.invoice_line_ids.price_unit, 80.0)

        # Another non-dealer partner
        other_partner = self.Partner.create({'name': 'Other Regular', 'dealer': False})
        move.partner_id = other_partner
        move._onchange_partner_id()
        self.assertEqual(
            move.invoice_line_ids.price_unit,
            80.0,
            "Changing to another non-dealer partner must not overwrite manual prices."
        )

    def test_onchange_partner_id_vendor_bill_not_touched(self):
        """Test changing partner on vendor bill does not modify bill line prices."""
        move = self.AccountMove.create({
            'move_type': 'in_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 10.0,
                'price_unit': 40.0,
            })],
        })
        self.assertEqual(move.invoice_line_ids.price_unit, 40.0)

        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        self.assertEqual(
            move.invoice_line_ids.price_unit,
            40.0,
            "Changing partner on vendor bill must never modify bill line prices."
        )

    def test_onchange_partner_id_below_minimum_quantity(self):
        """Test changing partner to dealer does not apply dealer price when quantity < minimum_quantity."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 5.0,
            })],
        })
        self.assertEqual(move.invoice_line_ids.price_unit, 100.0)

        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        self.assertEqual(
            move.invoice_line_ids.price_unit,
            100.0,
            "Price unit should remain standard price when quantity < minimum_quantity."
        )

    def test_onchange_partner_id_product_without_dealer_price(self):
        """Test changing partner to dealer does not change price for products without dealer pricing."""
        regular_product = self.Product.create({
            'name': 'Plain Widget',
            'list_price': 120.0,
            'price': 0.0,
            'minimum_quantity': 0.0,
        })
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': regular_product.id,
                'quantity': 20.0,
            })],
        })
        self.assertEqual(move.invoice_line_ids.price_unit, 120.0)

        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        self.assertEqual(
            move.invoice_line_ids.price_unit,
            120.0,
            "Product without dealer pricing should keep standard price on partner change."
        )

    def test_onchange_partner_id_section_line_skipped(self):
        """Test section/note lines without product_id are safely skipped during partner change."""
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [
                Command.create({
                    'display_type': 'line_section',
                    'name': 'Section Header',
                }),
                Command.create({
                    'product_id': self.product.id,
                    'quantity': 10.0,
                }),
            ],
        })
        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        product_line = move.invoice_line_ids.filtered(lambda l: l.product_id)
        self.assertEqual(product_line.price_unit, 55.0)

    def test_onchange_partner_id_with_sale_order_line(self):
        """Test invoice lines originating from a sale order are not overwritten on partner change."""
        so = self.env['sale.order'].create({
            'partner_id': self.regular_partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 10.0,
                'price_unit': 88.0,
            })],
        })
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 10.0,
                'price_unit': 88.0,
                'sale_line_ids': [Command.link(so.order_line.id)],
            })],
        })
        line = move.invoice_line_ids.filtered(lambda l: l.product_id)
        self.assertEqual(line.price_unit, 88.0)

        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        self.assertEqual(
            line.price_unit,
            88.0,
            "Invoice line linked to a sale order must preserve its agreed sale price."
        )

    def test_onchange_partner_id_currency_conversion(self):
        """Test dealer price conversion when invoice currency differs from company currency."""
        currency_eur = self.env.ref('base.EUR')
        currency_eur.rate_ids = [Command.create({
            'name': '2026-01-01',
            'company_rate': 0.8,
        })]
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': self.regular_partner.id,
            'currency_id': currency_eur.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 10.0,
            })],
        })
        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        line = move.invoice_line_ids
        company_currency = line.company_id.currency_id or self.env.company.currency_id
        expected_price = company_currency._convert(
            self.product.price,
            currency_eur,
            line.company_id or self.env.company,
            move.invoice_date or move.date,
        )
        self.assertAlmostEqual(line.price_unit, expected_price)

    def test_onchange_partner_id_credit_note_not_touched(self):
        """Test changing partner on customer credit note (out_refund) does not modify lines."""
        move = self.AccountMove.create({
            'move_type': 'out_refund',
            'partner_id': self.regular_partner.id,
            'invoice_line_ids': [Command.create({
                'product_id': self.product.id,
                'quantity': 10.0,
                'price_unit': 75.0,
            })],
        })
        self.assertEqual(move.invoice_line_ids.price_unit, 75.0)

        move.partner_id = self.dealer_partner
        move._onchange_partner_id()
        self.assertEqual(
            move.invoice_line_ids.price_unit,
            75.0,
            "Changing partner on customer credit note must not modify line unit price."
        )
