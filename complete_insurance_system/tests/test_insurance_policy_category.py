# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo.tests.common import TransactionCase


class TestInsurancePolicyCategory(TransactionCase):
    """Test cases for the insurance.policy.category model.

    Covers field creation, required field validation, update, delete, and search.
    """

    def setUp(self):
        super().setUp()

    def test_create_policy_category(self):
        """A policy category must be creatable with name and code."""
        cat = self.env['insurance.policy.category'].create(
            {'name': 'Travel', 'code': 'TRV'})
        self.assertTrue(cat.id,
                        "Policy category should be created successfully.")
        self.assertEqual(cat.name, 'Travel')
        self.assertEqual(cat.code, 'TRV')


    def test_policy_category_name_required(self):
        """Creating a policy category without a name must raise an error."""
        with self.assertRaises(Exception):
            self.env['insurance.policy.category'].create(
                {'name': False, 'code': 'XXX'})


    def test_policy_category_code_required(self):
        """Creating a policy category without a code must raise an error."""
        with self.assertRaises(Exception):
            self.env['insurance.policy.category'].create(
                {'name': 'Home', 'code': False})


    def test_policy_category_update(self):
        """A policy category must be updatable."""
        cat = self.env['insurance.policy.category'].create(
            {'name': 'Old Category', 'code': 'OLD'})
        cat.write({'name': 'New Category', 'code': 'NEW'})
        self.assertEqual(cat.name, 'New Category')
        self.assertEqual(cat.code, 'NEW')


    def test_policy_category_delete(self):
        """A policy category must be deletable when not referenced."""
        cat = self.env['insurance.policy.category'].create(
            {'name': 'Temp Cat', 'code': 'TMP'})
        cat_id = cat.id
        cat.unlink()
        self.assertFalse(
            self.env['insurance.policy.category'].search(
                [('id', '=', cat_id)]),
            "Policy category should be deleted.")


    def test_policy_category_search_by_code(self):
        """Search by code must return the correct category."""
        self.env['insurance.policy.category'].create(
            {'name': 'Marine', 'code': 'MRN'})
        results = self.env['insurance.policy.category'].search(
            [('code', '=', 'MRN')])
        self.assertEqual(len(results), 1,
                         "Should find exactly one category with code 'MRN'.")
        self.assertEqual(results.name, 'Marine')


    def test_multiple_categories_created(self):
        """Multiple distinct categories must be storable."""
        codes = ['A1', 'B2', 'C3']
        for code in codes:
            self.env['insurance.policy.category'].create(
                {'name': f'Category {code}', 'code': code})
        count = self.env['insurance.policy.category'].search_count(
            [('code', 'in', codes)])
        self.assertEqual(count, len(codes),
                         "All categories should be stored.")

