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
{
    'name': 'Website WebAR Product Viewer',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': "Realistic 3D and Augmented Reality product view for eCommerce",
    'description': """This module helps customers view products in 3D on the
website. Customers can experience interactive AR commerce using WebAR
technology. This gives customers a realistic view of the product, showing how
it will look in real-life environments.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        "views/product_template_views.xml",
        "views/website_sale_templates.xml",
    ],
    'demo': ["data/product_template_demo.xml"],
    'assets': {
        'web.assets_frontend': [
            'website_webar_product/static/src/js/website_product_view.js',
            'website_webar_product/static/src/css/website_product_view.css',
        ],
        'web.assets_unit_tests': [
            'website_webar_product/static/tests/**/*',
        ],
        'web.assets_unit_tests_setup': [
            'website_webar_product/static/src/js/website_product_view.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
