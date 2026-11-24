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
from odoo.tests import tagged

from odoo.addons.website_sale.tests.common import MockRequest, WebsiteSaleCommon


@tagged('post_install', '-at_install')
class TestNutivoData(WebsiteSaleCommon):
    """Test the website and product helpers used by the Nutivo templates."""

    @classmethod
    def setUpClass(cls):
        """Put the test product in a top level shop category."""
        super().setUpClass()
        cls.category = cls.env['product.public.category'].create({
            'name': 'Nutivo Test Dates',
        })
        cls.template = cls.product.product_tmpl_id
        cls.template.public_categ_ids = cls.category

    def test_price_whole_amount(self):
        """Whole amounts drop the decimals and the space."""
        currency = self.env['res.currency'].sudo().create({
            'name': 'NTV', 'symbol': 'N$', 'position': 'before',
            'rounding': 0.01,
        })
        self.assertEqual(
            self.website._nutivo_price(1399.0, currency), 'N$1,399')

    def test_price_with_decimals(self):
        """Other amounts keep the decimals of the currency."""
        currency = self.env['res.currency'].sudo().create({
            'name': 'NTD', 'symbol': 'N$', 'position': 'before',
            'rounding': 0.01,
        })
        self.assertEqual(
            self.website._nutivo_price(1458.849, currency), 'N$1,458.85')

    def test_free_shipping_amount(self):
        """The threshold comes from a system parameter, never below 0."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_float('theme_nutivo.free_shipping_amount', 500)
        self.assertEqual(self.website._nutivo_free_shipping_amount(), 500.0)
        params.set_float('theme_nutivo.free_shipping_amount', -5)
        self.assertEqual(self.website._nutivo_free_shipping_amount(), 0.0)

    def test_categories(self):
        """A category with a published product is listed with its link."""
        entries = {
            entry['name']: entry
            for entry in self.website._nutivo_categories()
        }
        self.assertIn('Nutivo Test Dates', entries)
        entry = entries['Nutivo Test Dates']
        self.assertEqual(entry['url'], self.category.website_url)
        self.assertEqual(entry['count'], 1)
        self.assertIn(self.template.name, entry['description'])

    def test_card_values(self):
        """A product card gives its sizes, origin and notes."""
        with MockRequest(self.env, website=self.website) as request:
            values = request.env['product.template'].browse(
                self.template.id)._nutivo_card_values()
        self.assertEqual(values['origin'], 'Nutivo Test Dates')
        self.assertTrue(values['sizes'])
        self.assertEqual(
            values['sizes'][0]['product_id'], self.product.id)
