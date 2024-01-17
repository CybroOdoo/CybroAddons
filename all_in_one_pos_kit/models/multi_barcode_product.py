# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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


class ProductMultiBarcode(models.Model):
    """Created new model to add store multi barcode for product"""
    _name = 'multi.barcode.product'
    _description = 'For creating multiple Barcodes for products'

    multi_barcode = fields.Char(string="Barcode",
                                help="Provide alternate barcodes for this "
                                     "product")
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 help='Related product name in product.product'
                                      ' model')
    product_template_id = fields.Many2one('product.template',
                                          string='Product template',
                                          help='Related product name in '
                                               'product.template model')
    _sql_constraints = [('field_unique', 'unique(multi_barcode)',
                         'Existing barcode is not allowed !'), ]

    def get_barcode_val(self, product):
        """Returns barcode of record in self and product id"""
        return self.multi_barcode, product
