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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Odoo Telegram Integration',
    'version': '16.0.1.0.0',
    'summary': 'Send Telegram messages directly from Odoo records',
    'description': '''This module integrates Telegram with Odoo, allowing users to 
    send messages directly from Odoo documents such as Sales Orders, Purchase Orders,
    Invoices,and other business records.
    ''',
    'category': 'Discuss',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail', 'crm', 'contacts', 'sale_management', 'account', 'purchase', 'stock', 'sale_stock'],
    'data': [
        'data/ir_module_category_data.xml',
        'data/telegram_template_data.xml',
        'security/ir.model.access.csv',
        'security/telegram_chatbox_groups.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/telegram_bot_views.xml',
        'views/telegram_message_views.xml',
        'views/telegram_template_views.xml',
        'views/menus.xml',
        'wizard/telegram_test_views.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
