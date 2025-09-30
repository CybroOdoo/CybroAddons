# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import odoo
from odoo.modules.registry import Registry
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, AccessDenied
from odoo.addons.web.controllers.session import Session
from odoo.tools.translate import _

def _get_client_ip(req):
    """
    Extract the client IP address in a proxy-safe way.
    Prefer X-Forwarded-For (first item) if present, otherwise use REMOTE_ADDR.
    """
    forwarded_for = req.httprequest.environ.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        # X-Forwarded-For can be a comma-separated list: client, proxy1, proxy2...
        ip = forwarded_for.split(',')[0].strip()
        return ip
    return req.httprequest.remote_addr


def _check_user_ip(user, ip_address):
    """
    Check if the user is allowed to login from the given ip_address.
    Raises AccessDenied if not allowed.
    """
    if user and user.allowed_ip_ids:
        allowed_ips = set(user.allowed_ip_ids.mapped('ip_address'))
        if ip_address not in allowed_ips:
            raise AccessDenied(_("Not allowed to login from this IP address."))

class Session(Session):
    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, db, login, password, base_location=None, **kwargs):

        if request.db and request.db != db:
            request.env.cr.close()
        elif request.db:
            request.env.cr.rollback()
        if not http.db_filter([db]):
            raise AccessError("Database not found.")
        credential = {'login': login, 'password': password, 'type': 'password'}
        auth_info = request.session.authenticate(db, credential)
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        registry = Registry(db)
        with registry.cursor() as cr:
            env = odoo.api.Environment(cr, auth_info['uid'], {})
            wsgienv = {
                'interactive': True,
                'base_location': request.httprequest.url_root.rstrip('/'),
                'HTTP_HOST': request.httprequest.environ['HTTP_HOST'],
                'REMOTE_ADDR': request.httprequest.environ['REMOTE_ADDR'],
            }

            # if 2FA is disabled we finalize immediately
            user = env['res.users'].browse(auth_info['uid'])
            auth_info = registry['res.users'].authenticate(db, credential, wsgienv)
            if user and user.allowed_ip_ids:
                ip_list = set(user.allowed_ip_ids.mapped('ip_address'))
                if ip_address not in ip_list:
                    raise AccessError("Not allowed to login from this IP")
        if auth_info['uid'] != request.session.uid:
            # Crapy workaround for unupdatable Odoo Mobile App iOS (Thanks Apple :@) and Android
            # Correct behavior should be to raise AccessError("Renewing an expired session for user that has multi-factor-authentication is not supported. Please use /web/login instead.")
            return {'uid': None}

        request.session.db = db
        registry = odoo.modules.registry.Registry(db)
        with registry.cursor() as cr:
            env = odoo.api.Environment(cr, request.session.uid, request.session.context)
            if not request.db:
                # request._save_session would not update the session_token
                # as it lacks an environment, rotating the session myself
                http.root.session_store.rotate(request.session, env)
                request.future_response.set_cookie(
                    'session_id', request.session.sid,
                    max_age=http.get_session_max_inactivity(env), httponly=True
                )
            return env['ir.http'].session_info()
    Session.authenticate = authenticate
