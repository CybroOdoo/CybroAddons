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
#############################################################################
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class PortalAccount(CustomerPortal):
    """Inherited class to add portal menu for warranty claims"""

    def _prepare_portal_counter_values(self, counter):
        """New Odoo 20 hook: return (model_name, domain, access_operation)
        for each placeholder_count key registered on a portal.entry record.
        This replaces manually computing counts in _prepare_home_portal_values."""
        partner = request.env.user.partner_id
        if counter == 'claim_count':
            return 'warranty.claim', [('customer_id', '=', partner.id)], 'sudo'
        if counter == 'registration_count':
            return 'warranty.registration', [('customer_id', '=', partner.id)], 'sudo'
        return super()._prepare_portal_counter_values(counter)

    @http.route(['/my/claims', '/my/claims/page/<int:page>'], type='http',
                auth="user", website=True)
    def my_claims(self, page=1, **kw):
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

