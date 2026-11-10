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
from unittest.mock import patch
from odoo.tests import TransactionCase


class TestProductTemplateWishlist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env['product.template']
        cls.Wishlist = cls.env['product.wishlist']
        cls.Website = cls.env['website']

        cls.website = cls.Website.search([], limit=1)

    def _create_wishlist(self, variant):
        return self.Wishlist.create({
            'product_id': variant.id,
            'website_id': self.website.id,
        })

    def test_is_in_wishlist_empty_recordset(self):
        """Test empty product template recordset."""
        product = self.ProductTemplate.browse()

        self.assertFalse(product._is_in_wishlist())

    def test_is_in_wishlist_with_wishlist(self):
        """Test product template available in wishlist."""
        product = self.ProductTemplate.create({
            'name': 'Test Product',
        })

        wishlist = self._create_wishlist(product.product_variant_id)

        with patch.object(
            type(self.Wishlist), 'current', return_value=wishlist
        ):
            self.assertTrue(product._is_in_wishlist())

    def test_is_in_wishlist_without_wishlist(self):
        """Test product template not available in wishlist."""
        product = self.ProductTemplate.create({
            'name': 'Test Product',
        })

        with patch.object(
            type(self.Wishlist),
            'current',
            return_value=self.Wishlist.browse(),
        ):
            self.assertFalse(product._is_in_wishlist())

    def test_is_in_wishlist_multiple_variants(self):
        """Test template when one of its variants is in wishlist."""
        attribute = self.env['product.attribute'].create({
            'name': 'Test Color',
            'value_ids': [
                (0, 0, {'name': 'Red'}),
                (0, 0, {'name': 'Blue'}),
            ],
        })

        product = self.ProductTemplate.create({
            'name': 'Test Product',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attribute.id,
                    'value_ids': [(6, 0, attribute.value_ids.ids)],
                }),
            ],
        })

        variant = product.product_variant_ids[-1]
        wishlist = self._create_wishlist(variant)

        with patch.object(
            type(self.Wishlist), 'current', return_value=wishlist
        ):
            self.assertTrue(product._is_in_wishlist())