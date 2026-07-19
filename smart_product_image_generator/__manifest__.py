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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Smart Product Image Generator',
    'version': '19.0.1.0.0',
    'category': 'Sales/Products',
    'summary': 'Generate professional product images using AI (OpenAI DALL-E 3, Stability AI, Google Gemini)',
    'description': """
    Generate AI-powered product images directly in Odoo using OpenAI, Stability AI, and Google Gemini.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'mail', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_config_parameter_data.xml',
        'data/server_action_data.xml',
        'views/res_config_settings_views.xml',
        'views/product_template_views.xml',
        'views/ai_image_generation_log_views.xml',
        'wizard/smart_product_image_generator_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'smart_product_image_generator/static/src/css/product_ai_image.css',
            'smart_product_image_generator/static/src/xml/image_lightbox.xml',
            'smart_product_image_generator/static/src/js/image_lightbox.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}