# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Web Responsive",
    'version': '17.0.1.0.1',
    'category': 'Extra Tools',
    'summary': 'This module helps to create enterprise like app drawer,'
               'Responsiveness and sticky headers included.',
    'description': """This module helps to create enterprise like app drawer,
     Responsiveness and sticky headers included.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'views/responsive_web_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'responsive_web/static/src/css/main_menu.css',
            'responsive_web/static/src/css/sticky.css',
            'responsive_web/static/src/xml/WebMenu.xml',
            'responsive_web/static/src/xml/PivotCustom.xml',
            'responsive_web/static/src/js/WebMenu.js',
            'responsive_web/static/src/xml/SearchResult.xml',
            'responsive_web/static/src/xml/ResponsiveWebTemplates.xml',
            'responsive_web/static/src/js/SearchResult.js',
            'responsive_web/static/src/js/ResponsiveWeb.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
