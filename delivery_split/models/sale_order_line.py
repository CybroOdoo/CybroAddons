# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (Contact : odoo@cybrosys.com)
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
from datetime import timedelta
from odoo.addons.sale_stock.models.sale_order_line import SaleOrderLine


class SaleOrderLine(models.Model):
    """ Inherits model 'sale.order.line' and added field 'recipient'  """
    _inherit = 'sale.order.line'

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
        if self.order_id.delivery_split:
            for line in self:
                if not line.recipient_id:
                    line.recipient_id = self.order_id.partner_id.id

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be
        created from a stock rule coming from a sale order line. This method
        could be override in order to add other custom key that could be used
        in move/po creation."""
        date_deadline = self.order_id.commitment_date or (
                self.order_id.date_order + timedelta(
            days=self.customer_lead or 0.0))
        date_planned = date_deadline - timedelta(
            days=self.order_id.company_id.security_lead)
        values = {
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'date_deadline': date_deadline,
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'product_description_variants': self.with_context(
                lang=self.order_id.partner_id.lang).
            _get_sale_order_line_multiline_description_variants(),
            'company_id': self.order_id.company_id,
            'product_packaging_id': self.product_packaging_id,
            'sequence': self.sequence,
        }
        if not self.recipient_id:
            self.recipient_id = self.order_id.partner_id.id
        if self.order_id.delivery_split:
            values.update({"partner_id": self.recipient_id.id})
        return values
    SaleOrderLine._prepare_procurement_values = _prepare_procurement_values
