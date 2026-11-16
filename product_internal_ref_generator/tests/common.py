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
"""Common setup for the internal reference generator tests."""
from odoo.tests.common import TransactionCase

PARAM_PREFIX = 'product_internal_ref_generator.'
SEQUENCE_NUMBER = r'\d{5}$'


class InternalRefCommon(TransactionCase):
    """Common setup for the internal reference generator tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.config_parameter = cls.env['ir.config_parameter'].sudo()
        cls.set_config(
            auto_generate_internal_ref=True,
            product_name_config=True, pro_name_digit=3,
            pro_name_separator='-',
            pro_categ_config=True, pro_categ_digit=3,
            pro_categ_separator='_',
            pro_template_config=True, pro_template_digit=2,
            pro_template_separator='/',
        )
        cls.category = cls.env['product.category'].create({
            'name': 'Furniture',
        })
        cls.attribute = cls.env['product.attribute'].create({
            'name': 'Color',
            'create_variant': 'no_variant',
        })
        cls.value_red = cls.env['product.attribute.value'].create({
            'name': 'Red',
            'attribute_id': cls.attribute.id,
        })
        cls.value_blue = cls.env['product.attribute.value'].create({
            'name': 'Blue',
            'attribute_id': cls.attribute.id,
        })
        cls.size = cls.env['product.attribute'].create({
            'name': 'Size',
            'create_variant': 'always',
        })
        cls.size_small = cls.env['product.attribute.value'].create({
            'name': 'Small',
            'attribute_id': cls.size.id,
        })
        cls.size_large = cls.env['product.attribute.value'].create({
            'name': 'Large',
            'attribute_id': cls.size.id,
        })

    @classmethod
    def set_config(cls, **values):
        """Store the given settings with the typed config parameter API."""
        for key, value in values.items():
            if isinstance(value, bool):
                cls.config_parameter.set_bool(PARAM_PREFIX + key, value)
            elif isinstance(value, int):
                cls.config_parameter.set_int(PARAM_PREFIX + key, value)
            else:
                cls.config_parameter.set_str(PARAM_PREFIX + key, value)
