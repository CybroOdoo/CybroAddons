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
from datetime import timedelta

import pytz

from odoo import api, fields, models, SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request

from ..utils import clear_session_history

_logger = logging.getLogger(__name__)

DEFAULT_SESSION_EXPIRE_MINUTES = 10


class AlreadyLoggedIn(AccessDenied):
    """Raised when a user with an active session logs in again."""

    KEY = 'already_logged_in'

    def __init__(self):
        super().__init__(self.KEY)


class ResUsers(models.Model):
    """Adds the session tracking fields to 'res.users'."""
    _inherit = 'res.users'

    sid = fields.Char(string='Session ID', help="ID of session", copy=False)
    exp_date = fields.Datetime(
        string='Current Session Expiration', copy=False,
        help="Time of expiring of current session")
    logged_in = fields.Boolean(
        copy=False, help="User is currently logged in")
    last_update = fields.Datetime(
        string="Last Connection", copy=False, help="Last log in")

    @api.model
    def _get_session_expire_minutes(self):
        """Return the configured session duration in minutes."""
        value = self.env['ir.config_parameter'].sudo().get_param(
            'restrict_logins.session_expire_time')
        try:
            minutes = int(value)
        except (TypeError, ValueError):
            return DEFAULT_SESSION_EXPIRE_MINUTES
        return minutes if minutes > 0 else DEFAULT_SESSION_EXPIRE_MINUTES

    @classmethod
    def _login(cls, db, credential, user_agent_env):
        """Authenticate the user and refuse the login when the account
        already has an active session."""
        login = credential['login']
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                with self._assert_can_auth(user=login):
                    user = self.search(self._get_login_domain(login),
                                       order=self._get_login_order(), limit=1)
                    if not user:
                        raise AccessDenied()
                    user = user.with_user(user)
                    auth_info = user._check_credentials(
                        credential, user_agent_env)
                    tz = request.cookies.get('tz') if request else None
                    if tz in pytz.all_timezones and (
                            not user.tz or not user.login_date):
                        user.tz = tz
                    if user.exp_date and user.sid and user.logged_in:
                        _logger.warning(
                            "User %s is already logged in. Multiple "
                            "sessions are not allowed.", user.name)
                        raise AlreadyLoggedIn()
                    if request:
                        user._save_session()
                    user._update_last_login()
        except AccessDenied:
            _logger.info("Login failed for db:%s login:%s from %s", db, login,
                         ip)
            raise
        _logger.info("Login successful for db:%s login:%s from %s", db, login,
                     ip)
        return auth_info

    @api.model
    def _check_password_login(self, login, password):
        """Return the user matching the login and password.

        :raise AccessDenied: when the credentials are wrong.
        """
        users = self.sudo()
        with users._assert_can_auth(user=login):
            user = users.search(users._get_login_domain(login),
                                order=users._get_login_order(), limit=1)
            if not user:
                raise AccessDenied()
            user.with_user(user)._check_credentials(
                {'login': login, 'password': password, 'type': 'password'},
                {'interactive': True})
        return user

    def _clear_session(self):
        """Clear the session details of the users."""
        self.write({
            'sid': False,
            'exp_date': False,
            'logged_in': False,
            'last_update': fields.Datetime.now(),
        })

    def _save_session(self):
        """Save the session details of the current request on the user."""
        exp_date = fields.Datetime.now() + timedelta(
            minutes=self._get_session_expire_minutes())
        self.with_user(SUPERUSER_ID).write({
            'sid': request.session.sid,
            'exp_date': exp_date,
            'logged_in': True,
            'last_update': fields.Datetime.now(),
        })

    @api.model
    def _validate_sessions(self):
        """Cron: clear the sessions that have expired."""
        users = self.search([('exp_date', '!=', False),
                             ('exp_date', '<', fields.Datetime.now())])
        for user in users:
            if clear_session_history(user.sid):
                user._clear_session()
                _logger.info("Cron _validate_session: cleared session of "
                             "user: %s", user.name)
            else:
                _logger.info("Cron _validate_session: failed to clear "
                             "session of user: %s", user.name)
