# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http
from odoo.http import request

class OdoNovaThemeController(http.Controller):

    @http.route('/industries', type='http', auth='public', website=True)
    def industries_page(self, **kwargs):
        """
        Handle the /industries route by explicitly rendering the custom
        theme template. This avoids potential website.page DB record issues.
        """
        return request.render('theme_odonova.industries_template', {})

    @http.route('/case-studies', type='http', auth='public', website=True)
    def case_studies_page(self, **kwargs):
        """
        Handle the /case-studies route by explicitly rendering the custom
        theme template. This avoids potential website.page DB record issues.
        """
        return request.render('theme_odonova.case_studies_template', {})
    @http.route('/about', type='http', auth='public', website=True)
    def about_page(self, **kwargs):
        """
        Handle the /about route by explicitly rendering the custom
        theme template.
        """
        return request.render('theme_odonova.about_template', {})
    @http.route('/thankyou', type='http', auth='public', website=True)
    def thankyou_page(self, **kwargs):
        """
        Handle the /about route by explicitly rendering the custom
        theme template.
        """
        return request.render('theme_odonova.contactus_thank_you_template', {})


    @http.route('/consultation', type='http', auth='public', website=True)
    def consultation_page(self, **kwargs):
        """
        Handle the /about route by explicitly rendering the custom
        theme template.
        """
        return request.render('theme_odonova.consultation_template', {})
