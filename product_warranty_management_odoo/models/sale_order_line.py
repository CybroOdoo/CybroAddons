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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """Keep the warranty expiry date of each sold product on its line."""
    _inherit = 'sale.order.line'

    is_warranty_available = fields.Boolean(
        related='product_id.is_warranty_available',
        help='The product of this line is sold with a warranty.')
    warranty_duration = fields.Integer(
        related='product_id.warranty_duration',
        help='Warranty duration of the product in months.')
    warranty_expiry_date = fields.Date(
        compute='_compute_warranty_expiry_date', store=True,
        help='Order date plus the warranty duration of the product.')

    @api.depends('order_id.date_order', 'product_id')
    def _compute_warranty_expiry_date(self):
        """Compute the expiry date from the order date. The product's
        duration is read when the line or order date changes, so a later
        change of the product's duration does not alter sold warranties."""
        for line in self:
            product = line.product_id
            if product.is_warranty_available and line.order_id.date_order:
                line.warranty_expiry_date = (
                    line.order_id.date_order.date()
                    + relativedelta(months=product.warranty_duration))
            else:
                line.warranty_expiry_date = False
