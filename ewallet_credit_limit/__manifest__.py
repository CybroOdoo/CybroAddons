# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies M  (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,

#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################.
{
    'name': 'E-Wallet Credit Limit',
    'version': '17.0.1.0.0',
    'summary': 'Adds credit limit functionality to e-wallets',
    'description': """
        This module extends e-wallet functionality to include credit limits
        for customers and enforce them during transactions.
    """,
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'sale',
    'depends': ['sale_management', 'account', 'loyalty','point_of_sale' , 'website_sale'],
    'data': [
        'views/loyalty_card.xml',
    ],
    'assets': {
            'point_of_sale._assets_pos': [
                'ewallet_credit_limit/static/src/js/order_screen/pos_order.js',
                'ewallet_credit_limit/static/src/js/order_screen/order_line.js',
                'ewallet_credit_limit/static/src/js/payment_screen/pos_store.js',
                'ewallet_credit_limit/static/src/js/payment_screen/payment_screen.js',
            ],
        },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}