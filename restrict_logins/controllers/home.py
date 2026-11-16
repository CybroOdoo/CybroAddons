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
from odoo.addons.web.controllers.home import Home as WebHome
from odoo import http
from odoo.tools.translate import _


class Home(WebHome):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        response = super().web_login(redirect=redirect, **kw)
        if hasattr(response, 'is_qweb') and response.is_qweb:
            error = response.qcontext.get('error')
            if error == "already_logged_in":
                uid = getattr(getattr(self, 'env', None), 'uid', None)
                response.qcontext['error'] = _(
                    "User already logged in. Log out from other devices and try again."
                )
                response.qcontext['logout_all'] = True
        return response
