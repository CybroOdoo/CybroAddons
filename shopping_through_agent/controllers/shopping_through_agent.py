# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.http import Controller, request, route


class Agent(Controller):
    """Class for the function to render a new page"""
    @route(route='/agent/shop', auth='user', website=True)
    def agent(self):
        """Function to pass the data to shop and also to clearing the cart"""
        customer_ids = request.env['res.partner'].search(
            [('agent_id', '=', request.env.user.partner_id.id)])
        return request.render('shopping_through_agent.agent_shop_template',
                              {'customer_ids': customer_ids})
