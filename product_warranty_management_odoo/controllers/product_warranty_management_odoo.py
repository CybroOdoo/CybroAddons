# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class WarrantyClaimController(http.Controller):
    """ Class for Warranty claim controller"""

    @http.route('/warranty', type='http', auth="public", website=True)
    def warranty_claim(self):
        """ Function to pass the warranty claim details to the warranty
        claim page"""
        customers = request.env['res.partner'].sudo().search([])
        sale_orders = request.env['sale.order'].sudo().search([])
        products = request.env['product.template'].sudo().search([])
        return request.render('product_warranty_management_odoo.warranty_claim_page',
                              {'sale_orders': sale_orders,
                               'customers': customers,
                               'products': products})

    @http.route('/warranty/claim/submit', type='http', auth="public",
                website=True)
    def warranty_claim_submit(self):
        """Function to render the claim thanks view"""
        return request.render('product_warranty_management_odoo.claim_thanks_view')
