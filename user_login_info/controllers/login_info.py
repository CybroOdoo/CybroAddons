# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.addons.web.controllers.home import Home
from odoo.http import request


class ImageController(Home):
    """Controller for capturing user image during login."""

    @http.route()
    def web_login(self, redirect=None, **kw):
        """Standard login with image capture logic."""
        res = super().web_login(redirect=redirect, **kw)
        if request.httprequest.method == 'POST':
            captured_image = request.params.get('captured_image')
            if captured_image:
                if not request.params.get('login_success'):
                    # User failed to login
                    request.env['user.log'].sudo().create({
                        'image': captured_image,
                        'is_secure': True
                    })
                else:
                    # User logged in successfully
                    request.env['user.log'].sudo().create({
                        'user_id': request.env.user.id,
                        'image': captured_image
                    })
        return res
