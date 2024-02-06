# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Sale Order Line Views',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'This module enhances the sales management process by '
               'providing a comprehensive and detailed view of both sale '
               'orders and quotation lines within a business application.',
    'description': 'Users can access a consolidated and organized display of '
                   'sales-related information, allowing for a quick and '
                   'thorough analysis of order details and quotation lines. '
                   'This feature streamlines the workflow, improves efficiency,'
                   ' and facilitates better decision-making in the sales and '
                   'quoting processes.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management'],
    'data': [
        'views/quotation_line_views.xml',
        'views/sale_order_line_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_sale_order_line_views/static/src/scss/sale_order_ine.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'licence': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
