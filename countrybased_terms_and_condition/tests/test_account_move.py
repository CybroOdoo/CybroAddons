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
class TestCountryBasedTermsAccountMove(TransactionCase):
    """Test cases for country-based terms and conditions on account.move."""

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
            'name': 'US Partner',
            'country_id': cls.country_us.id,
        })
        cls.partner_no_terms = cls.env['res.partner'].create({
            'name': 'Canada Partner',
            'country_id': cls.country_no_terms.id,
        })
        cls.partner_no_country = cls.env['res.partner'].create({
            'name': 'No Country Partner',
            'country_id': False,
        })

    def test_out_invoice_with_country_terms(self):
        """Test that customer invoice narration gets country sale terms."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_us.id,
        })
        move._compute_narration()
        self.assertEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_out_refund_with_country_terms(self):
        """Test that customer credit note narration gets country sale terms."""
        move = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner_us.id,
        })
        move._compute_narration()
        self.assertEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_out_invoice_without_country_terms(self):
        """Test customer invoice when country has no custom terms."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_no_terms.id,
        })
        move._compute_narration()
        self.assertNotEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_out_invoice_partner_without_country(self):
        """Test customer invoice when partner has no country."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_no_country.id,
        })
        move._compute_narration()
        self.assertNotEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_vendor_bill_does_not_get_customer_terms(self):
        """Test vendor bill does not get customer sale terms even if vendor country has terms."""
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_us.id,
        })
        move._compute_narration()
        self.assertNotEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_journal_entry_does_not_get_customer_terms(self):
        """Test journal entry does not get customer sale terms."""
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'partner_id': self.partner_us.id,
        })
        move._compute_narration()
        self.assertNotEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_multi_recordset_compute_narration(self):
        """Test _compute_narration on multi-recordsets with mixed move types."""
        out_invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_us.id,
        })
        in_invoice = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner_us.id,
        })
        moves = out_invoice | in_invoice
        res = moves._compute_narration()
        self.assertIsNone(res)
        self.assertEqual(out_invoice.narration, '<p>US Country Sale Terms and Conditions</p>')
        self.assertNotEqual(in_invoice.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_posted_invoice_does_not_get_country_terms(self):
        """Test posted invoice does not receive country terms on compute."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_no_terms.id,
        })
        move.state = 'posted'
        move._compute_narration()
        self.assertNotEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_account_move_country_terms_change_does_not_affect_posted(self):
        """Test changing country terms does not alter narration on existing posted invoice."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_us.id,
            'narration': '<p>Original Invoice Narration</p>',
        })
        move.state = 'posted'
        self.country_us.write({'sale_terms_condition': '<p>Brand New Terms</p>'})
        self.assertEqual(move.narration, '<p>Original Invoice Narration</p>')
        self.assertNotEqual(move.narration, '<p>Brand New Terms</p>')

    def test_account_move_empty_html_terms(self):
        """Test country with empty HTML terms does not overwrite narration."""
        country_empty_html = self.env['res.country'].create({
            'name': 'Empty HTML Country Account',
            'code': 'XD',
            'sale_terms_condition': '<p><br></p>',
        })
        partner = self.env['res.partner'].create({
            'name': 'Empty HTML Partner Account',
            'country_id': country_empty_html.id,
        })
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
        })
        move._compute_narration()
        self.assertNotEqual(move.narration, '<p><br></p>')
        self.assertNotEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')

    def test_account_move_partner_change_updates_draft_narration(self):
        """Test changing partner on draft invoice updates narration to new partner terms."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_no_terms.id,
        })
        move._compute_narration()
        self.assertNotEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')
        move.partner_id = self.partner_us
        move._compute_narration()
        self.assertEqual(move.narration, '<p>US Country Sale Terms and Conditions</p>')



