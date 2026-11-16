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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import MagicMock, patch

from odoo import Command
from odoo.addons.recent_view_systray.models.ir_http import IrHttp as RecentIrHttp
from odoo.http import request_var
from odoo.tests.common import TransactionCase


class TestRecentViewSystray(TransactionCase):
    """Unit tests for Recent View Systray module models and methods."""

    def setUp(self):
        super().setUp()

        # Create a standard internal user
        self.test_user = self.env['res.users'].create({
            'name': 'Test Normal User',
            'login': 'test_recent_view_user',
            'email': 'test_user@example.com',
            'group_ids': [Command.link(self.env.ref('base.group_user').id)],
        })

        mock_req = MagicMock()
        mock_req.session.uid = self.test_user.id
        mock_req.session.context = {}
        mock_req.session.get.return_value = False
        mock_req.cookies = {}
        token = request_var.set(mock_req)
        self.addCleanup(request_var.reset, token)

    def test_01_default_history_limit(self):
        """Test if the default history limit is set to 15."""
        self.assertEqual(
            self.test_user.history_limit,
            15,
            "Default history limit should be 15.",
        )

    def test_02_session_info_history_limit(self):
        """Test if session_info returns the correct history limit for user."""
        self.test_user.history_limit = 20

        # Call session_info in the environment of the test user
        session_info = self.env['ir.http'].with_user(
            self.test_user
        ).session_info()

        # Check if the limit is added directly to the session_info result
        self.assertEqual(
            session_info.get('history_limit'),
            20,
            "session_info should contain the history_limit of the user.",
        )

        # Check if the limit is added to the user_context
        if 'user_context' in session_info:
            self.assertEqual(
                session_info['user_context'].get('history_limit'),
                20,
                "session_info['user_context'] should contain history_limit.",
            )

    def test_03_admin_can_write_history_limit(self):
        """Test that an admin can write to the history_limit field."""
        admin_user = self.env.ref('base.user_admin')
        self.test_user.with_user(admin_user).write({'history_limit': 10})
        self.assertEqual(
            self.test_user.history_limit,
            10,
            "Admin should be able to update history limit.",
        )

    def test_04_session_info_fallback(self):
        """Test session_info fallback mechanism when history limit is zero."""
        self.test_user.history_limit = 0
        session_info = self.env['ir.http'].with_user(
            self.test_user
        ).session_info()

        # Fallback to 15 when limit is 0 or falsey
        self.assertEqual(
            session_info.get('history_limit'),
            15,
            "session_info should fallback to 15 if history_limit is 0.",
        )
        if 'user_context' in session_info:
            self.assertEqual(
                session_info['user_context'].get('history_limit'),
                15,
                "session_info['user_context'] should fallback to 15.",
            )

    def test_05_session_info_exception_fallback(self):
        """Test session_info fallback mechanism when an exception occurs."""
        with patch.object(
            self.env.cr, 'savepoint', side_effect=Exception("Database error")
        ):
            session_info = self.env['ir.http'].with_user(
                self.test_user
            ).session_info()
            self.assertEqual(
                session_info.get('history_limit'),
                15,
                "session_info should fallback to 15 when an exception occurs.",
            )

    def test_06_session_info_negative_limit_fallback(self):
        """Test session_info fallback when history limit is negative."""
        self.test_user.history_limit = -5
        session_info = self.env['ir.http'].with_user(
            self.test_user
        ).session_info()

        self.assertEqual(
            session_info.get('history_limit'),
            15,
            "session_info should fallback to 15 if history_limit is negative.",
        )
        if 'user_context' in session_info:
            self.assertEqual(
                session_info['user_context'].get('history_limit'),
                15,
                "session_info['user_context'] should fallback to 15 for negative limits.",
            )

    def test_07_update_history_limit_lower_then_higher(self):
        """Test lowering and then raising history_limit reflects in session_info."""
        admin_user = self.env.ref('base.user_admin')
        self.test_user.with_user(admin_user).write({'history_limit': 2})
        low_session = self.env['ir.http'].with_user(
            self.test_user
        ).session_info()
        self.assertEqual(low_session.get('history_limit'), 2)
        if 'user_context' in low_session:
            self.assertEqual(low_session['user_context'].get('history_limit'), 2)

        self.test_user.with_user(admin_user).write({'history_limit': 25})
        high_session = self.env['ir.http'].with_user(
            self.test_user
        ).session_info()
        self.assertEqual(high_session.get('history_limit'), 25)
        if 'user_context' in high_session:
            self.assertEqual(high_session['user_context'].get('history_limit'), 25)

    def test_08_user_can_read_own_history_limit(self):
        """Test a standard internal user can read their own history_limit."""
        self.test_user.history_limit = 8
        data = self.test_user.with_user(self.test_user).read(['history_limit'])
        self.assertEqual(
            data[0].get('history_limit'),
            8,
            "Standard user should be able to read their own history_limit.",
        )

    def test_09_session_info_without_user_context(self):
        """Test session_info when super result has no user_context key."""
        self.test_user.history_limit = 12
        ir_http = self.env['ir.http'].with_user(self.test_user)
        mro = type(ir_http).mro()
        next_cls = next(
            cls for cls in mro[mro.index(RecentIrHttp) + 1:]
            if 'session_info' in cls.__dict__
        )
        with patch.object(next_cls, 'session_info', return_value={}):
            session_info = RecentIrHttp.session_info(ir_http)
        self.assertEqual(session_info, {'history_limit': 12})
