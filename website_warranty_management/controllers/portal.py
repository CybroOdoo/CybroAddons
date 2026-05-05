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
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class PortalAccount(CustomerPortal):
    """Inherited class to add portal menu for warranty claims"""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if not counters or 'warranty_count' in counters:
            partner = request.env.user.partner_id
            claim_count = request.env['warranty.claim'].sudo().search_count([
                ('customer_id', '=', partner.id)
            ])
            registration_count = request.env['warranty.registration'].sudo().search_count([
                ('customer_id', '=', partner.id)
            ])
            values['warranty_count'] = claim_count + registration_count
        return values


    @http.route(['/my/claims', '/my/claims/page/<int:page>'], type='http',
                auth="user", website=True)
    def my_claims(self):
        """ Function to pass the claims to the portal"""
        partner = request.env.user.partner_id
        claims = request.env['warranty.claim'].sudo().search([
            ('customer_id', '=', partner.id)
        ])
        registrations = request.env['warranty.registration'].sudo().search([
            ('customer_id', '=', partner.id)
        ])
        return request.render(
            "website_warranty_management.portal_warranty_claims",
            {
                'claim_data': claims,
                'registration_data': registrations,
                'page_name': 'claim_count',
            })

    def _prepare_portal_layout_values(self):
        """ Inherit _prepare_portal_layout_values to add claim and registration counts"""
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values['claim_count'] = request.env['warranty.claim'].sudo().search_count([
            ('customer_id', '=', partner.id)
        ])
        values['registration_count'] = request.env['warranty.registration'].sudo().search_count([
            ('customer_id', '=', partner.id)
        ])
        return values

