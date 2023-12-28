# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#
#############################################################################
{
    'name': "PostgreSQL Query Execute Odoo16",
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Run the PSQL query in the Odoo user interface.""",
    'description': """This module helps you execute a query directly
     in the Odoo interface and output your query in Excel.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/psql_query_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'psql_query_execute/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
