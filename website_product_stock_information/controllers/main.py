# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################

from odoo import http
from odoo.http import request

class WebsiteSaleStock(http.Controller):

    @http.route(['/shop'], type='http', auth='public', website=True)
    def shop(self, **kwargs):
        response = request.render('website_sale.products')
        header = request.env['website.page'].search([
            ('url', '=', '/shop')
        ], limit=1)

        response.qcontext['showStockInfo'] = (
            header and header.arch_db.find('data-show-stock-info="1"') != -1
        )
        return response
