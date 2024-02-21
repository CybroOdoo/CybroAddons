# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    """
      Model representing a sales order.
      This class extends the 'sale.order' model and adds additional functionality
      specific to sales orders.
      """
    _inherit = 'sale.order'

    @api.model
    def get_pending_tasks(self, order_id):
        """
        Retrieve sale order based on a specific order ID. :param order_id:
        The ID of the sale order to retrieve. :return: A dictionary
        representing an action to open the sale order.
        """
        return {
            'name': "Sale Order",
            'type': "ir.actions.act_window",
            'res_model': 'sale.order',
            'domain': [('id', '=', order_id)],
            'view_mode': "tree,form",
            'views': [[False, "tree"], [False, "form"]],
            'target': 'main',
        }
