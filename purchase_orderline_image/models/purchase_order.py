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


class PurchaseOrder(models.Model):
    """Inheriting purchase order"""
    _inherit = 'purchase.order'

    show_product_image_setting = fields.Boolean(
        string="Show Product Image Setting",
        compute="_compute_show_product_image_setting",
        help="Technical field to check if product images should be shown"
    )

    def _compute_show_product_image_setting(self):
        """Compute whether to show product image based on settings"""
        show_image = self.env['ir.config_parameter'].sudo().get_bool(
            'purchase_orderline_image.show_product_image_in_report_purchase'
        )
        for order in self:
            order.show_product_image_setting = show_image