# -*- coding: utf-8 -*-
###############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Lesser General Public License(LGPLv3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Delivery Gate Pass',
    'summary': """Generating Gate pass slip in delivery orders""",
    'version': '15.0.1.0.0',
    'description': """This module facilitates the creation of gate pass slips 
                      for users, which can be used as a pass to let a vehicle 
                      into a facility. The slips allow for the addition of 
                      driver and vehicle-related information.""",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'category': 'Inventory/Delivery',
    'depends': ['base', 'stock'],
    'license': 'LGPL-3',
    'data': [
        'views/stock_picking_views.xml',
        'report/stock_picking_reports.xml',
        'report/stock_picking_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
