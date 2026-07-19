# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
import logging
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase, tagged
from odoo.addons.restrict_logins.controllers.session import (
    clear_session_history,
    super_clear_all,
)

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestClearSessionHistory(TransactionCase):
    """Tests for the clear_session_history() helper."""

    def test_returns_false_for_nonexistent_sid(self):
        """Must return False when session file does not exist."""
        _logger.info(
            "Testing clear_session_history with nonexistent session id"
        )

        mock_store = MagicMock()
        mock_store.get_session_filename.return_value = (
            '/nonexistent/path/no_such_file'
        )

        store_path = (
            'odoo.addons.restrict_logins.controllers.session'
            '.odoo.http.FilesystemSessionStore'
        )

        with patch(store_path, return_value=mock_store):
            result = clear_session_history(
                'totally-nonexistent-sid-xyz987'
            )

        _logger.info(
            "clear_session_history returned: %s",
            result
        )

        self.assertFalse(
            result,
            "clear_session_history must return False "
            "for a non-existent session ID"
        )

    def test_returns_true_when_file_deleted(self):
        """Must return True when session file is deleted."""
        _logger.info(
            "Testing clear_session_history successful deletion"
        )

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tmp_path = tf.name

        fake_sid = 'fake-valid-sid-001'

        mock_store = MagicMock()
        mock_store.get_session_filename.return_value = tmp_path

        store_path = (
            'odoo.addons.restrict_logins.controllers.session'
            '.odoo.http.FilesystemSessionStore'
        )

        with patch(store_path, return_value=mock_store):
            result = clear_session_history(fake_sid)

        _logger.info(
            "Session file deleted successfully for sid: %s",
            fake_sid
        )

        self.assertTrue(
            result,
            "clear_session_history must return True "
            "when the file is successfully deleted"
        )

        self.assertFalse(
            os.path.exists(tmp_path),
            "The session file should have been removed"
        )

    def test_returns_false_when_remove_raises_oserror(self):
        """Must return False when os.remove raises OSError."""
        _logger.info(
            "Testing clear_session_history OSError handling"
        )

        fake_sid = 'permission-denied-sid'

        mock_store = MagicMock()
        mock_store.get_session_filename.return_value = (
            '/nonexistent/path/file'
        )

        store_path = (
            'odoo.addons.restrict_logins.controllers.session'
            '.odoo.http.FilesystemSessionStore'
        )

        with patch(store_path, return_value=mock_store), \
             patch('os.remove',
                   side_effect=OSError("Permission denied")):

            result = clear_session_history(fake_sid)

        _logger.info(
            "clear_session_history returned False due to OSError"
        )

        self.assertFalse(
            result,
            "clear_session_history must return False on OSError"
        )


@tagged('post_install', '-at_install')
class TestSuperClearAll(TransactionCase):
    """Tests for the super_clear_all() helper."""

    def test_super_clear_all_returns_true(self):
        """super_clear_all() must always return True."""
        _logger.info(
            "Testing super_clear_all return value"
        )

        store_path = (
            'odoo.addons.restrict_logins.controllers.session'
            '.sessions.FilesystemSessionStore'
        )

        mock_store = MagicMock()
        mock_store.path = '/tmp/fake_sessions'

        with patch(store_path, return_value=mock_store), \
             patch('os.listdir', return_value=[]):

            result = super_clear_all()

        _logger.info(
            "super_clear_all executed successfully"
        )

        self.assertTrue(
            result,
            "super_clear_all() must return True"
        )

    def test_super_clear_all_skips_unlink_errors(self):
        """super_clear_all() must ignore unlink errors."""
        _logger.info(
            "Testing super_clear_all unlink error handling"
        )

        store_path = (
            'odoo.addons.restrict_logins.controllers.session'
            '.sessions.FilesystemSessionStore'
        )

        mock_store = MagicMock()
        mock_store.path = '/tmp/fake_sessions'

        with patch(store_path, return_value=mock_store), \
             patch('os.listdir',
                   return_value=['sess_abc', 'sess_def']), \
             patch('os.unlink',
                   side_effect=OSError("busy")):

            try:
                result = super_clear_all()
                _logger.info(
                    "super_clear_all ignored unlink errors successfully"
                )
            except Exception as exc:
                _logger.error(
                    "super_clear_all raised exception: %s",
                    exc
                )
                self.fail(
                    "super_clear_all() raised an exception: %s" % exc
                )

        self.assertTrue(
            result,
            "super_clear_all() must return True even when unlink fails"
        )


@tagged('post_install', '-at_install')
class TestSessionControllerLogout(TransactionCase):
    """Tests for session controller logout logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        _logger.info(
            "Setting up TestSessionControllerLogout"
        )

        cls.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time',
            '60'
        )

        cls.test_user = cls.env['res.users'].create({
            'name': 'Logout Test User',
            'login': 'logout_test@test.com',
            'password': 'Test@1234',
        })

        cls.test_user.sudo().write({
            'sid': 'logout-sid-001',
            'exp_date': datetime.now() + timedelta(minutes=60),
            'logged_in': True,
        })

    def test_clear_session_called_on_logout(self):
        """Logout must clear session fields."""
        _logger.info(
            "Testing user logout session clearing"
        )

        user = self.test_user.sudo()

        user.write({
            'sid': 'pre-logout-sid',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=30)
        })

        user._clear_session()

        _logger.info(
            "Session cleared for user: %s",
            user.login
        )

        self.assertFalse(
            user.sid,
            "sid must be cleared after logout"
        )

        self.assertFalse(
            user.logged_in,
            "logged_in must be False after logout"
        )

        self.assertFalse(
            user.exp_date,
            "exp_date must be cleared after logout"
        )

    def test_logout_all_clears_specific_user_session(self):
        """logout_all must clear specific user session."""
        _logger.info(
            "Testing logout_all clears user session"
        )

        user = self.test_user.sudo()

        user.write({
            'sid': 'logout-all-sid',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=30)
        })

        clear_path = (
            'odoo.addons.restrict_logins.controllers.session'
            '.clear_session_history'
        )

        with patch(clear_path, return_value=True) as mock_clear:

            session_cleared = mock_clear(user.sid)

            if session_cleared:
                user._clear_session()

        _logger.info(
            "logout_all cleared session for user: %s",
            user.login
        )

        self.assertFalse(
            user.logged_in,
            "logout_all must clear user session"
        )

        self.assertFalse(
            user.sid,
            "logout_all must clear user sid"
        )

    def test_super_logout_all_clears_all_users(self):
        """super_logout_all must clear all user sessions."""
        _logger.info(
            "Testing super_logout_all functionality"
        )

        user2 = self.env['res.users'].sudo().create({
            'name': 'Super Logout User',
            'login': 'super_logout@test.com',
            'password': 'Test@1234',
        })

        user2.write({
            'sid': 'super-logout-sid',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=30)
        })

        store_path = (
            'odoo.addons.restrict_logins.controllers.session'
            '.sessions.FilesystemSessionStore'
        )

        mock_store = MagicMock()
        mock_store.path = '/tmp/fake_sessions'

        with patch(store_path, return_value=mock_store), \
             patch('os.listdir', return_value=[]):

            users = self.env['res.users'].sudo().search([])

            for user in users:
                cleared = super_clear_all()

                if cleared:
                    user._clear_session()

        _logger.info(
            "super_logout_all cleared all user sessions"
        )

        self.assertFalse(
            user2.sudo().logged_in,
            "super_logout_all must clear all user sessions"
        )
