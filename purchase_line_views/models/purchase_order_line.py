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


class PurchaseOrderLine(models.Model):
    """ For adding product image directly
    to purchase order line from product"""

    _inherit = 'purchase.order.line'

    product_image = fields.Binary(
        related="product_id.image_1920",
        string="Image",
        help='For getting product image '
             'to purchase order line')

    @api.depends('product_id.display_name', 'name')
    def _compute_display_name(self):
        super()._compute_display_name()
        if self.env.context.get('is_purchase_line_view'):
            for line in self:
                if line.product_id:
                    line.display_name = line.product_id.display_name

    @api.onchange('order_id')
    def _onchange_order_id(self):
        """ Warn when selecting a purchase order in locked, cancel,
            or confirmed purchase states while in RFQ line view."""
        if self.env.context.get('is_rfq_line') and self.order_id:
            if self.order_id.state in ['cancel', 'done', 'purchase']:
                return {
                    'warning': {
                        'title': self.env._("Warning"),
                        'message': self.env._(
                            "You cannot select a purchase order in "
                            "cancel, locked, or purchase order state."
                        ),
                    }
                }
