# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Picking Order Line Views',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': """Picking Order Lines Views is helpful for the Detailed view of the picking
     order lines including the product images""",
    'description': """Picking Order Line Detailed Views Shows us the Transfer Order with 
    images of their related products in the tree view of stock move lines""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale', 'stock', 'sale_management', 'purchase'],
    'data': [
        'views/stock_move_line_views.xml',
        'views/stock_picking_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'licence': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
