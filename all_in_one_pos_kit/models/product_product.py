# -*- coding: utf-8 -*-
#############################################################################
#
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
from odoo.exceptions import ValidationError



class ProductProduct(models.Model):
    """
       Inherit product.product model for adding fields
    """
    _inherit = 'product.product'

    is_age_restrict = fields.Boolean(
        related="product_tmpl_id.is_age_restrict",
        store=True,
        readonly=False
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Extends the result of the _load_pos_data_fields method by appending
          the 'is_age_restrict' field."""
        result = super()._load_pos_data_fields(config_id)
        # An empty list means that every field is loaded already.
        if result and 'is_age_restrict' not in result:
            result.append('is_age_restrict')
        return result

    product_multi_barcodes_ids = fields.One2many(
        'multi.barcode.products','product_multi_id',
        help="Multiple Barcodes for the product", string='Barcodes')

    @api.model_create_multi
    def create(self, vals_list):
        """
           Create new product records with the provided values and update
           the associated multi-barcode product template.
        """
        products = super().create(vals_list)
        for product in products:
            product.product_multi_barcodes_ids.update({
                'template_multi_id': product.product_tmpl_id.id
            })
        return products

    def write(self, vals):
        """
               Update the product record with the provided values and update
               the associated multi-barcode product template.
        """
        res = super().write(vals)
        for product in self:
            product.product_multi_barcodes_ids.update({
                'template_multi_id': product.product_tmpl_id.id
            })
        return res

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        """ Raise validation error if bom is not set in 'product.product'."""
        if self.to_make_mrp and not self.bom_count:
            raise ValidationError(
                self.env._('Please set Bill of Material for this product.'))
