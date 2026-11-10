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
import json
import logging
import werkzeug.exceptions

from odoo import _, http
from odoo.addons.web.controllers.home import (
    LOGIN_SUCCESSFUL_PARAMS,
    SIGN_UP_REQUEST_PARAMS,
    Home,
)
from odoo.http import request

_logger = logging.getLogger(__name__)
LOGIN_SUCCESSFUL_PARAMS.add('account_created')


class AuthSignupHome(Home):
    """Portal user login and signup approval controller"""

    @http.route()
    def web_login(self, *args, **kw):
        """Block login for users whose signup request is pending approval"""
        response = super().web_login(*args, **kw)
        signup_approval = request.env['ir.config_parameter'].sudo().get_bool(
            'website_signup_approval.auth_signup_approval')
        if (signup_approval and response.qcontext and
                response.qcontext.get('login', False)):
            inactive_user = request.env['res.users.approve'].sudo().search(
                [('email', '=', response.qcontext.get('login')),
                 ('for_approval_menu', '=', False)], limit=1)
            if inactive_user:
                response.qcontext["error"] = _(
                    "You can log in only after your account has been "
                    "approved.")
        return response

    @http.route('/web/signup', type='http', auth='public', website=True,
                sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """Handle signup approval flow when enabled, standard otherwise"""
        signup_approval = request.env['ir.config_parameter'].sudo().get_bool(
            'website_signup_approval.auth_signup_approval')
        qcontext = self.get_auth_signup_qcontext()

        # Token invitations bypass approval flow and use standard flow
        if qcontext.get('token') or not signup_approval:
            return super().web_auth_signup(*args, **kw)

        # Public signup without token: check signup_enabled (b2c vs b2b)
        if not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        values = {k: v for k, v in request.params.items() if
                  k in SIGN_UP_REQUEST_PARAMS}
        if request.httprequest.method == 'POST' and values:
            if (values.get('password') !=
                    request.params.get('confirm_password')):
                qcontext['error'] = _("Passwords do not match")
                return request.render('auth_signup.signup', qcontext)
            if request.env['res.users'].sudo().search(
                    [('login', '=', request.params.get('login'))], limit=1):
                qcontext['error'] = _(
                    "Another user is already registered using this "
                    "email address.")
                return request.render('auth_signup.signup', qcontext)

            # Create approval request if not created via RPC (e.g. no files)
            approve = request.env['res.users.approve'].sudo().search(
                [('email', '=', values.get('login'))], limit=1)
            if not approve:
                doc_param = request.env['ir.config_parameter'].sudo().get_str(
                    'website_signup_approval.documents_ids')
                required_docs = request.env['document.attachment']
                if doc_param:
                    try:
                        required_doc_ids = json.loads(doc_param)
                        if required_doc_ids:
                            required_docs = request.env[
                                'document.attachment'].sudo().browse(
                                required_doc_ids).exists()
                    except (ValueError, TypeError):
                        required_docs = request.env['document.attachment']
                if required_docs:
                    qcontext['error'] = _(
                        "Please upload all required documents.")
                    return request.render('auth_signup.signup', qcontext)

                ctx = request.env['res.users']._crypt_context()
                raw_pw = values.get('password')
                pw_hash = ctx.hash(raw_pw) if raw_pw else False
                request.env['res.users.approve'].sudo().create({
                    'name': values.get('name'),
                    'email': values.get('login'),
                    'password': pw_hash,
                })
            return request.redirect('/success')
        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = (
            "frame-ancestors 'self'")
        return response

    @http.route('/success', type='http', auth='public', website=True,
                sitemap=False)
    def approval_success(self):
        """Display approval request success page"""
        return request.render("website_signup_approval.approval_form_success")


class SignUpApproveController(http.Controller):
    """Manage Approval Request in Backend"""

    @http.route(['/web/signup/approve'], type='jsonrpc', auth='public')
    def create_attachment(self, **dat):
        """Create approval request and attachments in backend"""
        params = request.env['ir.config_parameter'].sudo()
        if not params.get_bool(
                'website_signup_approval.auth_signup_approval'):
            return {'error': _("Signup approval is not enabled")}

        # Check signup_enabled (b2b vs b2c)
        signup_enabled = (
            request.env['res.users'].sudo()._get_signup_invitation_scope() == 'b2c'
        )
        token = (dat.get('token') or "").strip() or False
        if not signup_enabled and not token:
            return {'error': _("Signup is not allowed for uninvited users")}
        if token:
            try:
                request.env['res.partner'].sudo()._signup_retrieve_info(token)
            except Exception:
                return {'error': _("Invalid signup token")}

        if dat.get('password') != dat.get('confirm_password'):
            return {'error': _("Passwords do not match")}
        approve_id = request.env['res.users.approve']
        if approve_id.sudo().search(
                [('email', '=', dat.get('email'))], limit=1):
            return {'error': _("A request for this email already exists")}
        if request.env['res.users'].sudo().search(
                [('login', '=', dat.get('email'))], limit=1):
            return {'error': _(
                "Another user is already registered using this email "
                "address.")}

        # Check required documents
        doc_param = params.get_str('website_signup_approval.documents_ids')
        required_docs = request.env['document.attachment']
        if doc_param:
            try:
                required_doc_ids = json.loads(doc_param)
                if required_doc_ids:
                    required_docs = request.env[
                        'document.attachment'].sudo().browse(
                        required_doc_ids).exists()
            except (ValueError, TypeError):
                required_docs = request.env['document.attachment']

        raw_data = dat.get('data') or []
        data_list = []
        for data in raw_data:
            if not data:
                continue
            b64 = data.split('base64,')[1] if 'base64,' in data else data
            if b64:
                data_list.append((0, 0, {'attachments': b64}))

        if required_docs and len(data_list) < len(required_docs):
            return {'error': _("Please upload all required documents.")}

        raw_pw = dat.get('password')
        ctx = request.env['res.users']._crypt_context()
        pw_hash = ctx.hash(raw_pw) if raw_pw else False
        approve_id.sudo().create({
            'name': dat.get('username'),
            'email': dat.get('email'),
            'password': pw_hash,
            'attachment_ids': data_list,
        })
        return {'success': True}
