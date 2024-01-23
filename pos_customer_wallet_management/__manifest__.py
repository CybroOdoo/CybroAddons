# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'POS Customer Wallet Management',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'This Module Helps to Manage Customer Wallet in POS.',
    'description': """This Module Helps to Manage Customer Wallet in POS.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'contacts', 'account', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/res_partner_views.xml',
        'views/wallet_transaction_views.xml',
        'views/account_journal_views.xml',
        'views/pos_payment_method_views.xml',
        'wizard/recharge_wallet_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
         'pos_customer_wallet_management/static/src/js/customerListScreen.js',
         'pos_customer_wallet_management/static/src/js/payment_method.js',
         'pos_customer_wallet_management/static/src/js/wallet_recharge.js',
         'pos_customer_wallet_management/static/src/xml/balance_templates.xml',
         'pos_customer_wallet_management/static/src/xml/partner_templates.xml',
         'pos_customer_wallet_management/static/src/xml/wallet_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
