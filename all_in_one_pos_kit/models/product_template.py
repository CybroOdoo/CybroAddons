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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Inherited product.template to add field"""
    _inherit = 'product.template'

    is_age_restrict = fields.Boolean(string="Is Age Restricted",
                                     help="Enable if the product is age "
                                          "restricted")
    product_template_ids = fields.One2many('multi.barcode.product',
                                              'product_template_id',
                                              string='Barcodes',
                                              help='Add multi barcode for the '
                                                   'module')
    to_make_mrp = fields.Boolean(string='To Create MRP Order',
                                 help="Check if the product should be make mrp "
                                      "order")

    @api.model
    def create(self, vals):
        """Super the create function to update the field product_template_ids"""
        res = super(ProductTemplate, self).create(vals)
        res.product_template_ids.update({
            'product_id': res.product_variant_id.id
        })
        return res

    def write(self, vals):
        """Super the write function to update the field product_template_ids"""
        res = super(ProductTemplate, self).write(vals)
        if self.product_template_ids:
            self.product_template_ids.update({
                'product_id': self.product_variant_id.id
            })
        return res

    @api.onchange('to_make_mrp')
    def _onchange_to_make_mrp(self):
        """Function to show raise error if the product doesn't have BOM"""
        if self.to_make_mrp:
            if not self.bom_count:
                raise ValidationError(
                    'Please set Bill of Material for this product.')
