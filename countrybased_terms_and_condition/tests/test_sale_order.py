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
class TestCountryBasedTermsSaleOrder(TransactionCase):
    """Test cases for country-based terms and conditions on sale.order."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_us = cls.env['res.country'].create({
            'name': 'United States Test',
            'code': 'UT',
            'sale_terms_condition': '<p>US Country Sale Terms and Conditions</p>',
        })
        cls.country_no_terms = cls.env['res.country'].create({
            'name': 'Canada Test',
            'code': 'CT',
            'sale_terms_condition': False,
        })
        cls.partner_us = cls.env['res.partner'].create({
            'name': 'US Customer',
            'country_id': cls.country_us.id,
        })
        cls.partner_no_terms = cls.env['res.partner'].create({
            'name': 'Canada Customer',
            'country_id': cls.country_no_terms.id,
        })
        cls.partner_no_country = cls.env['res.partner'].create({
            'name': 'No Country Customer',
            'country_id': False,
        })

    def test_sale_order_note_with_country_terms(self):
        """Test that sale order note is populated with partner country terms."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner_us.id,
        })
        order._compute_note()
        self.assertEqual(order.note, '<p>US Country Sale Terms and Conditions</p>')

    def test_sale_order_note_without_country_terms(self):
        """Test that sale order note is not set to country terms when country has no terms."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner_no_terms.id,
        })
        order._compute_note()
        self.assertNotEqual(order.note, '<p>US Country Sale Terms and Conditions</p>')

    def test_sale_order_note_partner_without_country(self):
        """Test that sale order note handles partner without a country."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner_no_country.id,
        })
        order._compute_note()
        self.assertNotEqual(order.note, '<p>US Country Sale Terms and Conditions</p>')

    def test_sale_order_multi_recordset_compute_note(self):
        """Test that _compute_note operates correctly on multi-recordsets."""
        order1 = self.env['sale.order'].create({
            'partner_id': self.partner_us.id,
        })
        order2 = self.env['sale.order'].create({
            'partner_id': self.partner_no_terms.id,
        })
        orders = order1 | order2
        res = orders._compute_note()
        self.assertIsNone(res)
        self.assertEqual(order1.note, '<p>US Country Sale Terms and Conditions</p>')
        self.assertNotEqual(order2.note, '<p>US Country Sale Terms and Conditions</p>')

    def test_sale_order_note_not_overwritten_when_confirmed(self):
        """Test confirmed sale orders do not have note overwritten on recompute."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner_no_terms.id,
            'note': '<p>Existing Custom Note</p>',
        })
        order.state = 'sale'
        order.partner_id = self.partner_us
        order._compute_note()
        self.assertEqual(order.note, '<p>Existing Custom Note</p>')

    def test_sale_order_country_terms_change_does_not_affect_confirmed(self):
        """Test changing country terms does not alter note on existing confirmed order."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner_us.id,
            'note': '<p>Original Order Terms</p>',
        })
        order.state = 'sale'
        self.country_us.write({'sale_terms_condition': '<p>Brand New Terms</p>'})
        order._compute_note()
        self.assertEqual(order.note, '<p>Original Order Terms</p>')

    def test_sale_order_empty_html_terms(self):
        """Test country with empty HTML terms does not overwrite note."""
        country_empty_html = self.env['res.country'].create({
            'name': 'Empty HTML Country',
            'code': 'XC',
            'sale_terms_condition': '<p><br></p>',
        })
        partner = self.env['res.partner'].create({
            'name': 'Empty HTML Partner',
            'country_id': country_empty_html.id,
        })
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        order._compute_note()
        self.assertNotEqual(order.note, '<p><br></p>')
        self.assertNotEqual(order.note, '<p>US Country Sale Terms and Conditions</p>')

    def test_sale_order_partner_change_updates_draft_note(self):
        """Test changing partner on a draft quotation updates terms."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner_no_terms.id,
        })
        order._compute_note()
        self.assertNotEqual(order.note, '<p>US Country Sale Terms and Conditions</p>')
        order.partner_id = self.partner_us
        order._compute_note()
        self.assertEqual(order.note, '<p>US Country Sale Terms and Conditions</p>')

