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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Test suite for gender_contact module."""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestGenderContact(TransactionCase):
    """Test gender field behavior and search filters on res.partner."""

    @classmethod
    def setUpClass(cls):
        """Set up test records for contacts with different genders."""
        super().setUpClass()
        cls.partner_male = cls.env['res.partner'].create({
            'name': 'John Doe',
            'gender': 'male',
        })
        cls.partner_female = cls.env['res.partner'].create({
            'name': 'Jane Doe',
            'gender': 'female',
        })
        cls.partner_other = cls.env['res.partner'].create({
            'name': 'Alex Smith',
            'gender': 'other',
        })
        cls.partner_none = cls.env['res.partner'].create({
            'name': 'Unspecified Partner',
        })

    def test_01_gender_values(self):
        """Verify that gender field accepts and stores correct values."""
        self.assertEqual(self.partner_male.gender, 'male')
        self.assertEqual(self.partner_female.gender, 'female')
        self.assertEqual(self.partner_other.gender, 'other')
        self.assertFalse(self.partner_none.gender)

    def test_02_gender_update(self):
        """Verify that gender field can be updated or cleared."""
        partner = self.partner_male
        partner.write({'gender': 'female'})
        self.assertEqual(partner.gender, 'female')
        partner.write({'gender': False})
        self.assertFalse(partner.gender)

    def test_03_gender_search_filters(self):
        """Verify search filters matching the search view definitions."""
        male_contacts = self.env['res.partner'].search([('gender', '=', 'male')])
        self.assertIn(self.partner_male, male_contacts)
        self.assertNotIn(self.partner_female, male_contacts)

        female_contacts = self.env['res.partner'].search([('gender', '=', 'female')])
        self.assertIn(self.partner_female, female_contacts)
        self.assertNotIn(self.partner_male, female_contacts)

        other_contacts = self.env['res.partner'].search([('gender', '=', 'other')])
        self.assertIn(self.partner_other, other_contacts)
        self.assertNotIn(self.partner_male, other_contacts)

    def test_04_gender_read_group(self):
        """Verify grouping contacts by gender works as expected."""
        groups = self.env['res.partner'].read_group(
            domain=[('id', 'in', [
                self.partner_male.id,
                self.partner_female.id,
                self.partner_other.id,
                self.partner_none.id,
            ])],
            groupby=['gender'],
            aggregates=['__count'],
        )
        grouped_genders = {g[0] for g in groups}
        self.assertIn('male', grouped_genders)
        self.assertIn('female', grouped_genders)
        self.assertIn('other', grouped_genders)

    def test_05_views_rendering(self):
        """Verify inherited views render properly."""
        form_view = self.env.ref('gender_contact.view_partner_form')
        search_view = self.env.ref('gender_contact.view_res_partner_filter')
        res_form = self.env['res.partner'].get_view(view_id=form_view.id, view_type='form')
        self.assertTrue(res_form)
        self.assertIn('gender', res_form['arch'])
        res_search = self.env['res.partner'].get_view(view_id=search_view.id, view_type='search')
        self.assertTrue(res_search)
        self.assertIn('gender_male', res_search['arch'])
        self.assertIn('group_by_gender', res_search['arch'])

    def test_06_access_rights(self):
        """Verify standard internal users can create and read contacts with gender."""
        user = self.env.ref('base.user_demo', raise_if_not_found=False)
        if not user:
            group_field = (
                'group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'
            )
            user = self.env['res.users'].create({
                'name': 'Test User',
                'login': 'test_user_gender',
                group_field: [(6, 0, [self.env.ref('base.group_user').id])],
            })
        partner_as_user = self.env['res.partner'].with_user(user).create({
            'name': 'User Created Partner',
            'gender': 'female',
        })
        self.assertEqual(partner_as_user.gender, 'female')
