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
    'name': "Product Multi UoM",
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'This module helps to sell a product with multiple UoM categories',
    'description': "This versatile module empowers your sales strategy by "
                   "seamlessly handling products with diverse unit of measure "
                   "categories. Whether you're selling by length, weight, "
                   "quantity, or more, this module ensures a streamlined and "
                   "efficient process, allowing you to offer and sell your "
                   "products with different UOM categories effortlessly.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': [
        'security/ir.access.csv',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/sale_order_line_views.xml',
        'views/secondary_uom_line_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
