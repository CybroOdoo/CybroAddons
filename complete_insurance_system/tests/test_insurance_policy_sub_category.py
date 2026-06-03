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

class TestInsurancePolicySubCategory(TransactionCase):
    """Test cases for the insurance.policy.sub.category model.

    Covers:
    - Record creation with parent category link
    - Required field validation
    - Update and delete operations
    - Search by name and category
    """

    def setUp(self):
        super().setUp()
        self.parent_category = self.env[
            'insurance.policy.category'].create(
            {'name': 'Automobile', 'code': 'AUTO'})

    def test_create_sub_category(self):
        """A sub-category must be creatable with a name and parent category."""
        sub = self.env['insurance.policy.sub.category'].create({
            'name': 'Four-Wheeler',
            'category_id': self.parent_category.id,
        })
        self.assertTrue(sub.id,
                        "Sub-category should be created successfully.")
        self.assertEqual(sub.name, 'Four-Wheeler')
        self.assertEqual(sub.category_id.id, self.parent_category.id)


    def test_sub_category_name_required(self):
        """Creating a sub-category without a name must raise an error."""
        with self.assertRaises(Exception):
            self.env['insurance.policy.sub.category'].create({
                'name': False,
                'category_id': self.parent_category.id,
            })


    def test_sub_category_category_required(self):
        """Creating a sub-category without a parent category must raise an error."""
        with self.assertRaises(Exception):
            self.env['insurance.policy.sub.category'].create({
                'name': 'Orphan Sub',
                'category_id': False,
            })


    def test_sub_category_update(self):
        """A sub-category must support name updates."""
        sub = self.env['insurance.policy.sub.category'].create({
            'name': 'Old Sub',
            'category_id': self.parent_category.id,
        })
        sub.write({'name': 'Updated Sub'})
        self.assertEqual(sub.name, 'Updated Sub',
                         "Sub-category name should be updated.")


    def test_sub_category_delete(self):
        """A sub-category must be deletable when not referenced by a policy."""
        sub = self.env['insurance.policy.sub.category'].create({
            'name': 'Temp Sub',
            'category_id': self.parent_category.id,
        })
        sub_id = sub.id
        sub.unlink()
        self.assertFalse(
            self.env['insurance.policy.sub.category'].search(
                [('id', '=', sub_id)]),
            "Sub-category should be deleted.")


    def test_sub_category_search_by_parent(self):
        """Searching by parent category must return correct sub-categories."""
        self.env['insurance.policy.sub.category'].create({
            'name': 'SUV',
            'category_id': self.parent_category.id,
        })
        self.env['insurance.policy.sub.category'].create({
            'name': 'Sedan',
            'category_id': self.parent_category.id,
        })
        results = self.env['insurance.policy.sub.category'].search(
            [('category_id', '=', self.parent_category.id)])
        self.assertGreaterEqual(len(results), 2,
                                "Should find at least 2 sub-categories under Automobile.")

