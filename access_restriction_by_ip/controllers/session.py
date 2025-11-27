# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
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
from odoo.addons.web.controllers.session import Session
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

from contextlib import ExitStack


class AccessRestrict(Session):

    @http.route()
    def authenticate(self, db, login, password, base_location=None):
        if not http.db_filter([db]):
            raise AccessError("Database not found.")
        with ExitStack() as stack:
            if not request.db or request.db != db:
                # Use a new env only when no db on the request, which means the env was not set on in through `_serve_db`
                # or the db is different than the request db
                cr = stack.enter_context(odoo.modules.registry.Registry(db).cursor())
                env = odoo.api.Environment(cr, None, {})
            else:
                env = request.env
            credential = {'login': login, 'password': password, 'type': 'password'}
            auth_info = request.session.authenticate(env, credential)
            ip_address = request.httprequest.environ['REMOTE_ADDR']
            user = request.env['res.users'].sudo().browse(auth_info['uid']).exists()
            if user and user.allowed_ip_ids:
                ip_list = set(user.allowed_ip_ids.mapped('ip_address'))
                if ip_address not in ip_list:
                    raise AccessError("Not allowed to login from this IP")
            if auth_info['uid'] != request.session.uid:
                # Crapy workaround for unupdatable Odoo Mobile App iOS (Thanks Apple :@) and Android
                # Correct behavior should be to raise AccessError("Renewing an expired session for user that has multi-factor-authentication is not supported. Please use /web/login instead.")
                return {'uid': None}
            request.session.db = db
            request._save_session(env)
            return env['ir.http'].with_user(request.session.uid).session_info()
