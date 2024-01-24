# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Hide Any Menu User Wise',
    'version': '14.0.1.1.1',
    'category': 'Extra Tools',
    'summary': 'Hide Menu,hide menu, hide, hide menus, hide menu odoo,Hide Any Menu Item User Wise',
    'description': 'Hide Menu,hide menu, hide, hide menus, hide menu odoo,Hide Any Menu Item User Wise, Hide Menu Items, Hide Menu',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_users.xml',
        'wizard/import__menu_list_views.xml',
    ],
    "external_dependencies": {
        "python": [
                "openpyxl",
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
