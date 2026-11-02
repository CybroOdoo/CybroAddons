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
"""Controller definitions for handling REST API requests and authentication."""
from contextlib import ExitStack
from datetime import date, datetime
import json
import odoo
from odoo import http
from odoo.http import request
from odoo.http.session import authenticate, get_default_session, save_session


class RestApi(http.Controller):
    """Controller used to generate responses based on REST API requests."""

    def auth_api_key(self, api_key, user=None):
        """Authenticate the API key when sending a request."""
        if not api_key:
            return ("<html><body><h2>No <i>API Key</i> Provided "
                    "!</h2></body></html>")
        if user is None:
            if getattr(request, 'session', None) and getattr(request.session, 'uid', None):
                user = request.env['res.users'].browse(request.session.uid)
            elif getattr(request, 'env', None) and getattr(request.env, 'user', None):
                user = request.env.user

        if (user and not user._is_public()
                and user.sudo().api_key and user.sudo().api_key == api_key):
            return True
        return ('<html><body><h2>Invalid <i>API Key</i> '
                '!</h2></body></html>')

    def generate_response(self, method, model, rec_id):
        """Generate a response based on the request method and parameters."""
        option = request.env['connection.api'].sudo().search(
            [('model_id', '=', model)], limit=1)
        model_name = option.model_id.model
        if method != 'DELETE':
            data = json.loads(request.httprequest.data)
        else:
            data = {}
        fields = []
        if data:
            for field in data['fields']:
                fields.append(field)
        if not fields and method != 'DELETE':
            return ("<html><body><h2>No fields selected for the model"
                    "</h2></body></html>")
        if not option:
            return ("<html><body><h2>No Record Created for the model"
                    "</h2></body></html>")
        try:
            if method == 'GET':
                fields = []
                for field in data['fields']:
                    fields.append(field)
                if not option.is_get:
                    return ("<html><body><h2>Method Not Allowed"
                            "</h2></body></html>")
                else:
                    datas = []
                    if rec_id != 0:
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', rec_id)],
                            fields=fields
                        )
                        for record in partner_records:
                            for key, value in record.items():
                                if isinstance(value, (datetime, date)):
                                    record[key] = value.isoformat()
                        data = json.dumps({
                            'records': partner_records
                        })
                        datas.append(data)
                        return request.make_response(data=datas)
                    else:
                        partner_records = request.env[
                            str(model_name)].search_read(
                            domain=[],
                            fields=fields
                        )
                        for record in partner_records:
                            for key, value in record.items():
                                if isinstance(value, (datetime, date)):
                                    record[key] = value.isoformat()
                        data = json.dumps({
                            'records': partner_records
                        })
                        datas.append(data)
                        return request.make_response(data=datas)
        except Exception:
            return ("<html><body><h2>Invalid JSON Data"
                    "</h2></body></html>")
        if method == 'POST':
            if not option.is_post:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                try:
                    data = json.loads(request.httprequest.data)
                    datas = []
                    new_resource = request.env[str(model_name)].create(
                        data['values'])
                    partner_records = request.env[
                        str(model_name)].search_read(
                        domain=[('id', '=', new_resource.id)],
                        fields=fields
                    )
                    for record in partner_records:
                        for key, value in record.items():
                            if isinstance(value, (datetime, date)):
                                record[key] = value.isoformat()
                    new_data = json.dumps({'New resource': partner_records, })
                    datas.append(new_data)
                    return request.make_response(data=datas)
                except Exception:
                    return ("<html><body><h2>Invalid JSON Data"
                            "</h2></body></html>")
        if method == 'PUT':
            if not option.is_put:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                if rec_id == 0:
                    return ("<html><body><h2>No ID Provided"
                            "</h2></body></html>")
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        return ("<html><body><h2>Resource not found"
                                "</h2></body></html>")
                    else:
                        try:
                            datas = []
                            data = json.loads(request.httprequest.data)
                            resource.write(data['values'])
                            partner_records = request.env[
                                str(model_name)].search_read(
                                domain=[('id', '=', resource.id)],
                                fields=fields
                            )
                            for record in partner_records:
                                for key, value in record.items():
                                    if isinstance(value, (datetime, date)):
                                        record[key] = value.isoformat()
                            new_data = json.dumps(
                                {'Updated resource': partner_records,
                                 })
                            datas.append(new_data)
                            return request.make_response(data=datas)

                        except Exception:
                            return ("<html><body><h2>Invalid JSON Data "
                                    "!</h2></body></html>")
        if method == 'DELETE':
            if not option.is_delete:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                if rec_id == 0:
                    return ("<html><body><h2>No ID Provided"
                            "</h2></body></html>")
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        return ("<html><body><h2>Resource not found"
                                "</h2></body></html>")
                    else:

                        records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', resource.id)],
                            fields=['id', 'display_name']
                        )
                        remove = json.dumps(
                            {"Resource deleted": records,
                             })
                        resource.unlink()
                        return request.make_response(data=remove)

    @http.route(['/send_request'], type='http',
                auth='none',
                methods=['GET', 'POST', 'PUT', 'DELETE'], csrf=False)
    def fetch_data(self, **kw):
        """Handle incoming REST API requests, authenticate the API key, and return the response."""
        http_method = request.httprequest.method
        api_key = request.httprequest.headers.get('api-key')
        model = kw.get('model')
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        credential = {'login': username, 'password': password, 'type': 'password'}
        db = request.httprequest.headers.get('db') or request.session.db
        with ExitStack() as stack:
            if not getattr(request, 'db', None) or request.db != db:
                cr = stack.enter_context(odoo.modules.registry.Registry(db).cursor())
                env = odoo.api.Environment(cr, None, {})
            else:
                env = request.env

            try:
                auth = authenticate(request.session, env, credential)
            except Exception as e:
                return ("<html><body><h2>wrong login credentials: %s"
                        "</h2></body></html>" % str(e))

            if isinstance(auth, dict) and auth.get('uid'):
                request.session.uid = auth['uid']
            if getattr(request.session, 'uid', None):
                env = env(user=request.session.uid)

            orig_env = getattr(request, 'env', None)
            request.env = env
            try:
                auth_api = self.auth_api_key(api_key, user=env.user)
            finally:
                if orig_env:
                    request.env = orig_env

            model_id = env['ir.model'].sudo().search([('model', '=', model)])
            if not model_id:
                return ("<html><body><h3>Invalid model, check spelling or maybe "
                        "the related "
                        "module is not installed"
                        "</h3></body></html>")

            if auth_api is True:
                raw_id = kw.get('Id') or kw.get('id')
                rec_id = int(raw_id) if raw_id else 0
                orig_env = getattr(request, 'env', None)
                request.env = env
                try:
                    result = self.generate_response(http_method, model_id.id, rec_id)
                finally:
                    if orig_env:
                        request.env = orig_env
                save_session(request, env)
                return result
            else:
                save_session(request, env)
                return auth_api

    @http.route(['/odoo_connect'], type="http", auth="none", csrf=False,
                methods=['GET'])
    def odoo_connect(self):
        """Initialize the API transaction by authenticating and generating an
        API key for the user.
        """
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        db = request.httprequest.headers.get('db')
        try:
            with ExitStack() as stack:
                if not getattr(request, 'db', None) or request.db != db:
                    cr = stack.enter_context(odoo.modules.registry.Registry(db).cursor())
                    env = odoo.api.Environment(cr, None, {})
                else:
                    env = request.env

                request.session.update(get_default_session(), db=db)
                credential = {'login': username, 'password': password,
                              'type': 'password'}
                auth = authenticate(request.session, env, credential)
                user = env['res.users'].browse(auth['uid'])
                api_key = user.generate_api(username)
                datas = json.dumps({"Status": "auth successful",
                                    "User": user.name,
                                    "api-key": api_key})
                save_session(request, env(user=request.session.uid))
                return request.make_response(data=datas)
        except Exception as e:
            return ("<html><body><h2>wrong login credentials: %s"
                    "</h2></body></html>" % str(e))
