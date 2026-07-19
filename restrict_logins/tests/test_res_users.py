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
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestResUsersFields(TransactionCase):
    """Verify that restrict_logins adds the expected fields to res.users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        _logger.info("Setting up TestResUsersFields")

        cls.user = cls.env['res.users'].create({
            'name': 'Test Restrict User',
            'login': 'restrict_test_user@test.com',
            'password': 'Test@1234',
        })

    def test_sid_field_exists(self):
        """res.users must have a 'sid' Char field."""
        _logger.info("Testing sid field existence")

        self.assertIn(
            'sid',
            self.env['res.users']._fields,
            "'sid' field must exist on res.users"
        )

        field = self.env['res.users']._fields['sid']

        self.assertEqual(
            field.type,
            'char',
            "'sid' must be a Char field"
        )

    def test_exp_date_field_exists(self):
        """res.users must have an 'exp_date' Datetime field."""
        _logger.info("Testing exp_date field existence")

        self.assertIn(
            'exp_date',
            self.env['res.users']._fields,
            "'exp_date' field must exist on res.users"
        )

        field = self.env['res.users']._fields['exp_date']

        self.assertEqual(
            field.type,
            'datetime',
            "'exp_date' must be a Datetime field"
        )

    def test_logged_in_field_exists(self):
        """res.users must have a 'logged_in' Boolean field."""
        _logger.info("Testing logged_in field existence")

        self.assertIn(
            'logged_in',
            self.env['res.users']._fields,
            "'logged_in' field must exist on res.users"
        )

        field = self.env['res.users']._fields['logged_in']

        self.assertEqual(
            field.type,
            'boolean',
            "'logged_in' must be a Boolean field"
        )

    def test_last_update_field_exists(self):
        """res.users must have a 'last_update' Datetime field."""
        _logger.info("Testing last_update field existence")

        self.assertIn(
            'last_update',
            self.env['res.users']._fields,
            "'last_update' field must exist on res.users"
        )

        field = self.env['res.users']._fields['last_update']

        self.assertEqual(
            field.type,
            'datetime',
            "'last_update' must be a Datetime field"
        )

    def test_new_user_session_fields_default_to_falsy(self):
        """Newly created users should have falsy session fields."""
        _logger.info("Testing default session field values for new user")

        self.assertFalse(
            self.user.sid,
            "New user sid should be False/empty"
        )

        self.assertFalse(
            self.user.exp_date,
            "New user exp_date should be False"
        )

        self.assertFalse(
            self.user.logged_in,
            "New user logged_in should be False"
        )


@tagged('post_install', '-at_install')
class TestResUsersClearSession(TransactionCase):
    """Tests for ResUsers._clear_session()."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        _logger.info("Setting up TestResUsersClearSession")

        cls.user = cls.env['res.users'].create({
            'name': 'Session User',
            'login': 'session_user@test.com',
            'password': 'Test@1234',
        })

    def test_clear_session_clears_sid(self):
        """_clear_session() must set sid to False."""
        _logger.info("Testing _clear_session clears sid")

        self.user.write({
            'sid': 'fake-session-id-abc123',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=60)
        })

        self.user._clear_session()

        _logger.info(
            "Session cleared for user: %s",
            self.user.login
        )

        self.assertFalse(
            self.user.sid,
            "sid must be cleared after _clear_session()"
        )

    def test_clear_session_clears_exp_date(self):
        """_clear_session() must set exp_date to False."""
        _logger.info("Testing _clear_session clears exp_date")

        self.user.write({
            'sid': 'fake-session-id-xyz',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=60)
        })

        self.user._clear_session()

        self.assertFalse(
            self.user.exp_date,
            "exp_date must be cleared after _clear_session()"
        )

    def test_clear_session_sets_logged_in_false(self):
        """_clear_session() must set logged_in to False."""
        _logger.info("Testing _clear_session sets logged_in False")

        self.user.write({
            'sid': 'fake-session-id',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=60)
        })

        self.user._clear_session()

        self.assertFalse(
            self.user.logged_in,
            "logged_in must be False after _clear_session()"
        )

    def test_clear_session_sets_last_update(self):
        """_clear_session() must set last_update to approximately now."""
        _logger.info("Testing _clear_session updates last_update")

        before = datetime.now()

        self.user.write({
            'sid': 'fake-session-id',
            'logged_in': True,
            'exp_date': datetime.now() + timedelta(minutes=60)
        })

        self.user._clear_session()

        after = datetime.now()

        self.assertIsNotNone(
            self.user.last_update,
            "last_update must be set by _clear_session()"
        )

        self.assertGreaterEqual(
            self.user.last_update,
            before - timedelta(seconds=5),
            "last_update must be close to now"
        )

        self.assertLessEqual(
            self.user.last_update,
            after + timedelta(seconds=5),
            "last_update must be close to now"
        )

    def test_clear_session_on_already_cleared_user(self):
        """Calling _clear_session() on a user with no session must not crash."""
        _logger.info("Testing _clear_session on already cleared user")

        self.user.write({
            'sid': False,
            'logged_in': False,
            'exp_date': False
        })

        try:
            self.user._clear_session()
            _logger.info(
                "_clear_session executed successfully on cleared user"
            )
        except Exception as exc:
            _logger.error(
                "_clear_session failed: %s",
                exc
            )
            self.fail(
                "_clear_session() raised an exception on clean user: %s"
                % exc
            )


@tagged('post_install', '-at_install')
class TestResUsersSaveSession(TransactionCase):
    """Tests for ResUsers._save_session()."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        _logger.info("Setting up TestResUsersSaveSession")

        cls.user = cls.env['res.users'].create({
            'name': 'Save Session User',
            'login': 'save_session@test.com',
            'password': 'Test@1234',
        })

        cls.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time',
            '60'
        )

    def _mock_request_sid(self, sid='test-sid-001'):
        """Return a mock request whose session.sid equals sid."""
        mock_req = MagicMock()
        mock_req.session.sid = sid
        return mock_req

    def test_save_session_sets_sid(self):
        """_save_session() must write the sid."""
        _logger.info("Testing _save_session sets sid")

        fake_sid = 'fake-sid-save-001'

        with patch(
            'odoo.addons.restrict_logins.models.res_users.request',
            self._mock_request_sid(fake_sid)
        ):
            self.user._save_session()

        _logger.info(
            "Session saved with sid: %s",
            fake_sid
        )

        self.assertEqual(
            self.user.sudo().sid,
            fake_sid,
            "sid must match request.session.sid after _save_session()"
        )

    def test_save_session_sets_logged_in_true(self):
        """_save_session() must set logged_in=True."""
        _logger.info("Testing _save_session sets logged_in=True")

        with patch(
            'odoo.addons.restrict_logins.models.res_users.request',
            self._mock_request_sid('sid-logged-in-test')
        ):
            self.user._save_session()

        _logger.info(
            "logged_in value after save session: %s",
            self.user.logged_in
        )

        self.assertTrue(
            self.user.sudo().logged_in,
            "logged_in must be True after _save_session()"
        )

    def test_save_session_sets_exp_date_in_future(self):
        """_save_session() must set exp_date to future datetime."""
        _logger.info("Testing _save_session sets future exp_date")

        before = datetime.utcnow()

        with patch(
            'odoo.addons.restrict_logins.models.res_users.request',
            self._mock_request_sid('sid-exp-date-test')
        ):
            self.user._save_session()

        self.assertIsNotNone(
            self.user.sudo().exp_date,
            "exp_date must be set after _save_session()"
        )

        self.assertGreater(
            self.user.sudo().exp_date,
            before,
            "exp_date must be in the future after _save_session()"
        )

    def test_save_session_respects_session_expire_time(self):
        """exp_date must respect configured session expire time."""
        _logger.info("Testing session expiration time configuration")

        expire_minutes = 30

        self.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time',
            str(expire_minutes)
        )

        before = datetime.utcnow()

        with patch(
            'odoo.addons.restrict_logins.models.res_users.request',
            self._mock_request_sid('sid-expire-time-test')
        ):
            self.user._save_session()

        exp = self.user.sudo().exp_date

        expected_min = before + timedelta(minutes=expire_minutes - 1)
        expected_max = datetime.utcnow() + timedelta(
            minutes=expire_minutes + 1
        )

        self.assertGreater(
            exp,
            expected_min,
            "exp_date must be at least now + expire_time"
        )

        self.assertLess(
            exp,
            expected_max,
            "exp_date must not exceed expected range"
        )


@tagged('post_install', '-at_install')
class TestResUsersValidateSessions(TransactionCase):
    """Tests for ResUsers._validate_sessions()."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        _logger.info("Setting up TestResUsersValidateSessions")

        cls.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time',
            '60'
        )

    def _create_session_user(self, name, login, sid, exp_date):
        """Helper method to create session users."""
        _logger.info("Creating session user: %s", login)

        user = self.env['res.users'].create({
            'name': name,
            'login': login,
            'password': 'Test@1234',
        })

        user.sudo().write({
            'sid': sid,
            'exp_date': exp_date,
            'logged_in': True,
        })

        return user

    def test_validate_sessions_clears_expired_user(self):
        """Expired users must have sessions cleared."""
        _logger.info("Testing validation of expired sessions")

        expired_user = self._create_session_user(
            'Expired User',
            'expired_user@test.com',
            'expired-sid-001',
            datetime.utcnow() - timedelta(minutes=10),
        )

        clear_path = (
            'odoo.addons.restrict_logins.models.res_users'
            '.clear_session_history'
        )

        with patch(clear_path, return_value=True):
            self.env['res.users']._validate_sessions()

        _logger.info(
            "Expired session cleared for user: %s",
            expired_user.login
        )

        self.assertFalse(
            expired_user.sudo().logged_in,
            "logged_in must be False after validation"
        )

        self.assertFalse(
            expired_user.sudo().sid,
            "sid must be cleared after validation"
        )

        self.assertFalse(
            expired_user.sudo().exp_date,
            "exp_date must be cleared after validation"
        )

    def test_validate_sessions_does_not_clear_active_user(self):
        """Active users must keep their session."""
        _logger.info("Testing validation does not clear active users")

        active_user = self._create_session_user(
            'Active User',
            'active_user_validate@test.com',
            'active-sid-002',
            datetime.utcnow() + timedelta(minutes=30),
        )

        clear_path = (
            'odoo.addons.restrict_logins.models.res_users'
            '.clear_session_history'
        )

        with patch(clear_path, return_value=True):
            self.env['res.users']._validate_sessions()

        _logger.info(
            "Active session retained for user: %s",
            active_user.login
        )

        self.assertTrue(
            active_user.sudo().logged_in,
            "Active user session should NOT be cleared"
        )

        self.assertEqual(
            active_user.sudo().sid,
            'active-sid-002',
            "Active user sid must remain unchanged"
        )

    def test_validate_sessions_handles_clear_failure(self):
        """User session must remain if session file removal fails."""
        _logger.info("Testing failed session clear handling")

        expired_user = self._create_session_user(
            'Failed Clear User',
            'failed_clear@test.com',
            'expired-sid-fail',
            datetime.utcnow() - timedelta(minutes=5),
        )

        clear_path = (
            'odoo.addons.restrict_logins.models.res_users'
            '.clear_session_history'
        )

        with patch(clear_path, return_value=False):
            self.env['res.users']._validate_sessions()

        _logger.info(
            "Session clear failure handled for user: %s",
            expired_user.login
        )

        self.assertTrue(
            expired_user.sudo().logged_in,
            "logged_in must remain True when file clear failed"
        )

        self.assertEqual(
            expired_user.sudo().sid,
            'expired-sid-fail',
            "sid must remain when file clear failed"
        )
