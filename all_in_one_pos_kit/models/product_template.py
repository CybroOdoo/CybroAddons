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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Inherited product.template to add field"""
    _inherit = 'product.template'

    is_age_restrict = fields.Boolean(string="Is Age Restricted",
                                     help="Enable if the product is age "
                                          "restricted")
    template_multi_barcodes = fields.One2many('multi.barcode.product',
                                              'template_multi',
                                              string='Barcodes')
    to_make_mrp = fields.Boolean(string='To Create MRP Order',
                                 help="Check if the product should be make "
                                      "mrp order")

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        """
        Checks if the product has a Bill of Materials set when 'to_make_mrp'
         is True.
        Raises a ValidationError if no BOM exists.
        """
        if self.to_make_mrp:
            if not self.bom_count:
                raise ValidationError(
                    'Please set Bill of Material for this product.')

    @api.model
    def create(self, vals):
        """
        Creates a new product template. Updates 'template_multi_barcodes' with
         the new product variant ID.
        """
        res = super(ProductTemplate, self).create(vals)
        res.template_multi_barcodes.update({
            'product_multi': res.product_variant_id.id
        })
        return res

    def write(self, vals):
        """
           Updates an existing product template. Ensures
           'template_multi_barcodes' is updated if present.
        """
        res = super(ProductTemplate, self).write(vals)
        if self.template_multi_barcodes:
            self.template_multi_barcodes.update({
                'product_multi': self.product_variant_id.id
            })
        return res
