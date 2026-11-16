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
#############################################################################
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from odoo.exceptions import AccessDenied
from odoo.http import Response
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.restrict_logins.controllers import session as session_controller
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

        identifier = 'totally-nonexistent-sid-xyz987'[:42]
        mock_store = MagicMock()
        mock_store.get_missing_session_identifiers.return_value = [identifier]

        with patch.object(session_controller, 'session_store', return_value=mock_store):
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

        fake_sid = 'fake-valid-sid-001'
        mock_store = MagicMock()
        mock_store.get_missing_session_identifiers.side_effect = [[], [fake_sid]]

        with patch.object(session_controller, 'session_store', return_value=mock_store):
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

        mock_store.delete_from_identifiers.assert_called_once_with([fake_sid])

    def test_returns_false_when_session_remains_after_delete(self):
        """Return False if the session identifier still exists after deletion."""
        _logger.info(
            "Testing clear_session_history OSError handling"
        )

        fake_sid = 'permission-denied-sid'

        mock_store = MagicMock()
        mock_store.get_missing_session_identifiers.side_effect = [set(), set()]

        with patch.object(session_controller, 'session_store', return_value=mock_store):
            result = clear_session_history(fake_sid)

        self.assertFalse(result)
        mock_store.delete_from_identifiers.assert_called_once_with([fake_sid])


@tagged('post_install', '-at_install')
class TestSuperClearAll(TransactionCase):
    """Tests for the super_clear_all() helper."""

    def test_super_clear_all_returns_true(self):
        """super_clear_all() must always return True."""
        _logger.info(
            "Testing super_clear_all return value"
        )

        mock_store = MagicMock()
        mock_store.path = '/tmp/fake_sessions'

        with patch.object(session_controller, 'session_store', return_value=mock_store), \
             patch.object(session_controller.os, 'walk', return_value=[('/tmp/fake_sessions', [], [])]):

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

        mock_store = MagicMock()
        mock_store.path = '/tmp/fake_sessions'

        walk_result = [('/tmp/fake_sessions', [], ['sess_abc', 'sess_def'])]
        with patch.object(session_controller, 'session_store', return_value=mock_store), \
             patch.object(session_controller.os, 'walk', return_value=walk_result), \
             patch.object(session_controller.os, 'unlink', side_effect=OSError("busy")) as unlink:

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
        self.assertEqual(unlink.call_count, 2)


@tagged('post_install', '-at_install')
class TestSessionControllerLogout(TransactionCase):
    """Tests for session controller logout logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        _logger.info(
            "Setting up TestSessionControllerLogout"
        )

        cls.env['ir.config_parameter'].sudo().set_int(
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

    def _make_mock_request(self, user):
        mock_req = MagicMock()
        mock_req.session.uid = user.id
        mock_req.env = self.env(user=user)
        mock_req.redirect.return_value = Response("redirected", status=303)
        return mock_req

    def test_clear_session_called_on_logout(self):
        """Logout must clear session fields."""
        user = self.test_user.sudo()
        user.write({
            'sid': 'pre-logout-sid',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=30)
        })

        mock_req = self._make_mock_request(user)

        with patch('odoo.addons.restrict_logins.controllers.session.request', mock_req), \
             patch('odoo.addons.restrict_logins.controllers.session.odoo_logout'):
            session_controller.Session().logout()

        self.assertFalse(user.sid)
        self.assertFalse(user.logged_in)
        self.assertFalse(user.exp_date)

    def test_logout_all_clears_specific_user_session(self):
        """logout_all must clear specific user session."""
        user = self.test_user.sudo()
        user.write({
            'sid': 'logout-all-sid',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=30)
        })

        mock_req = self._make_mock_request(user)

        with patch('odoo.addons.restrict_logins.controllers.session.request', mock_req), \
             patch('odoo.addons.restrict_logins.controllers.session.clear_session_history', return_value=True), \
             patch('odoo.addons.restrict_logins.controllers.session.odoo_logout'):
            session_controller.Session().logout_all()

        self.assertFalse(user.logged_in)
        self.assertFalse(user.sid)

    def test_logout_all_unauthorized_raises_access_denied(self):
        """logout_all must raise AccessDenied when attempting to logout other users without admin."""
        user = self.test_user.sudo()
        other_user = self.env['res.users'].create({
            'name': 'Other User',
            'login': 'other_user@test.com',
            'password': 'Test@1234',
        })
        mock_req = self._make_mock_request(user)

        with patch('odoo.addons.restrict_logins.controllers.session.request', mock_req):
            with self.assertRaises(AccessDenied):
                session_controller.Session().logout_all(f_uid=other_user.id)

    def test_super_logout_all_clears_all_users(self):
        """super_logout_all must clear all user sessions when run by admin."""
        admin_user = self.env.ref('base.user_admin')
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

        mock_req = self._make_mock_request(admin_user)

        with patch('odoo.addons.restrict_logins.controllers.session.request', mock_req), \
             patch('odoo.addons.restrict_logins.controllers.session.clear_session_history', return_value=True), \
             patch('odoo.addons.restrict_logins.controllers.session.super_clear_all', return_value=True), \
             patch('odoo.addons.restrict_logins.controllers.session.odoo_logout'):
            session_controller.Session().super_logout_all()

        self.assertFalse(user2.sudo().logged_in)

    def test_super_logout_all_non_admin_raises_access_denied(self):
        """super_logout_all must raise AccessDenied for non-admin users."""
        user = self.test_user.sudo()
        mock_req = self._make_mock_request(user)

        with patch('odoo.addons.restrict_logins.controllers.session.request', mock_req):
            with self.assertRaises(AccessDenied):
                session_controller.Session().super_logout_all()
