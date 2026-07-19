# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
import logging
from datetime import timedelta

from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import AccessDenied
from odoo.http import request

from ..controllers.session import clear_session_history

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Inheriting 'res.users' for adding fields related to session management."""

    _inherit = 'res.users'

    sid = fields.Char(
        string='Session ID',
        help="Unique session identifier of the currently active user session.",
    )
    exp_date = fields.Datetime(
        string='Session Expiration',
        help="Expiration date and time of the current active session.",
    )
    logged_in = fields.Boolean(
        string='Logged In',
        help="Indicates whether the user is currently logged in.",
    )
    last_update = fields.Datetime(
        string='Last Connection',
        help="Date and time of the user's last login.",
    )

    @api.model
    def _login(self, credential, user_agent_env=None):
        """Override login to enforce single-session restriction.

        Raises AccessDenied if the user already has an active session,
        otherwise delegates to the standard login flow and persists
        session metadata.
        """
        login = credential.get('login')
        user = self.sudo().search(
            self._get_login_domain(login),
            order=self._get_login_order(),
            limit=1,
        )
        if user and user.exp_date and user.sid and user.logged_in:
            _logger.warning("User %s is already logged in.", user.name)
            raise AccessDenied("already_logged_in")
        auth_info = super()._login(
            credential,
            user_agent_env=user_agent_env,
        )
        if user:
            user._save_session()
            user._update_last_login()
        return auth_info

    def _clear_session(self):
        """Clear the session details of the user."""
        self.write({
            'sid': False,
            'exp_date': False,
            'logged_in': False,
            'last_update': fields.Datetime.now(),
        })

    def _save_session(self):
        """Save session details for the corresponding user."""
        session_time_limit = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'restrict_logins.session_expire_time'
            )
        )
        exp_date = fields.Datetime.now() + timedelta(minutes=session_time_limit)
        sid = request.session.sid
        self.with_user(SUPERUSER_ID).write({
            'sid': sid,
            'exp_date': exp_date,
            'logged_in': True,
            'last_update': fields.Datetime.now(),
        })

    def _validate_sessions(self):
        """Validate user sessions and clear any that have expired."""
        users = self.search([('exp_date', '!=', False)])
        for user in users:
            if user.exp_date < fields.Datetime.now():
                session_cleared = clear_session_history(user.sid)
                if session_cleared:
                    user._clear_session()
                    _logger.info(
                        "Cron _validate_session: cleared session user: %s",
                        user.name,
                    )
                else:
                    _logger.info(
                        "Cron _validate_session: failed to clear session"
                        " user: %s",
                        user.name,
                    )
