# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP(odoo@cybrosys.com)
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
    'name': 'Picking Order Line Views',
    'version': "15.0.1.0.0",
    'category': 'Sales',
    'summary': """Provide a Detailed View of Stock Picking Order Lines""",
    'description': """This app provides a detailed view of stock picking order 
     lines, including images and all necessary fields, 
     making it easier to understand.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale', 'stock', 'sale_management', 'purchase'],
    'data': [
        'views/stock_move_line_in_operation_views.xml',
        'views/stock_move_line_out_operation_views.xml'
    ],
    'images': ['static/description/banner.png'],
    'licence': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
