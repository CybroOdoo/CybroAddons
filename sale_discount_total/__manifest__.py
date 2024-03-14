# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen(odoo@cybrosys.com)
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
    'name': 'Sale Discount on Total Amount',
    'version': '17.0.1.0.0',
    'category': 'Sales Management',
    'summary': "Discount on Total in Sale and Invoice With Discount Limit "
               "and Approval",
    'description': "This module is designed to manage discounts on the total "
                   "amount in sales. It will include features to apply "
                   "discounts either as a specific amount or a percentage. "
                   "This module will enhance the functionality of Odoo's sales "
                   "module, allowing users to easily manage and apply discounts"
                   " to sales orders based on their requirements.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'live_test_url': 'https://www.youtube.com/watch?v=CigmHe9iC4s&feature=youtu.be',
    'depends': ['sale_management', 'account'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/account_move_templates.xml',
        'views/sale_order_templates.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
