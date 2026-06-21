# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby(<https://www.cybrosys.com>)
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
from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user

@tagged('post_install', '-at_install')
class TestRestrictWebDebug(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test user
        cls.test_user = new_test_user(cls.env, login='test_restrict_debug', groups='base.group_user', password='password')
        cls.restrict_group = cls.env.ref('restrict_web_debug.restrict_debug_mode')

    def test_session_info_without_group(self):
        """Test session info when user does not have the restrict_debug_mode group."""
        # Ensure user does not have the group
        self.test_user.write({'group_ids': [(3, self.restrict_group.id)]})
        
        self.authenticate('test_restrict_debug', 'password')
        response = self.make_jsonrpc_request('/web/session/get_session_info', {})
        
        # Verify the 'user_group' in session_info
        self.assertIn('user_group', response)
        # JSON converts tuples to lists
        self.assertEqual(response['user_group'], [False])

    def test_session_info_with_group(self):
        """Test session info when user has the restrict_debug_mode group."""
        # Add the group to the user
        self.test_user.write({'group_ids': [(4, self.restrict_group.id)]})
        
        self.authenticate('test_restrict_debug', 'password')
        response = self.make_jsonrpc_request('/web/session/get_session_info', {})
        
        # Verify the 'user_group' in session_info
        self.assertIn('user_group', response)
        # JSON converts tuples to lists
        self.assertEqual(response['user_group'], [True])
