# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nikhil krishnan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Indent Management - MRP',
    'version': '10.0.1.0.0',
    'summary': """Create MRP Indents To Warehouse Team.""",
    'description': """When we create a MRP Order, MRP team need raw material and if we check the availability,
    an indnet is created automatically and only Warehouse manager can approve the indent""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Manufacturing',
    'depends': ['stock', 'mrp'],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_production_views.xml',
        'views/manufacturing_indent_menu.xml',
        'views/stock_indent_menu.xml',
        'views/mrp_indent_sequence.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
