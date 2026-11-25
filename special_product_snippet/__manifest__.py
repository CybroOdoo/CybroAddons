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
    'name': 'Special Product Website Snippet',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': "Select Product and Multiple Templates for Product in "
               "Website Snippet",
    'description': "This module allows users to select a product and choose "
                   "from multiple layout templates in the website snippet.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        'views/special_product_snippet_templates.xml',
        'views/product_snippet_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'special_product_snippet/static/src/css/product_snippet.css',
            'special_product_snippet/static/src/xml/special_product_snippet.xml',
            'special_product_snippet/static/src/js/special_product_interaction.js',
        ],
        'website.assets_inside_builder_iframe': [
            'special_product_snippet/static/src/css/product_snippet.css',
            'special_product_snippet/static/src/xml/special_product_snippet.xml',
            'special_product_snippet/static/src/js/special_product_interaction.js',
        ],
        'website.website_builder_assets': [
            'special_product_snippet/static/src/xml/special_product_snippet.xml',
            'special_product_snippet/static/src/website_builder/special_product_option.xml',
            'special_product_snippet/static/src/website_builder/special_product_plugin.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
