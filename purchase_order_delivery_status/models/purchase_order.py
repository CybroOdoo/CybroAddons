# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    """ Add the delivery status to purchase orders. """
    _inherit = 'purchase.order'

    delivery_status = fields.Selection(selection=[
        ('nothing', 'Nothing to Receive'), ('to_receive', 'To Receive'),
        ('partial', 'Partially Received'), ('received', 'Received')],
        compute='_compute_delivery_status', store=True,
        help="Delivery status of the purchase order.")

    @api.depends(
        'state',
        'picking_ids',
        'order_line.qty_received',
        'order_line.product_qty',
        'order_line.product_id.type',
    )
    def _compute_delivery_status(self):
        """ Compute the delivery status of each purchase order. """
        for rec in self:
            orderlines = rec.order_line
            if rec.state in ('draft', 'sent', 'to approve', 'cancel'):
                rec.delivery_status = 'nothing'
            elif not orderlines:
                rec.delivery_status = 'nothing'
            elif not rec.picking_ids and not orderlines.filtered(
                    lambda x: x.product_id.type == 'service'):
                rec.delivery_status = 'nothing'
            elif all(o.qty_received == 0 for o in orderlines):
                rec.delivery_status = 'to_receive'
            elif orderlines.filtered(lambda x: x.qty_received < x.product_qty):
                rec.delivery_status = 'partial'
            else:
                rec.delivery_status = 'received'
