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
{
    'name': 'Generate Product Images Using OpenAI',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Generate product images with OpenAI directly from product templates.',
    'description': """This module lets product managers generate images for product templates
with OpenAI from a text prompt. The generated images are kept in a history
list on the product and can be set as the main product image.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['product', 'openai_odoo_base'],
    'data': [
        'security/ir.access.csv',
        'views/product_template_views.xml',
        'views/openai_image_suggestion_views.xml',
        'wizard/image_suggestion_views.xml',
    ],
    'external_dependencies': {
        'python': ['openai'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
