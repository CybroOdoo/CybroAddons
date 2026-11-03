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
    'name': "Website Product Stock",
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Allows users to see stock details of products from the website',
    'description': """Helps to display the stock details of each product on 
     the website. It includes options to show product stock information 
     conditionally based on predefined location types and stock types.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale_stock'],
    'data': [
        'views/product_stock_information_snippet_view.xml',
        'views/product_template_view.xml',
        'views/res_config_settings_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_product_stock_information/static/src/scss/product_stock.scss',
            'website_product_stock_information/static/src/xml/website_product_stock_information_templates.xml',
        ],
        'website.website_builder_assets': [
            'website_product_stock_information/static/src/website_builder/product_stock.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
