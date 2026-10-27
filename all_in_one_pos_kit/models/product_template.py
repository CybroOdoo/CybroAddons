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


class ProductTemplate(models.Model):
    """
       Inherit product.template model for adding fields
    """
    _inherit = 'product.template'

    template_multi_barcodes_ids = fields.One2many(
        'multi.barcode.products','template_multi_id',
        string='Barcodes', help="Multiple Barcodes for the product")
    to_make_mrp = fields.Boolean(
        string='To Create MRP Order',
        help="Check if the product should make mrp order")
    is_age_restrict = fields.Boolean(string="Is Age Restricted",
                                     help="By enabling age restrictions on a "
                                          "product")

    @api.model
    def _load_pos_data_fields(self, config):
        """Load the age restriction flag in the POS (product.template is the
        main product model of the Odoo 19 POS)."""
        result = super()._load_pos_data_fields(config)
        # An empty list means that every field is loaded already.
        if result:
            result += [name for name in ('is_age_restrict', 'to_make_mrp')
                       if name not in result]
        return result

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        """ Raise validation error if bom is not set in 'product.template'."""
        if self.to_make_mrp and not self.bom_count:
            raise ValidationError(self.env._(
                'Please set Bill of Material for this product.'))


    @api.model_create_multi
    def create(self, vals_list):
        """
           Create new product template records with the provided values
           and update the associated multi-barcode product.
        """
        templates = super().create(vals_list)
        for template in templates:
            template.template_multi_barcodes_ids.update({
                'product_multi_id': template.product_variant_id.id
            })
        return templates

    def write(self, vals):
        """
           Update the product template record with the provided values and
           Update the associated multi-barcode product.
        """
        res = super().write(vals)
        for template in self:
            if template.template_multi_barcodes_ids:
                template.template_multi_barcodes_ids.update({
                    'product_multi_id': template.product_variant_id.id
                })
        return res
