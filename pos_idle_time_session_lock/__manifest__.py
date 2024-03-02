# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rosmy (<https://www.cybrosys.com>)
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
    'name': "POS Idle Session Lock",
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """The Module Allows the POS User to Set Screen Lock for POS 
    Screen""",
    'description': """This module allows pos user to lock pos screen and the 
    screen is idle it will also lock when the screen is idle""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'point_of_sale', 'pos_hr'],
    'data': [
        'views/pos_config_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_idle_time_session_lock/static/src/js/session_timer.js',
        ],
        'web.assets_qweb': [
            'pos_idle_time_session_lock/static/src/xml/session_timer.xml'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
