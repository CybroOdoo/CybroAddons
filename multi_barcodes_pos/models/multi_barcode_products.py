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
from odoo import fields, models, api


class MultiBarcodeProducts(models.Model):
    """
       Model for storing multiple barcode details
    """
    _name = 'multi.barcode.products'
    _description = 'For creating multiple Barcodes for products'

    multi_barcode = fields.Char(string="Barcode",
                                help="Provide alternate barcodes for this "
                                     "product")
    product_multi_id = fields.Many2one('product.product',
                                    string="Product",
                                    help="Multi Barcode Product")
    template_multi_id = fields.Many2one('product.template',
                                     string="Product",
                                     help="Product with Multi Barcode")

    _sql_constraints = [('field_unique', 'unique(multi_barcode)',
                         'Existing barcode is not allowed !'),]

    @api.model
    def get_barcode_val(self, barcode):
        temp = self.search([('multi_barcode', '=', barcode)])
        """returns barcode of record in self and product id"""
        return temp.multi_barcode, temp.product_multi_id.id
