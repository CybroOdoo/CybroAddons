# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import  fields, models


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
        show_image = self.env['ir.config_parameter'].sudo().get_param(
            'purchase_orderline_image.show_product_image_in_report_purchase',
            default=False
        )
        for order in self:
            order.show_product_image_setting = bool(show_image)