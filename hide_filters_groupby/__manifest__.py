# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ASWIN A K (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Hide Filters GroupBy',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Hide Filters GroupBy Helps You to Hide Filter And'
               ' GroupBy Option.',
    'description': 'Hide Filters GroupBy Helps you to Hide Filter and'
                   ' Group by Option on the Basis of Globally or Custom. On '
                   'Choosing Option Globally Filter and Group by Option of'
                   ' all Models will be Hide and on Choosing Option Custom,'
                   ' Filter and Group by Option of all Selected Models will'
                   ' be Hidden.',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hide_filters_groupby/static/src/js/control_panel.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
