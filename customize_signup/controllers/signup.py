""""Customize Signup"""
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
import base64
from odoo import http
from odoo.addons.auth_signup.controllers.main import \
    AuthSignupHome
from odoo.http import request


class WebAuthSignup(AuthSignupHome):
    """This class helps to set extra information in signup."""

    @http.route('/web/signup', type='http', auth='public', website=True,
                sitemap=False, csrf=False)
    def web_auth_signup(self, *args, **kw):
        """function used to add extra information at the time of signup"""
        res = super().web_auth_signup(*args, **kw)
        qcontext = self.get_auth_signup_qcontext()
        user = request.env['res.users']
        user_sudo = user.sudo().search(
            user._get_login_domain(qcontext.get('login')),
            order=user._get_login_order(), limit=1)
        if 'file' in kw:
            data_b64 = kw['file']
            data = base64.b64encode(data_b64.read()) if data_b64 else b''
            user_sudo.partner_id.image_1920 = data
        if 'phone' in kw:
            user_sudo.partner_id.phone = kw['phone']
        if 'job_position' in kw:
            user_sudo.partner_id.function = kw['job_position']
        if 'city' in kw:
            user_sudo.partner_id.city = kw['city']
        if 'country' in kw:
            country = request.env['res.country'].search(
                [('id', '=', kw['country'])])
            user_sudo.partner_id.country_id = country
        return res
