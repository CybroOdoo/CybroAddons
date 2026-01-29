# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """ Inherits sale.order.line to add the new fields for delivery address """
    _inherit = 'sale.order.line'

    delivery_addr_id = fields.Many2one(
        'res.partner', string="Delivery Address",
        domain="[('parent_id', '=', order_partner_id)]",
        help="You can select from the delivery addresses of the same customer")
    is_address_readonly = fields.Boolean(
        default=False, compute="_compute_is_address_readonly")

    @api.depends('product_id')
    def _compute_is_address_readonly(self):
        """ This function will compute the is_address_readonly field.
        The field is used to make delivery address field in sale order line
        a readonly field if the product is a service. """
        for rec in self:
            rec.is_address_readonly = False
            if rec.product_id.type == 'service':
                rec.is_address_readonly = True
