# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
        return request.render('product_warranty_management_odoo'
                              '.warranty_claim_page',
                              {'sale_orders': sale_orders,
                               'customers': customers,
                               'products': products})

    @http.route('/warranty/claim/submit', type='http', auth="public",
                website=True)
    def warranty_claim_submit(self):
        """Function to render the claim thanks view"""
        return request.render('product_warranty_management_odoo'
                              '.claim_thanks_view')

    @http.route('/partner/sale_order', type='json', auth="public",
                website=True)
    def get_sale_order_data(self, partner_id):
        """Get sale order data of selected customer"""
        return request.env['sale.order'].search_read([
            ('partner_id', '=', partner_id)])

    @http.route('/partner/sale_order_line', type='json', auth="public",
                website=True)
    def get_sale_order_line_data(self, order_id):
        """Get sale order line data of selected order"""
        return request.env['sale.order.line'].search_read([
            ('order_id', '=', order_id)])

    @http.route('/partner/warranty_claim_count', type='json', auth="public",
                website=True)
    def warranty_claim_count(self, sale_order_id):
        """Get claim count of selected sale order"""
        return request.env['warranty.claim'].search_count([
            ('sale_order_id', '=', sale_order_id)
        ])

    @http.route('/read/sale_order', type='json', auth="public",
                website=True)
    def read_sale_order(self, order_id):
        """Read sale order data"""
        return request.env['sale.order'].search([('id', '=', order_id),
                                                 (
                                                 'is_warranty_check', '=', True)
                                                 ]).read()

    @http.route('/check/selected_product', type='json', auth="public",
                website=True)
    def check_selected_product(self, product_id):
        """Check weather the selected product is a warranty product"""
        return request.env['product.product'].search([
            ('id', '=', product_id),
            ('is_warranty_available', '=', True)
        ]).read()

    @http.route('/create_warranty_claim', type='json', auth="public",
                website=True)
    def create_warranty_claim(self, sale_order_id, customer_id, product_id):
        """create a warranty claim for the selected user"""
        request.env['warranty.claim'].create({
            'customer_id': customer_id,
            'product_id': product_id,
            'sale_order_id': sale_order_id,
        })
