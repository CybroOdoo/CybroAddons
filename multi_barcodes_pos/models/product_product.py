# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gee Paul Joby (odoo@cybrosys.com)
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


class ProductProduct(models.Model):
    """
       Inherit product.product model for adding fields
    """
    _inherit = 'product.product'

    product_multi_barcodes_ids = fields.One2many(
        'multi.barcode.products', 'product_multi_id',
        help="Multiple Barcodes for the product", string='Barcodes')

    @api.model_create_multi
    def create(self, vals_list):
        """
           Create new product records with the provided values and update
           the associated multi-barcode product template.
        """
        products = super().create(vals_list)
        products._sync_multi_barcode_template()
        return products

    def write(self, vals):
        """
           Update the product records with the provided values and update
           the associated multi-barcode product template.
        """
        res = super().write(vals)
        if 'product_multi_barcodes_ids' in vals:
            self._sync_multi_barcode_template()
        return res

    def _sync_multi_barcode_template(self):
        """
           Link the multi-barcodes of each product to its template, writing
           only the barcodes that are not linked yet.
        """
        for product in self:
            product.product_multi_barcodes_ids.filtered(
                lambda b: b.template_multi_id != product.product_tmpl_id
            ).write({'template_multi_id': product.product_tmpl_id.id})
