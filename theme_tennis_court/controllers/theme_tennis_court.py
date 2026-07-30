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


class TennisCourtWebsite(http.Controller):
    """Controller for Tennis Court theme custom pages."""

    @http.route('/about', website=True, type='http', auth='public')
    def about(self, **_kw):
        """Render the custom About Us page for the Tennis Court theme."""
        return request.render('theme_tennis_court.tc_about_page')

    @http.route('/facilities', website=True, type='http', auth='public')
    def facilities(self, **_kw):
        """Render the custom Facilities page for the Tennis Court theme."""
        return request.render('theme_tennis_court.tc_facilities_page')

    @http.route('/programs', website=True, type='http', auth='public')
    def programs(self, **_kw):
        """Render the custom Programs page for the Tennis Court theme."""
        return request.render('theme_tennis_court.tc_programs_page')

    @http.route('/coaches', website=True, type='http', auth='public')
    def coaches(self, **_kw):
        """Render the custom Coaches page for the Tennis Court theme."""
        return request.render('theme_tennis_court.tc_coaches_page')

    @http.route('/pricing', website=True, type='http', auth='public')
    def pricing(self, **_kw):
        """Render the custom Pricing page for the Tennis Court theme."""
        return request.render('theme_tennis_court.tc_pricing_page')
