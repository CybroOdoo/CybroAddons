# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import logging
from datetime import datetime, timedelta
import pytz
from odoo import SUPERUSER_ID
from odoo import api, fields, models
from odoo.exceptions import AccessDenied
from odoo.http import request
from ..controllers.restrict_logins import clear_session_history

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """ Inheriting 'res.users' for adding fields related session."""
    _inherit = 'res.users'

    sid = fields.Char(string='Session ID', help="ID of session")
    exp_date = fields.Datetime(string='Current Session Expiration',
                               help="Time of expiring of current session")
    logged_in = fields.Boolean(string='Logged In',
                               help="User is currently logged in")
    last_update = fields.Datetime(string="Last Connection",
                                  help="Last log in")

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        """
        Handles user login authentication.
        Notify user if they are already logged in and attempt to log in from
        other device.
        """
        if not password:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                with self._assert_can_auth():
                    user = self.search(self._get_login_domain(login),
                                       order=self._get_login_order(), limit=1)
                    if not user:
                        raise AccessDenied()
                    user = user.with_user(user)
                    user._check_credentials(password, user_agent_env)
                    tz = request.httprequest.cookies.get(
                        'tz') if request else None
                    if tz in pytz.all_timezones and (
                            not user.tz or not user.login_date):
                        user.tz = tz
                    # Check sid and exp date
                    if user.exp_date and user.sid and user.logged_in:
                        _logger.warning("User %s is already logged in "
                                        "into the system!. Multiple "
                                        "sessions are not allowed for "
                                        "security reasons!" % user.name)
                        request.uid = user.id
                        raise AccessDenied("already_logged_in")
                    # Save user session detail if login is successful
                    user._save_session()
                    user._update_last_login()
        except AccessDenied:
            _logger.info("Login failed for db:%s login:%s from %s", db, login,
                         ip)
            raise
        _logger.info("Login successful for db:%s login:%s from %s", db, login,
                     ip)
        return user.id

    def _clear_session(self):
        """ Function for clearing the session details of user."""
        self.write({
            'sid': False,
            'exp_date': False,
            'logged_in': False,
            'last_update': datetime.now()
        })

    def _save_session(self):
        """ Function for saving session details of the corresponding user."""
        exp_date = datetime.utcnow() + timedelta(minutes=45)
        sid = request.httprequest.session.sid
        self.with_user(SUPERUSER_ID).write({
            'sid': sid,
            'exp_date': exp_date,
            'logged_in': True,
            'last_update': datetime.now()
        })

    def _validate_sessions(self):
        """ Function for validating user sessions."""
        users = self.search([('exp_date', '!=', False)])
        for user in users:
            if user.exp_date < datetime.utcnow():
                # Clear session file for the user
                session_cleared = clear_session_history(user.sid)
                if session_cleared:
                    user._clear_session()     # Clear user session
                    _logger.info("Cron _validate_session: "
                                 "cleared session user: %s" % (user.name))
                else:
                    _logger.info("Cron _validate_session: failed to "
                                 "clear session user: %s" % (user.name))
