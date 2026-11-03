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


class LabourSupply(http.Controller):
    """Portal routes for labour supply contracts."""

    @http.route(['/labour_supplies'], type='http', auth='user',
                website=True)
    def portal_labour_supplies(self, **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        contracts = request.env['labour.supply'].search(
            [('customer_id', 'child_of', [partner.id])],
            order='create_date desc')
        return request.render(
            'manpower_supply_management.portal_labour_supply',
            {'labour_supplies_portal': contracts,
             'page_name': 'labour_supplies'})

    @http.route(['/labour_supplies/<int:contract_id>'], type='http',
                auth='user', website=True)
    def portal_labour_supply_details(self, contract_id, **kw):
        contract = request.env['labour.supply'].browse(contract_id).exists()
        if not contract or not contract.has_access('read'):
            return request.redirect('/my')
        return request.render(
            'manpower_supply_management.portal_labour_supply_details',
            {'contract': contract,
             'object': contract,
             'page_name': 'labour_supply'})