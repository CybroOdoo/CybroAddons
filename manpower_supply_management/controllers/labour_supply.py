# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
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
###########################################################################
from odoo import http
from odoo.http import request


class LabourSupply(http.Controller):
    """ Class to create a route for labour supply details in  website"""

    @http.route(['/labour_supplies'], type='http', auth='user',
                website=True)
    def create_labour_on_supply(self):
        """ Function to render template to website"""
        labour_supplies = request.env['labour.supply'].search(
            [('customer_id.id', '=',
              request.env.user.commercial_partner_id.id)])
        return request.render('manpower_supply_management.portal_labour_supply',
                              {'labour_supplies_portal': labour_supplies,
                               'page_name': 'labour_supplies_contract'})

    @http.route(['/labour_supplies/<int:contract>'], type='http',
                auth="user", website=True)
    def labour_on_supply_details(self, contract):
        """ Function to render template and pass value to website"""
        labour_contract_rec = request.env['labour.supply'].browse(contract)
        labour_contract_line_rec = request.env['labour.on.skill'].search(
            [('labour_supply_id', '=', contract)])
        return http.request.render(
            'manpower_supply_management.portal_labour_supply_details',
            {'labour_contract_line_rec': labour_contract_line_rec,
             'labour_contract_rec': labour_contract_rec,
             'page_name': 'labour_supplies'})
