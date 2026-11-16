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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Internal reference generation for product templates."""
from odoo import api, models

from .product_product import generate_internal_refs, get_internal_ref_config


class ProductTemplate(models.Model):  # pylint: disable=abstract-method
    """Generate internal references (default codes) for product templates.

    References are generated on the variants, which are created together
    with the template; a single-variant template shows its variant's
    reference.
    """
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        """Keep the internal reference given on creation: Odoo only copies
        it to the variant when the variant has none, and the variant has
        already received a generated one."""
        res = super().create(vals_list)
        if get_internal_ref_config(self.env)['auto_generate']:
            for rec, vals in zip(res, vals_list):
                if vals.get('default_code'):
                    rec.default_code = vals['default_code']
        return res

    @api.model
    def action_generate_internal_ref(self):
        """Generate the internal reference of every variant of the selected
        templates that does not have one yet."""
        generate_internal_refs(
            self.browse(self.env.context.get('active_ids', []))
            .mapped('product_variant_ids').filtered(
                lambda product: not product.default_code))
