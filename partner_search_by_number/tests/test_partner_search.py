# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPartnerSearchByNumber(TransactionCase):
    """Test suite for partner search by phone number functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']

        cls.partner_alpha = cls.Partner.create({
            'name': 'Alpha Customer',
            'phone': '+1 555-0101',
            'email': 'alpha@example.com',
            'ref': 'CUST_ALPHA_001',
            'vat': 'US111222333',
        })
        cls.partner_beta = cls.Partner.create({
            'name': 'Beta Vendor',
            'phone': '+1 555-0202',
            'email': 'beta@example.com',
            'ref': 'CUST_BETA_002',
            'vat': 'US444555666',
        })
        cls.partner_gamma = cls.Partner.create({
            'name': 'Gamma Contact',
            'phone': False,
            'email': 'gamma@example.com',
            'ref': 'CUST_GAMMA_003',
        })

    def test_search_display_name_domain_structure(self):
        """Test that _search_display_name returns expected domain with phone field."""
        operator = 'ilike'
        value = '555-0101'
        expected_domain = [
            '|', '|', '|', '|',
            ('complete_name', operator, value),
            ('email', operator, value),
            ('ref', operator, value),
            ('vat', operator, value),
            ('phone', operator, value),
        ]
        computed_domain = self.Partner._search_display_name(operator, value)
        self.assertEqual(
            computed_domain,
            expected_domain,
            "Domain returned by _search_display_name must include phone and standard search fields.",
        )

    def test_search_display_name_different_operator(self):
        """Test _search_display_name domain generation with '=' operator."""
        operator = '='
        value = '+1 555-0101'
        expected_domain = [
            '|', '|', '|', '|',
            ('complete_name', operator, value),
            ('email', operator, value),
            ('ref', operator, value),
            ('vat', operator, value),
            ('phone', operator, value),
        ]
        computed_domain = self.Partner._search_display_name(operator, value)
        self.assertEqual(
            computed_domain,
            expected_domain,
            "Domain returned by _search_display_name must correctly incorporate the provided operator.",
        )

    def test_name_search_by_exact_phone(self):
        """Test finding a partner by exact phone number using name_search."""
        results = self.Partner.name_search('+1 555-0101')
        result_ids = [res[0] for res in results]
        self.assertIn(
            self.partner_alpha.id,
            result_ids,
            "Partner Alpha should be found when searching by its exact phone number.",
        )
        self.assertNotIn(
            self.partner_beta.id,
            result_ids,
            "Partner Beta should not be found when searching for Partner Alpha's phone number.",
        )

    def test_name_search_by_partial_phone(self):
        """Test finding a partner by partial phone number using name_search."""
        results = self.Partner.name_search('0101')
        result_ids = [res[0] for res in results]
        self.assertIn(
            self.partner_alpha.id,
            result_ids,
            "Partner Alpha should be found when searching by partial phone number.",
        )
        self.assertNotIn(
            self.partner_beta.id,
            result_ids,
            "Partner Beta should not match a distinct partial number.",
        )

    def test_name_search_multiple_matches_by_phone(self):
        """Test searching with a common phone prefix matches both partners."""
        results = self.Partner.name_search('555-')
        result_ids = [res[0] for res in results]
        self.assertIn(
            self.partner_alpha.id,
            result_ids,
            "Partner Alpha should be found when searching by shared phone prefix.",
        )
        self.assertIn(
            self.partner_beta.id,
            result_ids,
            "Partner Beta should be found when searching by shared phone prefix.",
        )
        self.assertNotIn(
            self.partner_gamma.id,
            result_ids,
            "Partner Gamma without a phone number should not match the phone prefix.",
        )

    def test_name_search_non_matching_phone(self):
        """Test that searching with a non-matching phone number returns no unexpected partners."""
        results = self.Partner.name_search('999-9999')
        result_ids = [res[0] for res in results]
        self.assertNotIn(
            self.partner_alpha.id,
            result_ids,
            "Partner Alpha should not match an unrelated phone number.",
        )
        self.assertNotIn(
            self.partner_beta.id,
            result_ids,
            "Partner Beta should not match an unrelated phone number.",
        )

    def test_orm_search_by_display_name_phone(self):
        """Test ORM search on display_name field using phone number."""
        partners = self.Partner.search([('display_name', 'ilike', '+1 555-0101')])
        self.assertIn(
            self.partner_alpha,
            partners,
            "Partner Alpha should be found when filtering display_name by phone number.",
        )
        self.assertNotIn(
            self.partner_beta,
            partners,
            "Partner Beta should not be in the search results for Partner Alpha's phone.",
        )

    def test_standard_name_search_preserved(self):
        """Test that standard search by complete_name still works."""
        results = self.Partner.name_search('Alpha Customer')
        result_ids = [res[0] for res in results]
        self.assertIn(
            self.partner_alpha.id,
            result_ids,
            "Partner Alpha should still be found when searching by complete_name.",
        )

    def test_standard_email_search_preserved(self):
        """Test that standard search by email still works."""
        results = self.Partner.name_search('alpha@example.com')
        result_ids = [res[0] for res in results]
        self.assertIn(
            self.partner_alpha.id,
            result_ids,
            "Partner Alpha should still be found when searching by email.",
        )

    def test_standard_ref_search_preserved(self):
        """Test that standard search by reference still works."""
        results = self.Partner.name_search('CUST_ALPHA_001')
        result_ids = [res[0] for res in results]
        self.assertIn(
            self.partner_alpha.id,
            result_ids,
            "Partner Alpha should still be found when searching by ref.",
        )

    def test_standard_vat_search_preserved(self):
        """Test that standard search by VAT still works."""
        results = self.Partner.name_search('US111222333')
        result_ids = [res[0] for res in results]
        self.assertIn(
            self.partner_alpha.id,
            result_ids,
            "Partner Alpha should still be found when searching by VAT.",
        )

