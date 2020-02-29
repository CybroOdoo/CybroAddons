# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Milind Mohan(<https://www.cybrosys.com>)
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

from odoo import SUPERUSER_ID
from odoo import fields, api
from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request
from ..controllers.main import clear_session_history

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    sid = fields.Char('Session ID')
    exp_date = fields.Datetime('Expiry Date')
    logged_in = fields.Boolean('Logged In')
    last_update = fields.Datetime(string="Last Connection Updated")

    @classmethod
    def _login(cls, db, login, password):
        if not password:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                with self._assert_can_auth():
                    user = self.search(self._get_login_domain(login))
                    if not user:
                        raise AccessDenied()
                    user = user.with_user(user)
                    user._check_credentials(password)
                    # check sid and exp date
                    if user.exp_date and user.sid and user.logged_in:
                        _logger.warning("User %s is already logged in "
                                        "into the system!. Multiple "
                                        "sessions are not allowed for "
                                        "security reasons!" % user.name)
                        request.uid = user.id
                        raise AccessDenied("already_logged_in")
                    # save user session detail if login success
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
        """
            Function for clearing the session details for user
        """
        self.write({'sid': False, 'exp_date': False, 'logged_in': False,
                    'last_update': datetime.now()})

    def _save_session(self):
        """
            Function for saving session details to corresponding user
        """
        exp_date = datetime.utcnow() + timedelta(minutes=45)
        sid = request.httprequest.session.sid
        self.with_user(SUPERUSER_ID).write({'sid': sid, 'exp_date': exp_date,
                                            'logged_in': True,
                                            'last_update': datetime.now()})

    def _validate_sessions(self):
        """
            Function for validating user sessions
        """
        users = self.search([('exp_date', '!=', False)])
        for user in users:
            if user.exp_date < datetime.utcnow():
                # clear session session file for the user
                session_cleared = clear_session_history(user.sid)
                if session_cleared:
                    # clear user session
                    user._clear_session()
                    _logger.info("Cron _validate_session: "
                                 "cleared session user: %s" % (user.name))
                else:
                    _logger.info("Cron _validate_session: failed to "
                                 "clear session user: %s" % (user.name))
