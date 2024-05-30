# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
import logging
from datetime import datetime, timedelta
import werkzeug
import werkzeug.exceptions
import werkzeug.routing
from odoo import http, models, SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    """ Extends the Odoo abstract model 'ir.http' for custom HTTP handling."""
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        """ This method updates user session details, checks for session
        mismatches and performs necessary updates."""
        auth_method = endpoint.routing["auth"]
        if request._is_cors_preflight(endpoint):
            auth_method = 'none'
        try:
            if request.session.uid:
                uid = request.session.uid
                user_pool = request.env['res.users'].with_user(
                    SUPERUSER_ID).browse(uid)

                def _update_user(u_sid, u_now, u_exp_date, u_uid):
                    """ Function for updating session details for the
                    corresponding user."""
                    if u_uid and u_exp_date and u_sid and u_now:
                        query = """update res_users set sid = '%s',
                                       last_update = '%s',exp_date = '%s',
                                       logged_in = 'TRUE' where id = %s
                                       """ % (u_sid, u_now, u_exp_date, u_uid)
                        request.env.cr.execute(query)
                sid = request.session.sid
                last_update = user_pool.last_update
                now = datetime.now()
                exp_date = datetime.now() + timedelta(minutes=45)
                # Check that the authentication contains bus_inactivity
                request_params = request.params.copy()
                if 'options' in request_params and 'bus_inactivity' in \
                        request_params['options']:
                    # Update session if there is sid mismatch
                    if uid and user_pool.sid and sid != user_pool.sid:
                        _update_user(sid, now, exp_date, uid)
                else:
                    # Update if there is no session data and user is active
                    if not user_pool.last_update and not user_pool.sid and \
                            not user_pool.logged_in:
                        _update_user(sid, now, exp_date, uid)
                    # Update sid and date if last update is above 0.5 min
                    if last_update:
                        update_diff = (datetime.now() -
                                       last_update).total_seconds() / 60.0
                        if uid and (update_diff > 0.5 or sid != user_pool.sid):
                            _update_user(sid, now, exp_date, uid)
        except Exception as e:
            _logger.info(
                "Exception during updating user session...%s", e)
            pass
        try:
            if request.session.uid:
                try:
                    request.session.check_security()
                    # What if error in security.check()
                    #   -> res_users.check()
                    #   -> res_users._check_credentials()
                except (AccessDenied, http.SessionExpiredException):
                    # All other exceptions mean undetermined status
                    # (e.g.connection pool full), let them bubble up
                    request.session.logout(keep_db=True)
            if request.uid is None:
                getattr(cls, "_auth_method_%s" % auth_method)()
        except (AccessDenied, http.SessionExpiredException,
                werkzeug.exceptions.HTTPException):
            raise
        except Exception:
            _logger.info("Exception during request Authentication.",
                         exc_info=True)
            raise AccessDenied()
        return auth_method
