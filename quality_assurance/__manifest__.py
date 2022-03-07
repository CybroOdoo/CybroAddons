# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: fasluca(<https://www.cybrosys.com>)
#
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': 'Quality Assurance',
    'version': '14.0.1.0.0',
    'summary': 'Manage Your Quality Assurance Processes',
    'description': """
    This module provides features to manage basic quality assurance procedures.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https:www.cybrosys.com",
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Inventory',
    'depends': ['product', 'stock', 'purchase'],
    'data': [
        'data/data.xml',
        'security/quality_security.xml',
        'security/ir.model.access.csv',
        'views/quality_view.xml',
        'views/stock_view.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True
}
