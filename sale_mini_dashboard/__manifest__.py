# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Sale Mini Dashboard',
    'version': '15.0.1.0.0',
    'category': 'Sales',
    'summary': 'Mini dashboard for Sales, Displays the total amount and count '
               'of Quotations and Sale Orders',
    'description': """This module is developed for displaying the count of 
    quotations and sale orders, total amount for sale orders and total 
    amount for quotations.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': ['views/sale_order_views.xml'],
    'assets': {
        'web.assets_backend': [
            'sale_mini_dashboard/static/src/js/sale_dashboard.js',
        ],
        'web.assets_qweb': [
            'sale_mini_dashboard/static/src/xml/sale_dashboard_views.xml'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
