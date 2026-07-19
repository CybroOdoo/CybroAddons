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

import werkzeug.exceptions
import werkzeug.routing

from odoo import SUPERUSER_ID, api, fields, http, models
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.service import security

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    """Extends the Odoo abstract model 'ir.http' for custom HTTP handling."""

    _inherit = 'ir.http'

    @classmethod
    def _update_user_session(cls, u_sid, u_now, u_exp_date, u_uid):
        """Update session details for the corresponding user via direct query."""
        if u_uid and u_exp_date and u_sid and u_now:
            query = """UPDATE res_users
                          SET sid = %s,
                              last_update = %s,
                              exp_date = %s,
                              logged_in = TRUE
                        WHERE id = %s"""
            request.env.cr.execute(query, (u_sid, u_now, u_exp_date, u_uid))

    @classmethod
    def _authenticate(cls, endpoint):
        """Update user session details, check for session mismatches and
        perform necessary updates before authenticating the request."""
        auth_method = (
            'none'
            if http.is_cors_preflight(request, endpoint)
            else endpoint.routing['auth']
        )
        try:
            if request.session.uid:
                uid = request.session.uid
                user_pool = request.env['res.users'].with_user(
                    SUPERUSER_ID
                ).browse(uid)
                sid = request.session.sid
                last_update = user_pool.last_update
                now = fields.Datetime.now()
                session_time_limit = int(
                    request.env['ir.config_parameter'].sudo().get_param(
                        'restrict_logins.session_expire_time'
                    )
                )
                exp_date = fields.Datetime.now() + timedelta(
                    minutes=session_time_limit
                )
                if uid and user_pool.sid and sid != user_pool.sid:
                    cls._update_user_session(sid, now, exp_date, uid)
                else:
                    if (
                        not user_pool.last_update
                        and not user_pool.sid
                        and not user_pool.logged_in
                    ):
                        cls._update_user_session(sid, now, exp_date, uid)
                    if last_update:
                        update_diff = (
                            (fields.Datetime.now() - last_update).total_seconds()
                            / 60.0
                        )
                        if uid and (update_diff > 0.5 or sid != user_pool.sid):
                            cls._update_user_session(sid, now, exp_date, uid)
        except Exception as e:
            _logger.info(
                "Exception during updating user session: %s", e
            )
        try:
            if request.session.uid is not None:
                if not security.check_session(request.session, request.env):
                    request.session.logout(keep_db=True)
                    request.env = api.Environment(
                        request.env.cr, None, request.session.context
                    )
            getattr(cls, '_auth_method_{}'.format(auth_method))()
        except (
            AccessDenied,
            http.SessionExpiredException,
            werkzeug.exceptions.HTTPException,
        ):
            raise
        except Exception:
            _logger.info(
                "Exception during request authentication.", exc_info=True
            )
            raise AccessDenied()
        return auth_method
