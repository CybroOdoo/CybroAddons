# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
import werkzeug
from werkzeug.urls import url_encode
from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.home import ensure_db, Home, \
    SIGN_UP_REQUEST_PARAMS, LOGIN_SUCCESSFUL_PARAMS

_logger = logging.getLogger(__name__)
LOGIN_SUCCESSFUL_PARAMS.add('account_created')


class AuthSignupHome(Home):
    """Portal user login"""
    @http.route()
    def web_login(self, *args, **kw):
        """Function have login features"""
        response = super(AuthSignupHome, self).web_login(*args, **kw)
        if response.qcontext and response.qcontext.get('login', False):
            inactive_user = request.env['res.users.approve'].sudo().search(
                [('name', '=', response.qcontext.get('login')),
                 ('for_approval_menu', '=', False)])
            if inactive_user:
                response.qcontext["error"] = _(
                    "You can login only after your login get approved..!")
        return response

    @http.route('/web/signup', type='http', auth='public', website=True,
                sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """Function have signup features"""
        qcontext = self.get_auth_signup_qcontext()
        values = {k: v for k, v in request.params.items() if
                  k in SIGN_UP_REQUEST_PARAMS}
        signup_approval = request.env['ir.config_parameter'].sudo().get_param(
            'website_signup_approval.auth_signup_approval')
        if values:
            if signup_approval:
                return request.redirect('/success')
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                if qcontext.get('token'):
                    User = request.env['res.users']
                    user_sudo = User.sudo().search(
                        User._get_login_domain(qcontext.get('login')),
                        order=User._get_login_order(), limit=1
                    )
                    template = request.env.ref(
                        'auth_signup.mail_template_user_signup_account_created',
                        raise_if_not_found=False)
                    if user_sudo and template:
                        template.sudo().send_mail(user_sudo.id,
                                                  force_send=True)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search(
                        [("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _(
                        "Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")
        elif 'signup_email' in qcontext:
            user = request.env['res.users'].sudo().search(
                [('email', '=', qcontext.get('signup_email')),
                 ('state', '!=', 'new')], limit=1)
            if user:
                return request.redirect('/web/login?%s' % url_encode(
                    {'login': user.login, 'redirect': '/web'}))
        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    @http.route('/success', type='http', auth='public', website=True,
                sitemap=False)
    def approval_success(self):
        """Create approval request success form"""
        return request.render("website_signup_approval.approval_form_success")


class SignUpApproveController(http.Controller):
    """Manage Approval Request in Backend"""
    @http.route(['/web/signup/approve'], type='json', auth='public')
    def create_attachment(self, **dat):
        """Create approval request and attachment in backend"""
        data_list = []
        for data in dat['data']:
            data = data.split('base64')[1] if data else False
            data_list.append((0, 0, {'attachments': data}))
        if request.env['res.users.approve'].sudo().search(
                [('name', '=', dat['email'])]):
            pass
        else:
            attach = request.env['res.users.approve'].sudo().create(
                {'name': dat['email'],
                 'email': dat['username'],
                 'password': dat['password'],
                 'attachment_ids': data_list
                 })
            for data in dat['data']:
                data = data.split('base64')[1] if data else False
                request.env['ir.attachment'].sudo().create(
                    {'name': attach.name,
                     'datas': data,
                     'res_model': 'res.users.approve',
                     'res_id': attach.id,
                     }
                )
