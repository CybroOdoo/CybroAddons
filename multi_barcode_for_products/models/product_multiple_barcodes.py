# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ADVAITH B G (odoo@cybrosys.com)
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
    """Creating multiple barcode for products"""
    _name = 'product.multiple.barcodes'
    _description = 'Product Multiple Barcodes'
    _rec_name = 'product_multi_barcode'

    product_multi_barcode = fields.Char(string="Barcode",
                                        help="Provide alternate barcodes for "
                                             "the product")
    product_id = fields.Many2one('product.product', string="Product Variant",
                                 help="This will be the Product "
                                      "variants")
    product_template_id = fields.Many2one('product.template', string="Product",
                                          help="This will be the products")
    _sql_constraints = [
        ('field_unique', 'unique(product_multi_barcode)',
         'Existing barcode is not allowed !'),
    ]

    def get_barcode_val(self, product):
        """
        Summary:
            get barcode of record in self and product id
        Args:
            product(int):current product
        Returns:
            barcode of the record in self and product
        """

        return self.product_multi_barcode, product
