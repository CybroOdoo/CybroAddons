# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
    _inherit = ['pos.load.mixin']
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

    _name_uniq = models.Constraint(
        'unique(multi_barcode)',
        'Existing barcode is not allowed !',
    )


    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Specify additional fields to load into the POS frontend.

        This method defines the fields of the current model that should be
        loaded and made available in the Point of Sale during initialization.

        :param int config_id: ID of the POS configuration
        :return: List of field names to load in POS
        :rtype: list
        """
        return ['multi_barcode', 'product_multi_id', 'template_multi_id']


    @api.model
    def get_barcode_val(self, barcode):
        """
        Fetch multi-barcode details for a given barcode.

        This method searches for a record matching the provided barcode and
        returns the barcode value along with the related product template ID.

        :param str barcode: Barcode value to search for
        :return: Tuple containing the barcode and product template ID
        :rtype: tuple(str, int)
        """
        temp = self.search([('multi_barcode', '=', barcode)], limit=1)
        return temp.multi_barcode, temp.template_multi_id.id
