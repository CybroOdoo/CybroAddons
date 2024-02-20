# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
        'multi.barcode.products','product_multi_id',
        help="Multiple Barcodes for the product", string='Barcodes')

    @api.model
    def create(self, vals):
        """
           Create a new product record with the provided values and update
           the associated multi-barcode product template.
        """
        res = super(ProductProduct, self).create(vals)
        res.product_multi_barcodes_ids.update({
            'template_multi_id': res.product_tmpl_id.id
        })
        return res

    def write(self, vals):
        """
               Update the product record with the provided values and update
               the associated multi-barcode product template.
        """
        res = super(ProductProduct, self).write(vals)
        self.product_multi_barcodes_ids.update({
            'template_multi_id': self.product_tmpl_id.id
        })
        return res
