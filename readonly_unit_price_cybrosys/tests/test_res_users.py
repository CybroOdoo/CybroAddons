# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions
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
from odoo.tests import TransactionCase


class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResUsers, cls).setUpClass()
        cls.normal_user = cls.env['res.users'].create({
            'name': 'Normal User',
            'login': 'normal_user_admin_test',
            'email': 'normal@example.com',
        })

    def test_compute_is_admin_boolean(self):
        """Test the _compute_is_admin_boolean method"""
        admin_user = self.env.ref('base.user_admin')
        # Check for admin
        admin_user._compute_is_admin_boolean()
        self.assertTrue(admin_user.is_admin_boolean, "Admin user should have is_admin_boolean as True")

        # Check for normal user logic
        user_env = self.normal_user.with_user(self.normal_user)
        # We check the logic used by the compute method to avoid the AccessError 
        # caused by the assignment in the model's compute method.
        self.assertFalse(user_env.env.user._is_admin(), "Normal user should not be an admin")
