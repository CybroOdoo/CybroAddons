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
from odoo.fields import Command
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPricelistPriceOnProduct(TransactionCase):
    """ Test suite for the Pricelist Price on Product module in Odoo 20.
    Verifies that only pricelists with 'display_pricelist = True' appear on the
    product's Prices tab (fixed_pricelist_rule_ids). """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test product template
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Acoustic Bloc Screen',
            'list_price': 500.0,
        })

        # 1. Pricelist with display_pricelist enabled
        cls.pricelist_displayed = cls.env['product.pricelist'].create({
            'name': 'Default (USD)',
            'display_pricelist': True,
            'item_ids': [
                Command.create({
                    'applied_on': '1_product',
                    'compute_price': 'fixed',
                    'product_tmpl_id': cls.product_tmpl.id,
                    'fixed_price': 450.0,
                }),
            ],
        })

        # 2. Pricelist with display_pricelist disabled
        cls.pricelist_hidden = cls.env['product.pricelist'].create({
            'name': 'USD Retails (USD)',
            'display_pricelist': False,
            'item_ids': [
                Command.create({
                    'applied_on': '1_product',
                    'compute_price': 'fixed',
                    'product_tmpl_id': cls.product_tmpl.id,
                    'fixed_price': 100.0,
                }),
            ],
        })

    def test_01_displayed_and_hidden_pricelists(self):
        """ Verify that only pricelists with display_pricelist=True appear in
        fixed_pricelist_rule_ids on the product template. """
        rules = self.product_tmpl.fixed_pricelist_rule_ids
        pricelists = rules.mapped('pricelist_id')

        # Enabled pricelist should appear in the Prices tab
        self.assertIn(
            self.pricelist_displayed,
            pricelists,
            "Pricelist with display_pricelist=True should appear in the Prices tab.",
        )

        # Disabled pricelist should NOT appear in the Prices tab
        self.assertNotIn(
            self.pricelist_hidden,
            pricelists,
            "Pricelist with display_pricelist=False should NOT appear in the Prices tab.",
        )

    def test_02_toggle_display_pricelist(self):
        """ Verify that toggling 'display_pricelist' dynamically displays or
        hides the pricelist line on the product template. """
        # Create a pricelist initially hidden (display_pricelist=False)
        pricelist_toggle = self.env['product.pricelist'].create({
            'name': 'Toggle Pricelist',
            'display_pricelist': False,
            'item_ids': [
                Command.create({
                    'applied_on': '1_product',
                    'compute_price': 'fixed',
                    'product_tmpl_id': self.product_tmpl.id,
                    'fixed_price': 300.0,
                }),
            ],
        })

        # Initially hidden
        self.product_tmpl.invalidate_recordset(['fixed_pricelist_rule_ids'])
        self.assertNotIn(
            pricelist_toggle,
            self.product_tmpl.fixed_pricelist_rule_ids.mapped('pricelist_id'),
            "Pricelist should be hidden while display_pricelist is False.",
        )

        # Toggle to True -> should appear
        pricelist_toggle.write({'display_pricelist': True})
        self.product_tmpl.invalidate_recordset(['fixed_pricelist_rule_ids'])
        self.assertIn(
            pricelist_toggle,
            self.product_tmpl.fixed_pricelist_rule_ids.mapped('pricelist_id'),
            "Pricelist should appear after enabling display_pricelist.",
        )

        # Toggle back to False -> should disappear
        pricelist_toggle.write({'display_pricelist': False})
        self.product_tmpl.invalidate_recordset(['fixed_pricelist_rule_ids'])
        self.assertNotIn(
            pricelist_toggle,
            self.product_tmpl.fixed_pricelist_rule_ids.mapped('pricelist_id'),
            "Pricelist should disappear after disabling display_pricelist.",
        )

    def test_03_default_display_pricelist_value(self):
        """ Ensure that newly created pricelists have display_pricelist=False by default. """
        new_pricelist = self.env['product.pricelist'].create({
            'name': 'New Standard Pricelist',
        })
        self.assertFalse(
            new_pricelist.display_pricelist,
            "Default value of display_pricelist should be False.",
        )

    def test_04_multiple_products_filtering(self):
        """ Verify that the filtering applies consistently across multiple products. """
        product_tmpl_2 = self.env['product.template'].create({
            'name': 'Second Test Product',
            'list_price': 300.0,
        })

        # Add rules for the second product to both pricelists
        self.env['product.pricelist.item'].create([
            {
                'pricelist_id': self.pricelist_displayed.id,
                'product_tmpl_id': product_tmpl_2.id,
                'applied_on': '1_product',
                'compute_price': 'fixed',
                'fixed_price': 250.0,
            },
            {
                'pricelist_id': self.pricelist_hidden.id,
                'product_tmpl_id': product_tmpl_2.id,
                'applied_on': '1_product',
                'compute_price': 'fixed',
                'fixed_price': 80.0,
            },
        ])

        product_tmpl_2.invalidate_recordset(['fixed_pricelist_rule_ids'])
        pricelists = product_tmpl_2.fixed_pricelist_rule_ids.mapped('pricelist_id')

        self.assertIn(
            self.pricelist_displayed,
            pricelists,
            "Displayed pricelist should appear on second product.",
        )
        self.assertNotIn(
            self.pricelist_hidden,
            pricelists,
            "Hidden pricelist should not appear on second product.",
        )
