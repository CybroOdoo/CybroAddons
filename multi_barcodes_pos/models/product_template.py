# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gee Paul Joby (odoo@cybrosys.com)
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


class ProductTemplate(models.Model):
    """
       Inherit product.template model for adding fields
    """
    _inherit = 'product.template'

    template_multi_barcodes_ids = fields.One2many(
        'multi.barcode.products', 'template_multi_id',
        string='Barcodes', help="Multiple Barcodes for the product")

    @api.model_create_multi
    def create(self, vals_list):
        """
           Create new product template records with the provided values
           and update the associated multi-barcode product.
        """
        templates = super().create(vals_list)
        templates._sync_multi_barcode_product()
        return templates

    def write(self, vals):
        """
           Update the product template records with the provided values and
           update the associated multi-barcode product.
        """
        res = super().write(vals)
        if 'template_multi_barcodes_ids' in vals:
            self._sync_multi_barcode_product()
        return res

    def _sync_multi_barcode_product(self):
        """
           Link the multi-barcodes without a variant to the template's main
           variant, keeping barcodes already set on a specific variant.
        """
        for template in self:
            template.template_multi_barcodes_ids.filtered(
                lambda b: not b.product_multi_id
            ).write({'product_multi_id': template.product_variant_id.id})
