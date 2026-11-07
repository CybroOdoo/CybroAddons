#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Inherits Product template for multi barcode feature"""
    _inherit = 'product.template'

    template_multi_barcode_ids = fields.One2many(
        'product.multiple.barcodes',
        'product_template_id',
        string='Multi Barcodes',
        help="Multiple barcodes for the product template",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Creating the multi barcodes"""
        res = super().create(vals_list)
        for template in res:
            if template.template_multi_barcode_ids:
                variant = template.product_variant_id or template.product_variant_ids[:1]
                if variant:
                    for mb in template.template_multi_barcode_ids:
                        if not mb.product_id:
                            mb.product_id = variant.id
        return res

    def write(self, vals):
        """Updating the multi barcodes"""
        res = super().write(vals)
        for template in self:
            if template.template_multi_barcode_ids:
                variant = template.product_variant_id or template.product_variant_ids[:1]
                if variant:
                    for mb in template.template_multi_barcode_ids:
                        if not mb.product_id:
                            mb.product_id = variant.id
        return res
