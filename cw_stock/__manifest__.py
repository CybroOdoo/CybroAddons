# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
    'name': " Catch Weight Management: Inventory",
    'version': '15.0.1.0.0',
    'category': 'Warehouse',
    'summary': """Helps to manage Catch Weight of products in Inventory
     module""",
    'description': """ Catch weight is simply a parallel unit of measure used 
     to manage variable-weight products. This module helps to deal with Catch 
     Weight in Inventory module. It is possible to enable the Catch Weight for 
     each Product. Catch Weight is available in stock moves and scrap 
     orders.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock_account'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_return_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_valuation_layer_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
