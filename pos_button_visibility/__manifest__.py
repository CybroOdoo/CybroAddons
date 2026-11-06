# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
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
################################################################################
{
    'name': 'POS Button Visibility by User',
    'version': '18.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': (
        'Configure POS button restrictions for each user.'
    ),
    'description': (
        'Administrators can configure which POS buttons are available to '
        'each user. Restrictions apply to the active POS user.'
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'pos_loyalty'],
    'data': [
        'security/ir.model.access.csv',
        'data/pos_buttons_data.xml',
        'views/res_users.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_button_visibility/static/src/js/ControlButtons.js',
            'pos_button_visibility/static/src/js/numpad_button.js',
            'pos_button_visibility/static/src/xml/RewardButton.xml',
            'pos_button_visibility/static/src/xml/RefundButton.xml',
        ],
        'web.assets_tests': [
            'pos_button_visibility/static/tests/tours/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
