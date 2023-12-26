# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'POS Automate Invoice',
    'version': '16.0.1.0.0',
    'summary': """To manage the POS Invoice Automatically""",
    'description': """This module facilitates the automated sending of invoices
     to customers, along with the ability to schedule emails at specific 
     intervals. Additionally, it empowers users to download invoices 
     based on predefined conditions within the configuration settings.""",
    'category': 'Sales',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['account', 'point_of_sale'],
    'website': 'https://www.cybrosys.com',
    'data': [
        'data/send_mail_template.xml',
        'data/send_mail_cron.xml',
        'views/res_config_settings.xml',
        'views/pos_order.xml',
        'views/pos_config.xml',
        'views/ir_cron.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_invoice_automate/static/src/js/PaymentScreen.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
