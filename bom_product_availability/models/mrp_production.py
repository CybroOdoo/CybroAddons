# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models, fields, _


class ProductCount(models.Model):
    """Available products that can be made using Bill of Materials"""
    _inherit = "mrp.production"

    product_count = fields.Integer(string="Available Quantity",
                                   compute="_compute_product_count_bom",
                                   help="Number of products that can be made "
                                        "using available BOMs.")
    check_quant = fields.Boolean(string="Check Quantity",
                                 help="To check before warning message")

    @api.depends('product_id')
    def _compute_product_count_bom(self):
        """Check number of products that can be made using available BOMs"""
        for record in self:
            record.product_count = ''
            product_id = record.bom_id.bom_line_ids.mapped('product_id')
            bom_quantity = record.bom_id.bom_line_ids.mapped('product_qty')
            product_quantity = [products.qty_available for products in
                                product_id]
            product_count_min = []
            for bom_quant, product_quant in zip(bom_quantity, product_quantity):
                available_quantity = product_quant / bom_quant
                product_count_min.append(available_quantity)
            if 0 in product_quantity:
                record.product_count = 0
                record.check_quant = True
            elif len(product_count_min) != 0:
                record.product_count = min(product_count_min)

    @api.onchange('bom_id')
    def _onchange_product_count(self):
        """If available quantity of product is zero or less than zero, show warning message """
        if self.bom_id:
            if self.check_quant or self.product_count <= 0:
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _('There is no available BOM quantities to '
                                     'complete the manufacture'),
                    }
                }
