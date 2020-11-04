# -*- coding: utf-8 -*-
###################################################################################
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': "Advanced Product Price Update",
    'version': '14.0.1.0.0',
    'summary': """User Can Easily Update Cost Price/Sale Price of Products""",
    'description': """This module updates price of any product on single click""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.Cybrosys.com",
    'category': 'Tools',
    'depends': ['base', 'sale'],
    'data': [
        'views/product_price_view.xml',
        'security/ir.model.access.csv'
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
