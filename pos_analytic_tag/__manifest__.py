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
    'name': "PoS Analytic Tag",
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'To manage analytic tags in POS',
    'description': "This module assists in managing analytic tags in the "
                   "Point of Sale. It enables the use of analytic filters in" 
                   "reporting, facilitating analysis based on these tags.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'analytic', 'account'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/pos_config_views.xml',
        'views/pos_session_views.xml',
        'views/pos_order_views.xml',
        'views/pos_payment_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_analytic_tag/static/src/js/PosSession.js',
        ],
        'web.assets_unit_tests': [
            'pos_analytic_tag/static/tests/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
