# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
    """Model for creating multiple Barcodes per product.

    This model is used to store alternate barcodes for a product. It includes
    fields for the barcode value, the corresponding product and template
    barcodes, and a constraint to ensure that each barcode is unique.

    Attributes:
        _name (str): Technical name of the model.
        _rec_name (str): Name of the field to use as the record name.
        product_multi_barcode (fields.Char): Field for storing the barcode value.
        product_barcode_id (fields.Many2one): Field for linking to the
        corresponding `product.product` record.
        template_barcode_id (fields.Many2one): Field for linking to the
        corresponding `product.template` record.
        _sql_constraints (list): List of SQL constraints to apply to the model.
    """

    _name = 'product.multiple.barcodes'
    _rec_name = 'product_multi_barcode'
    _description = 'Model for managing multiple barcodes for products,'

    product_multi_barcode = fields.Char(string="Barcode",
                                        help="Provide alternate "
                                             "barcodes for this product")
    product_barcode_id = fields.Many2one('product.product',
                                         string='Product Barcode',
                                         help='Select the product associated'
                                              ' with this barcode.')
    template_barcode_id = fields.Many2one('product.template',
                                          string='Template Barcode',
                                          help='Select the product template '
                                               'associated with this barcode.')

    _sql_constraints = [
        ('field_unique', 'unique(product_multi_barcode)',
         'Existing barcode is not allowed !'),
    ]

    def get_barcode_val(self, product):
        """Get the barcode value and corresponding product ID.

        This method returns a tuple with the barcode value and the ID of the corresponding
        `product.product` record.

        Args:
            product (product.product): The product to get the barcode value for.

        Returns:
            tuple: A tuple containing the barcode value and the product ID.
        """
        return self.product_multi_barcode, product
