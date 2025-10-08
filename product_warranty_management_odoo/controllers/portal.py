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
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class PortalAccount(CustomerPortal):
    """Inherited class to add portal menu for warranty claims"""
    def _prepare_home_portal_values(self, counters):
        """ Super the function to add the warranty claim menu"""
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user.partner_id.id
        claim_count = (request.env['warranty.claim'].
                       search_count([('customer_id', '=', user)]))
        values['claim_count'] = claim_count
        return values

    @http.route('/my/claims', type='http', auth="user", website=True)
    def my_claims(self):
        """ Define the action to open the warranty claim tree view"""
        user = request.env.user.partner_id.id
        claims = (request.env['warranty.claim'].sudo().
                  search([('customer_id', '=', user)]))
        # Extract the required fields and store them in a list of dictionaries
        claim_data = []
        for claim in claims:
            claim_data.append({
                'customer_id': claim.customer_id.name,
                'product_id': claim.product_id.name,
                'sale_order_id': claim.sale_order_id.name,
                'status': claim.state,
            })
        # Pass the claim_data to the template
        return http.request.render('product_warranty_management_odoo.portal_warranty_claims',
                                   {'claim_data': claim_data})
