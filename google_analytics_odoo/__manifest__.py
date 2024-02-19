# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
    'name': "All In One Google Analytics",
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': 'By connecting Google Analytics to Odoo and tracking relevant '
               'events, you can make data-driven decisions, improve user'
               'experience, and enhance the overall performance of your '
               'application.',
    'description': 'Integrating Odoo with Google Analytics allows businesses to'
                   'track user interactions and events within the Odoo '
                   'application and send that data to their Google Analytics '
                   'account.This integration empowers businesses to improve '
                   'user experience and overall application performance.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'purchase', 'account', 'website_sale'],
    'data': ['views/res_config_settings_views.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
