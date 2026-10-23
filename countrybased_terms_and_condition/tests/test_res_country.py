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
##############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCountryBasedTermsResCountry(TransactionCase):
    """Test cases for country-based terms and conditions on res.country."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env['res.country'].create({
            'name': 'Test Country Terms',
            'code': 'XA',
            'sale_terms_condition': '<p>Sample Terms &amp; Conditions</p>',
        })

    def test_res_country_sale_terms_condition_create(self):
        """Test creating a country record with terms and conditions."""
        self.assertEqual(
            self.country.sale_terms_condition,
            '<p>Sample Terms &amp; Conditions</p>'
        )

    def test_res_country_sale_terms_condition_write(self):
        """Test updating terms and conditions on an existing country."""
        self.country.write({
            'sale_terms_condition': '<p>Updated Country Terms</p>'
        })
        self.assertEqual(
            self.country.sale_terms_condition,
            '<p>Updated Country Terms</p>'
        )

    def test_res_country_sale_terms_condition_empty(self):
        """Test country record without terms and conditions."""
        country_empty = self.env['res.country'].create({
            'name': 'Empty Country',
            'code': 'XB',
        })
        self.assertFalse(country_empty.sale_terms_condition)
