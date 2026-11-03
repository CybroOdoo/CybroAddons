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
    'name': "POS Multi Currency Payment",
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "Multi-currency payment support for Point of Sale in Odoo 20.",
    'description': """POS Multi Currency Payment
==============================
This module enables accepting payments in multiple foreign currencies in Point of Sale.
It allows cashiers to select a currency, view conversion rates, and record payments
in the chosen currency while updating the order totals accurately.
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/pos_order_receipt.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'multi_currency_payment_in_pos/static/xml/multicurrency_templates.xml',
            'multi_currency_payment_in_pos/static/src/js/pos_multicurrency.js',
            'multi_currency_payment_in_pos/static/src/js/backend_order.js',
            'multi_currency_payment_in_pos/static/src/scss/multicurrency.scss',
        ],
        'point_of_sale.assets_debug': [
            'multi_currency_payment_in_pos/static/tests/tours/pos_multicurrency_tour.js',
        ],
        'web.assets_tests': [
            'multi_currency_payment_in_pos/static/tests/tours/pos_multicurrency_tour.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
