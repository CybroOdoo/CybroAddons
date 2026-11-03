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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductProduct(TransactionCase):
    """Test cases for dealer fields on product.product."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env['product.product']

    def test_default_dealer_fields(self):
        """Test default values of price and minimum_quantity."""
        product = self.Product.create({
            'name': 'Standard Product',
            'list_price': 100.0,
        })
        self.assertEqual(
            product.price,
            0.0,
            "Dealer price should default to 0.0."
        )
        self.assertEqual(
            product.minimum_quantity,
            0.0,
            "Dealer's minimum quantity should default to 0.0."
        )

    def test_create_product_with_dealer_pricing(self):
        """Test setting dealer price and minimum quantity on creation."""
        product = self.Product.create({
            'name': 'Bulk Dealer Product',
            'list_price': 100.0,
            'price': 70.0,
            'minimum_quantity': 15.0,
        })
        self.assertEqual(product.price, 70.0)
        self.assertEqual(product.minimum_quantity, 15.0)

    def test_update_dealer_pricing(self):
        """Test updating dealer price and minimum quantity on an existing product."""
        product = self.Product.create({
            'name': 'Editable Dealer Product',
            'list_price': 200.0,
        })
        product.write({
            'price': 150.0,
            'minimum_quantity': 25.0,
        })
        self.assertEqual(product.price, 150.0)
        self.assertEqual(product.minimum_quantity, 25.0)

    def test_product_view_field_label(self):
        """Test that product form view uses 'Dealer Price' and does not override to 'Dealers Price'."""
        view = self.env.ref('customers_dealers_quantity.product_normal_form_view')
        self.assertTrue(view, "View record must exist.")
        self.assertNotIn(
            'string="Dealers Price"',
            view.arch,
            "View arch should not contain string='Dealers Price'."
        )
        self.assertNotIn(
            "string='Dealers Price'",
            view.arch,
            "View arch should not contain string='Dealers Price'."
        )
