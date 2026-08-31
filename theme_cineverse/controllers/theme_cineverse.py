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


class ThemeCineverseController(http.Controller):
    """
    HTTP Controller for handling custom routing of the CineVerse theme.
    Maps custom URLs to their respective QWeb templates.
    """

    @http.route(['/now-showing'], type='http', auth="public", website=True)
    def now_showing_page(self, **kwargs):
        """Render the 'Now Showing' movies template."""
        return request.render("theme_cineverse.cineverse_movies_template")

    @http.route(['/showtimes'], type='http', auth="public", website=True)
    def showtimes_page(self, **kwargs):
        """Render the 'Showtimes' scheduling template."""
        return request.render("theme_cineverse.cineverse_showtimes_template")

    @http.route(['/vip'], type='http', auth="public", website=True)
    def vip_page(self, **kwargs):
        """Render the VIP experiences template."""
        return request.render("theme_cineverse.cineverse_vip_template")

    @http.route(['/gallery'], type='http', auth="public", website=True)
    def gallery_page(self, **kwargs):
        """Render the cinematic photo gallery template."""
        return request.render("theme_cineverse.cineverse_gallery_template")
