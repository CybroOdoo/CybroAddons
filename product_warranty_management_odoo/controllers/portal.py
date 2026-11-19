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
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class WarrantyClaimPortal(CustomerPortal):
    """Show the warranty claims of the customer in the portal."""

    def _prepare_claims_domain(self):
        """Return the domain of the current customer's claims."""
        partner = request.env.user.partner_id.commercial_partner_id
        return [('customer_id', 'child_of', partner.id)]

    def _prepare_portal_counter_values(self, counter):
        """Add the counter of the 'My Claims' portal card."""
        if counter == 'claim_count':
            return 'warranty.claim', self._prepare_claims_domain(), 'sudo'
        return super()._prepare_portal_counter_values(counter)

    @http.route('/my/claims', type='http', auth='user', website=True)
    def portal_my_claims(self):
        """List the warranty claims of the current customer."""
        claims = request.env['warranty.claim'].sudo().search(
            self._prepare_claims_domain())
        values = self._prepare_portal_layout_values()
        values.update({'claims': claims, 'page_name': 'warranty_claims'})
        return request.render(
            'product_warranty_management_odoo.portal_warranty_claims', values)
