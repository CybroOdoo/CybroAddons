# -*- coding: utf-8 -*-

import odoo
from odoo.addons.web.controllers.session import Session
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class AccessRestrict(Session):

    @http.route()
    def authenticate(self, db, login, password, base_location=None):
        if not http.db_filter([db]):
            raise AccessError("Database not found.")
        pre_uid = request.session.authenticate(db, login, password)
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        user = request.env['res.users'].sudo().browse(pre_uid).exists()
        if user and user.allowed_ip_ids:
            ip_list = set(user.allowed_ip_ids.mapped('ip_address'))
            if ip_address not in ip_list:
                raise AccessError("Not allowed to login from this IP")
        if pre_uid != request.session.uid:
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
                    max_age=http.SESSION_LIFETIME, httponly=True
                )
            return env['ir.http'].session_info()
