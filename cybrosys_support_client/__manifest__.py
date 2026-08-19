# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
##############################################################################
{
    'name': "Cybrosys Support Assistant",
    "version": "19.0.1.0.1",
    "category": "Productivity ",
    "summary": "Get Technical/Functional Assistance from Cybrosys without leaving your Database",
    "description": """Get Technical/Functional Assistant from Cybrosys without leaving your Odoo Database, Cybrosys Support, Functional Support, Technical Support""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter_data.xml',
        'wizard/client_support_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'cybrosys_support_client/static/src/js/client_support_systray.js',
            'cybrosys_support_client/static/src/js/client_support_user_menu.js',
            'cybrosys_support_client/static/src/xml/client_support_systray.xml',
            'cybrosys_support_client/static/src/css/client_support.css',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
