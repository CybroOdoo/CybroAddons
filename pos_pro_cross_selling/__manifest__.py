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
    'name': 'POS Cross-Selling',
    'version': '20.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': 'Cross Selling Products in POS',
    'description': "This module is used for cross-selling products in POS. "
                   "We can manage and use the cross-selling products in POS",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.access.csv',
        'views/pos_cross_selling_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            '/pos_pro_cross_selling/static/src/app/cross_product/cross_product.js',
            '/pos_pro_cross_selling/static/src/app/cross_product/cross_product.xml',
            '/pos_pro_cross_selling/static/src/js/ProductItem.js',
            '/pos_pro_cross_selling/static/src/scss/cross_product.scss'
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
