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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request


class LumieeEventsWebsite(http.Controller):
    """Controller for Lumiee Events theme custom pages."""

    @http.route('/services', website=True, type='http', auth='public')
    def services(self, **kw):
        """Renders the services page."""
        return request.render('theme_lumiee_events.le_services_page')

    @http.route('/gallery', website=True, type='http', auth='public')
    def gallery(self, **kw):
        """Renders the gallery page."""
        return request.render('theme_lumiee_events.le_gallery_page')

    @http.route('/pricing', website=True, type='http', auth='public')
    def pricing(self, **kw):
        """Renders the pricing page."""
        return request.render('theme_lumiee_events.le_pricing_page')

    @http.route('/contact', website=True, type='http', auth='public')
    def contact(self, **kw):
        """Renders the contact page."""
        return request.render('theme_lumiee_events.le_contact_page')
