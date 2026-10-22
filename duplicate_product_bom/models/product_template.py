# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Product template model extension to duplicate BOMs on template copy."""
from odoo import models


class ProductTemplate(models.Model):
    """Inherits from 'product.template' model and extends the 'copy' method."""
    _inherit = 'product.template'

    def copy(self, default=None):
        """Overrides default 'copy' to copy BOM information with template.

        Args:
            default (dict, optional): Default values for the new record
                being created.

        Returns:
            ProductTemplate: A new instance or recordset of product template
                with copied BOM information.
        """
        results = super().copy(default)
        for template, template_copy in zip(self, results):
            variant_mapping = {}
            if (len(template.product_variant_ids) == 1
                    and len(template_copy.product_variant_ids) == 1):
                variant_mapping[template.product_variant_ids.id] = (
                    template_copy.product_variant_ids.id
                )
            else:
                copy_variants_by_key = {
                    frozenset(
                        v.product_template_variant_value_ids
                        .product_attribute_value_id.ids
                    ): v.id
                    for v in template_copy.product_variant_ids
                }
                for variant in template.product_variant_ids:
                    key = frozenset(
                        variant.product_template_variant_value_ids
                        .product_attribute_value_id.ids
                    )
                    if key in copy_variants_by_key:
                        variant_mapping[variant.id] = copy_variants_by_key[key]

            for bom in template.bom_ids:
                bom_copy_vals = {
                    'product_tmpl_id': template_copy.id,
                }
                if bom.product_id:
                    bom_copy_vals['product_id'] = variant_mapping.get(
                        bom.product_id.id, False
                    )
                else:
                    bom_copy_vals['product_id'] = False

                if any(line.bom_product_template_attribute_value_ids
                       for line in bom.bom_line_ids):
                    ptav_mapping = {
                        (ptav.attribute_id.id,
                         ptav.product_attribute_value_id.id): ptav.id
                        for ptav in (template_copy.attribute_line_ids
                                     .product_template_value_ids)
                    }
                    bom_line_commands = []
                    for line in bom.bom_line_ids:
                        line_vals = line.copy_data()[0]
                        if line.bom_product_template_attribute_value_ids:
                            new_ptav_ids = [
                                ptav_mapping[(val.attribute_id.id,
                                              val.product_attribute_value_id.id)]
                                for val in line.bom_product_template_attribute_value_ids
                                if (val.attribute_id.id,
                                    val.product_attribute_value_id.id) in ptav_mapping
                            ]
                            line_vals['bom_product_template_attribute_value_ids'] = [
                                (6, 0, new_ptav_ids)
                            ]
                        bom_line_commands.append((0, 0, line_vals))
                    bom_copy_vals['bom_line_ids'] = bom_line_commands

                bom.copy(bom_copy_vals)

        return results
