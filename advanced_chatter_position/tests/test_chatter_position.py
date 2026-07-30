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
from unittest.mock import MagicMock, patch
import odoo


class TestChatterPosition(TransactionCase):
    """Test cases for the advanced_chatter_position module."""

    def setUp(self):
        super(TestChatterPosition, self).setUp()
        self.user_test = self.env['res.users'].create({
            'name': 'Test User Chatter',
            'login': 'test_user_chatter',
            'email': 'test_chatter@example.com',
            'chatter_position': 'bottom',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })

    def test_chatter_position_field(self):
        """Test if the chatter_position field is correctly stored."""
        self.assertEqual(self.user_test.chatter_position, 'bottom',
                         "Chatter position should be 'bottom'")
        self.user_test.chatter_position = 'right'
        self.assertEqual(self.user_test.chatter_position, 'right',
                         "Chatter position should be updated to 'right'")

    def test_session_info(self):
        """Test if session_info includes the correct chatter_position."""
        # Create a dummy request object to be pushed to Odoo's request stack.
        # This is the most robust way to mock Odoo's request in a TransactionCase,
        # as it satisfies all modules that access odoo.http.request.
        class DummyRequest:
            def __init__(self, user, env):
                self.session = MagicMock()
                self.session.uid = user.id
                self.session.context = {'lang': 'en_US'}
                self.session.debug = False
                self.session.profile_session = False
                self.session.profile_collectors = []
                self.session.profile_params = {}
                self.env = env
                self.registry = env.registry
                self.db = env.cr.dbname
                self.httprequest = MagicMock()
                self.httprequest.args = {}
                self.httprequest.user_agent.string = "Mozilla/5.0"
                self.future_response = MagicMock()

        dummy = DummyRequest(self.user_test, self.env)

        # Patch requests.get globally to avoid BlockedRequest from other modules 
        # (e.g. export_delete_login_log) during authentication/login if they are triggered.
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {'ip': '127.0.0.1'}
            mock_get.return_value.status_code = 200

            # Push the dummy request to the stack
            odoo.http._request_stack.push(dummy)
            try:
                # Call session_info via ir.http as the test user
                session_info = self.env['ir.http'].with_user(self.user_test).session_info()

                # Verify our additions to session_info
                self.assertIn('chatter_position', session_info,
                              "chatter_position should be in session_info")
                self.assertEqual(session_info['chatter_position'], 'bottom',
                                 "chatter_position in session_info should match user preference")

                # Verify user_context additions
                self.assertIn('user_context', session_info,
                              "user_context should be in session_info")
                self.assertEqual(session_info['user_context'].get('chatter_position'), 'bottom',
                                 "chatter_position should be in user_context")

                # Test default/other value
                self.user_test.chatter_position = 'right'
                session_info_right = self.env['ir.http'].with_user(self.user_test).session_info()
                self.assertEqual(session_info_right['chatter_position'], 'right',
                                 "Should return 'right' if position is set to right")
            finally:
                # Always pop from stack
                odoo.http._request_stack.pop()
