# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class SaleOrder(models.Model):
    """Inherits 'sale.order' and adds new field"""
    _inherit = 'sale.order'
    _description = 'Sale Order Delivery Split'

    is_delivery_split = fields.Boolean(string='Delivery Split',
                                       help='Enable the option to add recipients '
                                            'to each sale order line to split '
                                            'delivery')
    is_consolidate = fields.Boolean(string='Consolidate Orders',
                                    help='Enable the option to consolidate '
                                         'orders if choose same recipients in '
                                         'split delivery')

    @api.onchange("partner_id")
    def _onchange_product_template_id(self):
        """ Update recipients in order lines with the customer of sale order
        is changed """
        if self.is_delivery_split:
            for line in self.order_line:
                line.recipient_id = self.partner_id.id
