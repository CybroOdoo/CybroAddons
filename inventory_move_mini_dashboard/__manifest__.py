# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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
############################################################################
{
    'name': 'Inventory Move Mini Dashboard',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Mini Dashboard View for Stock Moves and Transfers',
    'description': 'Module offers a user-friendly mini dashboard for '
                   'stock moves and transfers, providing real-time data '
                   'visualization to efficiently track inventory movement',
    'author': 'Cybrosys Techno Solution',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solution',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'stock'],
    'data': [
        'views/stock_move_views.xml',
        'views/stock_picking_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_move_mini_dashboard/static/src/views/*.js',
            'inventory_move_mini_dashboard/static/src/**/*.xml',
        ]},
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto-install': False,
    'application': False,
}
