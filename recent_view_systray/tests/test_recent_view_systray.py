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

from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError

class TestRecentViewSystray(TransactionCase):

    def setUp(self):
        super(TestRecentViewSystray, self).setUp()
        
        # Create a standard internal user
        self.test_user = self.env['res.users'].create({
            'name': 'Test Normal User',
            'login': 'test_recent_view_user',
            'email': 'test_user@example.com',
        })
        self.env.ref('base.group_user').users = [(4, self.test_user.id)]

    def test_01_default_history_limit(self):
        """Test if the default history limit is set to 15"""
        self.assertEqual(self.test_user.history_limit, 15, "Default history limit should be 15.")

    def test_02_session_info_history_limit(self):
        """Test if the session_info returns the correct history limit for the user"""
        self.test_user.history_limit = 20
        
        # Call session_info in the environment of the test user
        # Note: IrHttp is an abstract model, so we can access it through self.env
        session_info = self.env['ir.http'].with_user(self.test_user).session_info()
        
        # Check if the limit is added directly to the session_info result
        self.assertEqual(session_info.get('history_limit'), 20, 
                         "session_info should contain the history_limit of the user.")
        
        # Check if the limit is added to the user_context
        if 'user_context' in session_info:
            self.assertEqual(session_info['user_context'].get('history_limit'), 20, 
                             "session_info['user_context'] should contain the history_limit.")

    def test_03_admin_can_write_history_limit(self):
        """Test that an admin can write to the history_limit field"""
        admin_user = self.env.ref('base.user_admin')
        self.test_user.with_user(admin_user).write({'history_limit': 10})
        self.assertEqual(self.test_user.history_limit, 10, "Admin should be able to update history limit.")

    def test_04_session_info_fallback(self):
        """Test session_info fallback mechanism when history limit is zero or not set"""
        self.test_user.history_limit = 0
        session_info = self.env['ir.http'].with_user(self.test_user).session_info()
        
        # Our code does `limit = self.env.user.history_limit or 15`
        # So if it's 0, it should fallback to 15
        self.assertEqual(session_info.get('history_limit'), 15, 
                         "session_info should fallback to 15 if history_limit is 0 or falsey.")
