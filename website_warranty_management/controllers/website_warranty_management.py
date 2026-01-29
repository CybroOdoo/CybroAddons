# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
        if request.env.user.has_group('base.group_portal'):
            customers = request.env.user.partner_id
            sale_orders = request.env['sale.order'].sudo().search(
                [('partner_id', '=', customers.id)])
        elif request.env.user.has_group('base.group_public'):
            customers = ""
            sale_orders = ""
        else:
            customers = request.env['res.partner'].sudo().search([])
            sale_orders = request.env['sale.order'].sudo().search([])
        products = request.env['product.template'].sudo().search([])
        return request.render(
            'website_warranty_management.warranty_claim_page',
            {'sale_orders': sale_orders,
             'customers': customers,
             'products': products})

    @http.route('/warranty/claim/submit', type='http', auth="public",
                website=True)
    def warranty_claim_submit(self):
        """Function to render the claim thanks view"""
        return request.render(
            'website_warranty_management.claim_thanks_view')
