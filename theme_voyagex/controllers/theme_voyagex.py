# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.http import request


class VoyageXLoginRedirect(http.Controller):

    @http.route('/login', type='http', auth='public', website=True, sitemap=False)
    def redirect_login(self, **kw):
        """Redirect custom theme login URL to Odoo standard login."""
        return request.redirect('/web/login', code=301)

    @http.route('/signup', type='http', auth='public', website=True, sitemap=False)
    def redirect_signup(self, **kw):
        """Redirect custom theme signup URL to Odoo standard signup."""
        return request.redirect('/web/signup', code=301)
