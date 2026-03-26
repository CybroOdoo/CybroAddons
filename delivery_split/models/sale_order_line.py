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

class SaleOrderLine(models.Model):
    """ Inherits model 'sale.order.line' and added field 'recipient'  """
    _inherit = 'sale.order.line'
    _description = 'Sale Order Line Delivery Split'

    recipient_id = fields.Many2one('res.partner', string='Recipient',
                                   help='Choose a recipient for splitting '
                                        'delivery',
                                   domain=['|', ('company_id', '=', lambda
                                       self: self.env.company.id),
                                           ('company_id', '=', False)])

    @api.onchange("product_template_id")
    def _onchange_product_template_id(self):
        """Update recipients in order lines with the customer of sale order as
        default recipient"""
        res = super(SaleOrderLine, self)._onchange_product_template_id() if (
            hasattr(super(SaleOrderLine, self),
             '_onchange_product_template_id')) else None
        if self.order_id.is_delivery_split:
            for line in self:
                if not line.recipient_id:
                    line.recipient_id = self.order_id.partner_id.id
        return res

    def _prepare_procurement_values(self, **kwargs):
        """ Add partner_id to procurement values if delivery_split is enabled """
        values = super(SaleOrderLine, self)._prepare_procurement_values(**kwargs)

        if not self.recipient_id:
            self.recipient_id = self.order_id.partner_id.id

        if self.order_id.is_delivery_split:
            values.update({"partner_id": self.recipient_id.id})

        return values
