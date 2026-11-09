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
"""Unit tests for the product.pricelist model in uom_in_pricelist."""

from odoo import Command
from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestProductPricelist(TransactionCase):
    """Test cases for product.pricelist model functions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit_uom = cls.env.ref('uom.product_uom_unit')
        cls.dozen_uom = cls.env.ref('uom.product_uom_dozen')

        cls.product = cls.env['product.product'].create({
            'name': 'Pricelist Test Product',
            'list_price': 10.0,
            'uom_id': cls.unit_uom.id,
            'taxes_id': [Command.clear()],
        })

        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test UoM Pricelist',
        })

        # Rule 1: Specific to Dozen UoM on the product with fixed price 90.0 per unit (1080.0 per dozen)
        cls.rule_dozen = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'compute_price': 'fixed',
            'fixed_price': 90.0,
            'product_uom_id': cls.dozen_uom.id,
        })

        # Rule 2: Generic fallback rule on global scope without UoM restriction with fixed price 10.0
        cls.rule_generic = cls.env['product.pricelist.item'].create({
            'pricelist_id': cls.pricelist.id,
            'applied_on': '3_global',
            'compute_price': 'fixed',
            'fixed_price': 10.0,
            'product_uom_id': False,
        })

    def test__get_applicable_rules_domain(self):
        """Test _get_applicable_rules_domain filters rules based on product_uom_id."""
        # 1. When uom is specified (dozen_uom), domain matches rules with product_uom_id == False or dozen_uom
        domain_dozen = self.pricelist._get_applicable_rules_domain(
            self.product, uom=self.dozen_uom
        )
        matching_rules_dozen = self.env['product.pricelist.item'].search(domain_dozen)
        self.assertIn(self.rule_dozen, matching_rules_dozen)
        self.assertIn(self.rule_generic, matching_rules_dozen)

        # Create a rule specifically for Units to verify exclusion when searching for Dozen
        rule_unit_specific = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '1_product',
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'compute_price': 'fixed',
            'fixed_price': 8.0,
            'product_uom_id': self.unit_uom.id,
        })
        matching_rules_dozen_after = self.env['product.pricelist.item'].search(domain_dozen)
        self.assertNotIn(rule_unit_specific, matching_rules_dozen_after)

        # 2. When uom is None, domain does not add product_uom_id constraint
        domain_no_uom = self.pricelist._get_applicable_rules_domain(self.product)
        matching_rules_no_uom = self.env['product.pricelist.item'].search(domain_no_uom)
        self.assertIn(self.rule_generic, matching_rules_no_uom)

    def test__compute_price_rule(self):
        """Test _compute_price_rule resolves price rule respecting uom keyword and positional args."""
        # 1. Calling with uom=dozen_uom matches rule_dozen (90.0 per unit * 12 = 1080.0)
        res_dozen = self.pricelist._compute_price_rule(
            self.product, quantity=1.0, uom=self.dozen_uom
        )
        price_dozen, rule_id_dozen = res_dozen[self.product.id]
        self.assertEqual(rule_id_dozen, self.rule_dozen.id)
        self.assertEqual(price_dozen, 1080.0)

        # 2. Calling with uom=unit_uom skips rule_dozen and falls back to rule_generic (fixed price 10.0)
        res_unit = self.pricelist._compute_price_rule(
            self.product, quantity=1.0, uom=self.unit_uom
        )
        price_unit, rule_id_unit = res_unit[self.product.id]
        self.assertEqual(rule_id_unit, self.rule_generic.id)
        self.assertEqual(price_unit, 10.0)

        # 3. Calling with legacy positional arguments (*args: currency, uom, date, compute_price)
        res_positional = self.pricelist._compute_price_rule(
            self.product, 1.0, None, self.dozen_uom, False, True
        )
        price_pos, rule_id_pos = res_positional[self.product.id]
        self.assertEqual(rule_id_pos, self.rule_dozen.id)
        self.assertEqual(price_pos, 1080.0)
