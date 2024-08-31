# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ajith V(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    """
    This class extends the 'sale.order' model to include a new field
    'delivery_status' which tracks the delivery status of the sale order.
    """
    _inherit = 'sale.order'

    delivery_status = fields.Selection(
        selection=[
            ('nothing', 'Nothing to Deliver'),
            ('to_deliver', 'To Deliver'),
            ('partial', 'Partially Delivered'),
            ('delivered', 'Delivered'),
            ('processing', 'Processing')
        ],
        string='Delivery Status',
        compute='_compute_delivery_status',
        store=True,
        readonly=True,
        copy=False,
        default='nothing'
    )

    @api.depends('state', 'order_line.qty_delivered')
    def _compute_delivery_status(self):
        """
        Computes the delivery status of the sale order based on the state of
        related stock pickings and quantities delivered in the order lines.
        """
        for rec in self:
            pickings = self.env['stock.picking'].search(
                [('sale_id', '=', rec.id)])
            orderlines = rec.mapped('order_line').filtered(
                lambda x: x.product_id.type != 'service')
            service_orderlines = rec.mapped('order_line').filtered(
                lambda x: x.product_id.type == 'service')

            if not pickings and not service_orderlines:
                rec.delivery_status = 'nothing'
            elif all(o.qty_delivered == 0 for o in orderlines):
                rec.delivery_status = 'to_deliver'
            elif orderlines.filtered(
                    lambda x: x.qty_delivered < x.product_uom_qty):
                rec.delivery_status = 'partial'
            elif all(o.qty_delivered == o.product_uom_qty for o in orderlines):
                rec.delivery_status = 'delivered'
            if any(p.state in ('waiting', 'confirmed') for p in pickings):
                rec.delivery_status = 'processing'
            if not orderlines and service_orderlines and rec.state == 'sale':
                rec.delivery_status = 'delivered'
