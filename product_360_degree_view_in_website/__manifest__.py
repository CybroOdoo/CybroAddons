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
    'name': "Product 360 Degree View in Website",
    'version': '20.0.1.0.0',
    'category': 'eCommerce',
    'summary': """View the product from all angles in eCommerce.""",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['product', 'website_sale'],
    'data': ['security/ir.access.csv',
             'views/product_template_views.xml',
             'views/product_product_views.xml',
             'views/360_view_templates.xml',
             ],
    'assets': {'web.assets_frontend': [
        'product_360_degree_view_in_website/static/src/js/360_view.js',
        'product_360_degree_view_in_website/static/src/css/360_view.css'
    ], },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
