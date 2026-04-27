# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys (odoo@cybrosys.com)
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


class MultiBarcodeProducts(models.Model):
    """
       Model for storing multiple barcode details
    """
    _name = 'multi.barcode.products'
    _description = 'For creating multiple Barcodes for products'
    _inherit = ['pos.load.mixin']

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
    def _load_pos_data_fields(self, config_id):
        return ['multi_barcode', 'product_multi_id', 'template_multi_id']

    @api.model
    def get_barcode_val(self, barcode):
        """returns barcode of record in self and product id"""

        temp = self.search([('multi_barcode', '=', barcode)])
        return temp.multi_barcode, temp.product_multi_id.id
