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
import odoo
from odoo.addons.web.controllers.session import Session
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.http.router import db_filter
from odoo.http.session import authenticate, save_session

from contextlib import ExitStack


class AccessRestrict(Session):
    """Custom Session controller for enforcing IP access restrictions during session authentication."""

    @http.route()
    def authenticate(self, db, login, password, base_location=None):
        """Authenticate user credentials and verify client IP address against allowed IPs."""
        if not db_filter([db]):
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
            auth_info = authenticate(request.session, env, credential)
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
            save_session(request, env)
            return env['ir.http'].with_user(request.session.uid).session_info()
