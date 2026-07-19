# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase

class TestChatterPosition(TransactionCase):

    def setUp(self):
        super(TestChatterPosition, self).setUp()
        self.user_right = self.env['res.users'].create({
            'name': 'Test User Right',
            'login': 'test_user_right',
            'chatter_position': 'right',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

    def test_default_chatter_position(self):
        """Test that the default chatter position is 'default'."""
        new_user = self.env['res.users'].create({
            'name': 'Test Default User',
            'login': 'test_user_default',
        })
        self.assertEqual(
            new_user.chatter_position, 
            'default', 
            "The default chatter position must be 'default'."
        )

    def test_session_info_chatter_position(self):
        """Test that session_info injects the user's chatter position."""
        # Authenticate as our test user
        self.env = self.env(user=self.user_right)
        
        # Get session info
        session_info = self.env['ir.http'].session_info()
        
        self.assertIn(
            'chatter_position', 
            session_info, 
            "session_info should contain the 'chatter_position' key."
        )
        self.assertEqual(
            session_info['chatter_position'], 
            'right', 
            "session_info should reflect the correct chatter position of the user."
        )

    def test_write_chatter_position(self):
        """Test updating the chatter position for a user."""
        self.user_right.write({'chatter_position': 'bottom'})
        self.assertEqual(
            self.user_right.chatter_position, 
            'bottom', 
            "The user's chatter position should be updated to 'bottom'."
        )

        self.env = self.env(user=self.user_right)
        session_info = self.env['ir.http'].session_info()
        self.assertEqual(
            session_info['chatter_position'], 
            'bottom', 
            "session_info should update when the user changes their chatter position."
        )
