# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(odoo@cybrosys.com)
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
from odoo import fields, models


class MassOrderConfirmation(models.TransientModel):
    """
    Creates the model mass.order.confirmation for the wizard to confirm the
    sale order and the purchase order
    """
    _name = 'mass.order.confirmation'
    _description = 'Mass Order Confirmation'

    is_sale_order = fields.Boolean(string="Is Sale Order",
                                   help="True if confirming is sale order")
    is_purchase_order = fields.Boolean(string="Is Purchase Order",
                                       help="True if confirming the purchase "
                                            "order")
    sale_order_ids = fields.Many2many('sale.order', string="Sale Orders",
                                      help="Sale Orders to confirm", domain=[
            ('state', 'in', ('draft', 'sent'))])
    purchase_order_ids = fields.Many2many('purchase.order',
                                          string="Purchase Orders",
                                          help="Purchase Orders to confirm",
                                          domain=[
                                              ('state', 'in',
                                               ('draft', 'sent'))])

    def action_confirm_orders(self):
        """
        Method action_confirm_orders to confirm multiple Sale Orders or Purchase
        Orders from the list view itself.
        """
        if self.is_sale_order:
            for order in self.sale_order_ids:
                order.action_confirm()
        else:
            for order in self.purchase_order_ids:
                order.button_confirm()
