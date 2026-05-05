# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
{
    'name': 'User Wise Button Restrict In POS',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Restrict POS buttons based on user and session',
    'description': """This module allows administrators to control the visibility of
    buttons in the Point of Sale (POS) interface based on the logged-in
    user and active session. It helps in restricting specific actions
    for different users to improve control and usability.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['pos_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/pos_button_data.xml',
        'views/res_users_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_button_visibility/static/src/js/control_buttons_patch.js',
            'pos_button_visibility/static/src/js/product_screen_numpad_patch.js',
            'pos_button_visibility/static/src/xml/control_buttons_refund.xml',
            'pos_button_visibility/static/src/xml/control_buttons_reward.xml',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
