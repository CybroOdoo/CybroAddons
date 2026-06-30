# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Global Search',
    'version': '18.0.1.0.1',
    'category': 'Extra Tools',
    'summary': """Easy Search in Customers, Products, Sale, Purchase, Inventory
    and Accounting modules""",
    'description': """This module allows users to search the records in
    Customers, Products, Sale, Purchase, Inventory and Accounting Modules.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'stock', 'sale', 'purchase'],
    'data': [
        'security/master_search_security.xml',
        'security/ir.model.access.csv',
        'views/master_search_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'master_search/static/src/scss/master_search.scss',
            'master_search/static/src/js/master_search.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
