# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class MultiProductBarcode(models.Model):
    """
    A model for managing multiple barcodes for products in Odoo.
    """
    _name = 'multi.barcode.product'

    multi_barcode = fields.Char(string="Barcode",
                                help="Provide alternate barcodes "
                                     "for this product")
    product_multi = fields.Many2one('product.product')
    template_multi = fields.Many2one('product.template')

    def get_barcode_val(self, product):
        """
        Retrieve the barcode value along with the associated product.

        Args:
            product (recordset): The product record associated with the barcode.

        Returns:
            tuple: A tuple containing the barcode value (str) and the product
             (recordset).
        """
        return self.multi_barcode, product
