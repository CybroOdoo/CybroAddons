# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "website customer e-wallet",
    'version': '16.0.1.0.0',
    'category': 'Website',
    'summary': 'Enables wallet in portal.in odoo community',
    'description': "This module allows us to use our wallet from website."
                   "By using this wallet ,we can transfer the amount tot "
                   "another person ,add amount into it.we can use the wallet for"
                   "future purchases.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'sale_management', 'loyalty', 'portal', 'website_sale',
                'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_data_templates.xml',
        'data/ir_sequence_data.xml',
        'views/portal_views.xml',
        'views/forgot_pin_templates.xml',
        'views/login_templates.xml',
        'views/wallet_templates.xml',
        'views/res_config_settings_views.xml',
        'views/res_users_views.xml',
        'views/wallet_history_templates.xml',
        'views/add_wallet_money_templates.xml',
        'views/wallet_change_pin_templates.xml',
        'views/customer_wallet_transactions_views.xml',
        'wizard/wallet_amount_views.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'website_customer_wallet/static/src/js/wallet_info.js',
            'website_customer_wallet/static/src/js/add_wallet_money.js',
            'website_customer_wallet/static/src/js/wallet_login.js',
            'website_customer_wallet/static/src/js/wallet_transfer.js',
            'website_customer_wallet/static/src/js/forgot_pin.js',
            'website_customer_wallet/static/src/js/change_pin.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
