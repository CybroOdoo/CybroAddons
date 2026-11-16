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
"""Internal reference generation for product variants."""
from odoo import api, models

PARAM_PREFIX = 'product_internal_ref_generator.'
SEQUENCE_CODE = 'product.sequence.ref'
DEFAULT_DIGIT = 3
DEFAULT_SEPARATOR = '-'
TYPE_PREFIX = {
    'consu': 'Goods:',
    'service': 'Service:',
    'combo': 'Combo:',
}


def get_internal_ref_config(env):
    """Return the internal reference settings as a dictionary."""
    param = env['ir.config_parameter'].sudo()
    config = {
        'auto_generate': param.get_bool(
            PARAM_PREFIX + 'auto_generate_internal_ref'),
    }
    for part, enabled, digit, separator in (
            ('name', 'product_name_config', 'pro_name_digit',
             'pro_name_separator'),
            ('categ', 'pro_categ_config', 'pro_categ_digit',
             'pro_categ_separator'),
            ('attribute', 'pro_template_config', 'pro_template_digit',
             'pro_template_separator')):
        config[part] = param.get_bool(PARAM_PREFIX + enabled) and (
            param.get_int(PARAM_PREFIX + digit, DEFAULT_DIGIT),
            param.get_str(PARAM_PREFIX + separator, DEFAULT_SEPARATOR),
        )
    return config


def prepare_internal_ref(product, config):
    """Build the internal reference of a product variant.

    The reference is made of the product type, the first characters of the
    product name, of its category and of its attribute values (each part
    only when enabled in the settings), followed by the next number of the
    single sequence shared by all products, so references never repeat.
    """
    texts = []
    if config['name']:
        texts.append(('name', product.name))
    if config['categ']:
        texts.append(('categ', product.categ_id.name))
    if config['attribute']:
        values = (
            product.product_template_attribute_value_ids
            .product_attribute_value_id
            | product.attribute_line_ids.filtered(
                lambda line: line.attribute_id.create_variant == 'no_variant'
            ).value_ids)
        texts += [('attribute', value.name) for value in values]
    parts = [TYPE_PREFIX.get(product.type, '')]
    for part, text in texts:
        digit, separator = config[part]
        if text:
            parts += [text[:digit], separator]
    parts.append(product.env['ir.sequence'].next_by_code(SEQUENCE_CODE))
    return ''.join(parts)


def generate_internal_refs(products):
    """Write a generated internal reference on every given variant."""
    config = get_internal_ref_config(products.env)
    for product in products:
        product.default_code = prepare_internal_ref(product, config)


class ProductProduct(models.Model):  # pylint: disable=abstract-method
    """Generate internal references (default codes) for product variants."""
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        """Generate the internal reference of new variants when the
        auto-generate option is enabled and no reference was given."""
        res = super().create(vals_list)
        if get_internal_ref_config(self.env)['auto_generate']:
            generate_internal_refs(self.browse([
                rec.id for rec, vals in zip(res, vals_list)
                if not vals.get('default_code')]))
        return res

    @api.model
    def action_generate_internal_ref_pro(self):
        """Generate the internal reference of the selected variants that do
        not have one yet."""
        generate_internal_refs(
            self.browse(self.env.context.get('active_ids', [])).filtered(
                lambda product: not product.default_code))
