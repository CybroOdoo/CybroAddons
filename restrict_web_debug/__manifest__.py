# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': 'Userwise Developer Mode Restriction',
    'version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Userwise Developer Mode Restriction',
    "description": "Restric Developer Mode for Specific Users, Disable Developer Mode,Restrict Debug mode User wise,Developer mode restriction userwise",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/res_users.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'restrict_web_debug/static/src/core/debug/debug_menu_basic_inherit.js',
            'restrict_web_debug/static/src/core/debug/template_view.xml',
        ],

    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
