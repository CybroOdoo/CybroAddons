# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Global Search',
    'version': '14.0.1.1.1',
    'summary': """Easy Search in Customers, Products, Sale, Purchase, Inventory and Accounting modules""",
    'description': """Search, Global Search, Quick Search, Easy Search, Easy Search in Customers, Products, Sale, Purchase, Inventory and Accounting modules, 
                      Search, Advance search, global search, odoo14, """,
    'category': 'Settings',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'depends': ['base', 'stock', 'sale', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/master_search_view.xml',
        'views/template.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
