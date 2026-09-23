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
    'name': 'POS Product Stock',
    'version': "20.0.1.0.0",
    'category': 'Point Of Sale',
    'summary': "Quantity of all Products in each Warehouse",
    'description': "Shows Stock quantity in POS for all Products in each "
                   "Warehouse, Odoo 19.5",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale', 'stock'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_product_stock/static/src/xml/product_item.xml',
            'pos_product_stock/static/src/css/product_quantity.scss',
            'pos_product_stock/static/src/js/pos_location.js',
            'pos_product_stock/static/src/js/pos_payment_screen.js',
            'pos_product_stock/static/src/js/pos_session.js',
            'pos_product_stock/static/src/js/deny_order.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
