# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class ProductProduct(models.Model):
    """Inherit the product_product module to add new fields"""
    _inherit = 'product.product'

    product_multi_barcodes_ids = fields.One2many('multi.barcode.products',
                                             'product_id',
                                                 string='Product Barcodes',
                                             help='Add multi barcode for '
                                                  'product')

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Extends the result of the _load_pos_data_fields method by appending
          the 'is_age_restrict' field."""
        result = super()._load_pos_data_fields(config_id)
        result.append('is_age_restrict')
        result.append('to_make_mrp')
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Super the create function to update the field
        product_multi_barcodes_ids"""
        products = super().create(vals_list)
        for product in products:
            product.product_multi_barcodes_ids.update({
                'product_template_id': product.product_tmpl_id.id
            })
        return products

    def write(self, vals):
        """Super the write function to update the field
        product_multi_barcodes_ids"""
        res = super(ProductProduct, self).write(vals)
        self.product_multi_barcodes_ids.update({
            'product_template_id': self.product_tmpl_id.id
        })
        return res

    @api.onchange('to_make_mrp')
    def _onchange_to_make_mrp(self):
        """Function to show raise error if the product doesn't have BOM"""
        if self.to_make_mrp and not self.bom_count:
            raise Warning(_('Please set Bill of Material for this product.'))
