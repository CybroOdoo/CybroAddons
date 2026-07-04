# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestResUsersViber(TransactionCase):
    """Test the res.users override for Viber Integration."""

    def setUp(self):
        super(TestResUsersViber, self).setUp()
        self.user_model = self.env['res.users']
        
        # Create some test users with phone numbers
        self.test_user_1 = self.user_model.create({
            'name': 'Viber Test User 1',
            'login': 'viber_test_user_1',
            'phone': '+1234567890',
        })
        self.test_user_2 = self.user_model.create({
            'name': 'Viber Test User 2',
            'login': 'viber_test_user_2',
            'phone': '+0987654321',
        })

    def test_get_users(self):
        """Test getting the users list correctly formats the dictionary."""
        result = self.user_model.get_users()
        
        # Verify the structure has 'users'
        self.assertIn('users', result)
        self.assertIsInstance(result['users'], list)
        
        users_list = result['users']
        
        # Check if our created test users are returned in the response
        user_1_found = False
        user_2_found = False
        
        for user_data in users_list:
            if user_data.get('id') == self.test_user_1.id:
                user_1_found = True
                self.assertEqual(user_data.get('name'), 'Viber Test User 1')
                self.assertEqual(user_data.get('phone'), '+1234567890')
            elif user_data.get('id') == self.test_user_2.id:
                user_2_found = True
                self.assertEqual(user_data.get('name'), 'Viber Test User 2')
                self.assertEqual(user_data.get('phone'), '+0987654321')
                
        self.assertTrue(user_1_found, "Test User 1 was not returned by get_users()")
        self.assertTrue(user_2_found, "Test User 2 was not returned by get_users()")
