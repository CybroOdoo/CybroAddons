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
#############################################################################
import logging
from datetime import timedelta

from odoo import fields, models
from odoo.http import request
from odoo.http.session import session_store, logout as odoo_logout

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
        try:
            if request.session.uid and not getattr(request.env.cr, 'readonly', False):
                uid = request.session.uid
                user_pool = request.env['res.users'].sudo().browse(uid)
                sid = getattr(request.session, 'sid', False)
                if not sid:
                    return super()._authenticate(endpoint)

                current_ident = sid[:42]
                stored_ident = user_pool.sid[:42] if user_pool.sid else False
                now = fields.Datetime.now()
                session_time_limit = request.env[
                    'ir.config_parameter'
                ].sudo().get_int(
                    'restrict_logins.session_expire_time'
                ) or 60
                exp_date = now + timedelta(minutes=session_time_limit)

                if uid and stored_ident and current_ident != stored_ident:
                    store = session_store()
                    missing = store.get_missing_session_identifiers([stored_ident])
                    if stored_ident not in missing:
                        odoo_logout(request.session, keep_db=True)
                        return super()._authenticate(endpoint)
                    cls._update_user_session(sid, now, exp_date, uid)
                else:
                    if (
                        not user_pool.last_update
                        or not user_pool.sid
                        or not user_pool.logged_in
                    ):
                        cls._update_user_session(sid, now, exp_date, uid)
                    elif user_pool.last_update:
                        update_diff = (
                            (now - user_pool.last_update).total_seconds()
                            / 60.0
                        )
                        if update_diff > 1.0 or user_pool.sid != sid:
                            cls._update_user_session(sid, now, exp_date, uid)
        except Exception as e:
            _logger.info(
                "Exception during updating user session: %s", e
            )
        return super()._authenticate(endpoint)
