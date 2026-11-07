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
from odoo import fields, models


class SaleOrder(models.Model):
    """Inherits sale.order to know whether line images must be shown."""
    _inherit = 'sale.order'

    is_image_true = fields.Boolean(
        string="Show Line Images", compute='_compute_is_image_true',
        help="Show product images in the sale order lines")

    def _compute_is_image_true(self):
        """Set True when the 'Show Product Image' setting is enabled."""
        show_image = self.env['ir.config_parameter'].sudo().get_bool(
            'sale_product_image.is_show_product_image_in_sale_report')
        for order in self:
            order.is_image_true = show_image
