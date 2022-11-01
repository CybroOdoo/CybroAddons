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
    'name': 'Systray Menu Favourites',
    'version': '15.0.1.0.0',
    'summary': 'Systray Menu Favourites',
    'description': """ Menu Favourites In Systray""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Tools',
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.png'],
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv'
    ],
    'assets': {
        'web.assets_backend': [
            'systray_menu_shortcut/static/src/js/systray.js',
            'systray_menu_shortcut/static/src/css/systray.css'
        ],
        'web.assets_qweb': [
            'systray_menu_shortcut/static/src/xml/systray_view.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
