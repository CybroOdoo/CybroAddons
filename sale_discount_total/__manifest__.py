#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Sale Discount on Total Amount',
    'version': '20.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': "Discount on the total of sale orders and invoices with a "
               "discount limit and approval",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'live_test_url': 'https://www.youtube.com/watch?v=CigmHe9iC4s',
    'depends': ['sale', 'account'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/account_move_templates.xml',
        'views/sale_order_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
