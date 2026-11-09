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
"""Unit tests for the product.pricelist.item model in uom_in_pricelist."""

from odoo import Command
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestProductPricelistItem(TransactionCase):
    """Test cases for product.pricelist.item model functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit_uom = cls.env.ref('uom.product_uom_unit')
        cls.dozen_uom = cls.env.ref('uom.product_uom_dozen')

        cls.product = cls.env['product.product'].create({
            'name': 'Pricelist Item Test Product',
            'list_price': 15.0,
            'uom_id': cls.unit_uom.id,
            'taxes_id': [Command.clear()],
        })

        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test Item Pricelist',
        })

    def test__compute_product_uom_id(self):
        """Test _compute_product_uom_id assigns default UoM and preserves custom UoM."""
        # 1. On creation with product_tmpl_id, product_uom_id defaults to product template's UoM
        item = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'compute_price': 'fixed',
            'fixed_price': 20.0,
        })
        self.assertEqual(item.product_uom_id, self.unit_uom)

        # 2. When user sets a custom UoM (e.g. Dozen), recompute preserves it
        item.product_uom_id = self.dozen_uom
        item._compute_product_uom_id()
        self.assertEqual(item.product_uom_id, self.dozen_uom)

        # 3. When product_tmpl_id is cleared (global or category rule), product_uom_id is reset to False
        item.product_tmpl_id = False
        item._compute_product_uom_id()
        self.assertFalse(item.product_uom_id)

    def test__is_applicable_for(self):
        """Test _is_applicable_for checks UoM compatibility via keyword and positional args."""
        # 1. Rule restricted to Dozen UoM
        item_dozen = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'compute_price': 'fixed',
            'fixed_price': 100.0,
            'product_uom_id': self.dozen_uom.id,
        })

        # Applicable when uom is Dozen (keyword argument)
        self.assertTrue(item_dozen._is_applicable_for(self.product, 1.0, uom=self.dozen_uom))
        # Not applicable when uom is Units (keyword argument)
        self.assertFalse(item_dozen._is_applicable_for(self.product, 1.0, uom=self.unit_uom))

        # Positional uom parameter support
        self.assertTrue(item_dozen._is_applicable_for(self.product, 1.0, self.dozen_uom))
        self.assertFalse(item_dozen._is_applicable_for(self.product, 1.0, self.unit_uom))

        # 2. Rule with no UoM restriction (product_uom_id is False)
        item_generic = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'compute_price': 'fixed',
            'fixed_price': 15.0,
            'product_uom_id': False,
        })

        # Applicable for any UoM
        self.assertTrue(item_generic._is_applicable_for(self.product, 1.0, uom=self.unit_uom))
        self.assertTrue(item_generic._is_applicable_for(self.product, 1.0, uom=self.dozen_uom))
