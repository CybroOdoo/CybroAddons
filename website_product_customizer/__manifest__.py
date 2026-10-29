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
    'name': 'Website Product Customizer',
    'version': '20.0.1.0.0',
    'category': 'Website,eCommerce,Sales,Extra Tools',
    'summary': 'Product customization designer for eCommerce',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'website',
        'website_sale',
        'sale',
        'product',
    ],
    'data': [
        # Security
        'security/ir.access.csv',
        'security/product_design_customization_security.xml',

        # Data
        'data/ir_sequence_data.xml',
        'data/product_public_category_data.xml',
        'data/product_design_template_tag_data.xml',
        'data/product_design_font_data.xml',
        'data/product_design_color_data.xml',

        # Views - Backend

        'views/product_design_template_views.xml',
        'views/product_design_font_views.xml',
        'views/product_design_color_views.xml',
        'views/product_design_customization_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',

        # Views - Frontend
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_product_customizer/static/lib/fabric/fabric.min.js',
            'website_product_customizer/static/src/scss/designer.scss',
            'website_product_customizer/static/src/js/designer.js',
            'website_product_customizer/static/src/js/product_page_button.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
