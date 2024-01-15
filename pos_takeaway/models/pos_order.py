# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class PosOrder(models.Model):
    """
    Inheriting and adding field is_takeaway and this field is used for filter pos orders
    """
    _inherit = 'pos.order'

    is_takeaway = fields.Boolean(default=False, string="Is a Takeaway Order",
                                 help="Is a Takeaway Order")

    @api.model
    def token_generate(self, uid):
        """
        This function is used for generating token number for takeaway
        orders
        """
        uid = "Order " + uid[0]
        # Directly search for pos.order
        order = self.env['pos.order'].search([
            ('pos_reference', 'ilike', uid)], limit=1)
        order.is_takeaway = True
        if order and order.config_id:
            if order.config_id.is_generate_token:
                # Find the associated pos.config record
                order.config_id.pos_token += 1
                return order.config_id.pos_token
