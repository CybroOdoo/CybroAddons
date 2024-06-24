# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo.http import Controller, request, route


class Agent(Controller):
    """ Class for the function to render a new page """
    @route(route='/agent/shop', auth='user', website=True)
    def agent(self):
        """ Function to pass the data to shop and also to clearing the cart """
        customer_ids = request.env['res.partner'].search(
            [('agent_id', '=', request.env.user.partner_id.id)])
        return request.render('shopping_through_agent.agent_shop_template',
                              {'customer_ids': customer_ids})
