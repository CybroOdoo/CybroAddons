# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu (odoo@cybrosys.com)
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
################################################################################

from odoo import fields, models


class ProductMultiBarcode(models.Model):
    """For creating multiple Barcodes per product"""
    _name = 'product.multiple.barcodes'
    _rec_name = 'product_multi_barcode'

    product_multi_barcode = fields.Char(string="Barcode",
                                        help="Provide alternate barcodes for this product")
    product_barcode = fields.Many2one('product.product', string='Product Barcode')
    template_barcode = fields.Many2one('product.template', string='Template Barcode')
    _sql_constraints = [
        ('field_unique', 'unique(product_multi_barcode)',
         'Existing barcode is not allowed !'),
    ]

    def get_barcode_val(self, product):
        """returns barcode of record in self and product id"""
        return self.product_multi_barcode, product
