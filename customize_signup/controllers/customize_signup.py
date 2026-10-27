# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

"""Customize signup controller for extra partner information."""

import base64
import logging

from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request
from odoo.tools.image import image_process
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)


class WebAuthSignup(AuthSignupHome):
    """This class helps to set extra information in signup."""

    def _update_partner_extra_fields(self, user_sudo, kw):
        """Update extra information fields on user's partner."""
        if 'file' in kw and kw['file']:
            file_obj = kw['file']
            file_content = file_obj.read() if hasattr(file_obj, 'read') else file_obj
            if isinstance(file_content, bytes) and file_content:
                # Server-side validation: ensure the uploaded file is a valid image
                mimetype = guess_mimetype(file_content)
                if mimetype.startswith('image/'):
                    try:
                        image_process(file_content, verify_resolution=True)
                        user_sudo.partner_id.image_1920 = base64.b64encode(file_content)
                    except Exception as err:
                        _logger.warning("Failed to decode uploaded image: %s", err)

        if kw.get('phone'):
            user_sudo.partner_id.phone = kw['phone']
        if kw.get('job_position'):
            user_sudo.partner_id.function = kw['job_position']
        if kw.get('city'):
            user_sudo.partner_id.city = kw['city']
        if kw.get('country'):
            country_val = kw['country']
            country = (
                request.env['res.country'].browse(int(country_val))
                if str(country_val).isdigit()
                else request.env['res.country'].search([('id', '=', country_val)], limit=1)
            )
            if country.exists():
                user_sudo.partner_id.country_id = country

    @http.route('/web/signup', type='http', auth='public', website=True,
                sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """ function used to add extra information at the time of signup """
        res = super().web_auth_signup(*args, **kw)
        if (
            request.httprequest.method != 'POST'
            or getattr(res, 'status_code', None) not in (301, 302, 303, 307, 308)
            or (hasattr(res, 'qcontext') and res.qcontext and res.qcontext.get('error'))
        ):
            return res

        qcontext = self.get_auth_signup_qcontext()
        login = qcontext.get('login')
        if not login:
            return res

        # Guard: Ensure the user was authenticated and logged in during signup
        user_sudo = None
        if request.session.uid:
            logged_in_user = request.env['res.users'].sudo().browse(request.session.uid)
            if logged_in_user.exists() and not logged_in_user._is_public() and logged_in_user.login == login:
                user_sudo = logged_in_user

        if not user_sudo:
            return res

        self._update_partner_extra_fields(user_sudo, kw)
        return res
