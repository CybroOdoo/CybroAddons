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
from datetime import timedelta

from odoo import api, fields, models
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
        auth_info = super()._login(
            credential,
            user_agent_env=user_agent_env,
        )
        user = self.sudo().browse(auth_info['uid'])
        current_sid = getattr(getattr(request, 'session', None), 'sid', False)
        current_ident = current_sid[:42] if current_sid else False
        stored_ident = user.sid[:42] if user.sid else False

        if (
            user
            and user.exp_date
            and stored_ident
            and user.logged_in
            and user.exp_date > fields.Datetime.now()
            and (not current_ident or stored_ident != current_ident)
        ):
            force_logout = False
            if request:
                params = getattr(request, 'params', {}) or {}
                form = getattr(getattr(request, 'httprequest', None), 'form', {}) or {}
                if (
                    params.get('force_logout') in ('1', 1, True, 'true')
                    or form.get('force_logout') in ('1', 1, True, 'true')
                ):
                    force_logout = True

            if force_logout:
                if user.sid:
                    clear_session_history(user.sid)
                user._clear_session()
            else:
                _logger.warning("User %s is already logged in.", user.name)
                raise AccessDenied("already_logged_in")

        if user:
            user._save_session()
        return auth_info

    def _clear_session(self):
        """Clear the session details of the user."""
        self.sudo().write({
            'sid': False,
            'exp_date': False,
            'logged_in': False,
            'last_update': fields.Datetime.now(),
        })

    def _save_session(self):
        """Save session details for the corresponding user."""
        session_time_limit = self.env[
            'ir.config_parameter'
        ].sudo().get_int(
            'restrict_logins.session_expire_time'
        ) or 60
        exp_date = fields.Datetime.now() + timedelta(minutes=session_time_limit)
        sid = (
            request.session.sid
            if (request and hasattr(request, 'session') and hasattr(request.session, 'sid'))
            else False
        )
        self.sudo().write({
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
