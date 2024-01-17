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
from odoo import api, fields, models, _


class ProductProduct(models.Model):
    """Inherit the product_product module to add new fields"""
    _inherit = 'product.product'

    product_multi_barcodes_ids = fields.One2many('multi.barcode.product',
                                             'product_id',
                                                 string='Barcodes',
                                             help='Add multi barcode for '
                                                  'product')

    @api.model
    def create(self, vals):
        """Super the create function to update the field
        product_multi_barcodes_ids"""
        res = super(ProductProduct, self).create(vals)
        res.product_multi_barcodes_ids.update({
            'product_template_id': res.product_tmpl_id.id
        })
        return res

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
