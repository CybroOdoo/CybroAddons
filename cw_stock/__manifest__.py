# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': "Catch Weight - Stock",
    'version': '17.0.1.0.0',
    'category': 'Warehouse',
    'summary': """Catch Weight Management In Inventory Module""",
    'description': """This module brings the catch weight system in the 
    Inventory module.We can enable the catch weight for each product, Stock 
    Moves and .""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock_account', 'uom'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_return_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_valuation_layer_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
