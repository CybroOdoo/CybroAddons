# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
##############################################################################
from odoo import http
from odoo.http import request


class WebsiteInvesting(http.Controller):
    """
    Controller class for investing and trading page on trading theme website.
    """

    @http.route(['/investing_page'], type='http', auth="public", website=True)
    def investing_page(self, **kw):
        """
        HTTP route method that renders the investing page template for the trading theme on the website.
        :param kw: keyword arguments
        :return: HTTP response containing the rendered template
        """
        return request.render("theme_trading.investing_page")

    @http.route(['/trading_page'], type='http', auth="public", website=True)
    def trading_page(self, **kw):
        """
        This method handles the request to the Trading website page and renders the
        'theme_trading.trading_page' template.
        """
        return request.render("theme_trading.trading_page")
