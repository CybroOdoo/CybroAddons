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
import odoo.http
from unittest.mock import MagicMock, patch
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestIrHttp(TransactionCase):
    """Test ir.http model extensions for recent_view_systray."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Http = cls.env['ir.http']

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.session.uid = self.env.user.id
        self.mock_request.cookies = {}
        odoo.http._request_stack.push(self.mock_request)

    def tearDown(self):
        odoo.http._request_stack.pop()
        super().tearDown()

    def test_session_info_default_limit(self):
        """Test session_info returns default history_limit when not set."""
        self.env.user.history_limit = 0
        
        result = self.Http.session_info()
        
        self.assertEqual(result.get('history_limit'), 15)
        if 'user_context' in result:
            self.assertEqual(result['user_context'].get('history_limit'), 15)

    def test_session_info_custom_limit(self):
        """Test session_info returns user's custom history_limit."""
        self.env.user.history_limit = 25
        
        result = self.Http.session_info()
        
        self.assertEqual(result.get('history_limit'), 25)
        if 'user_context' in result:
            self.assertEqual(result['user_context'].get('history_limit'), 25)

    @patch('odoo.sql_db.Cursor.savepoint')
    def test_session_info_exception(self, mock_savepoint):
        """Test session_info falls back to 15 if an exception occurs."""
        mock_savepoint.side_effect = Exception("Mock Database Error")
        
        result = self.Http.session_info()
        
        self.assertEqual(result.get('history_limit'), 15)
