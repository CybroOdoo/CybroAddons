# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'User Wise Button Restrict In POS ',
    'version': '15.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': """This module is used to restrict button based on user""",
    'description': 'Pos buttons can be restricted to the users.Buttons is '
                   'restricted if we enable the fields in res user.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'pos_loyalty'],
    'data': {
        'views/res_users_views.xml',
    },
    'assets': {
        'point_of_sale.assets': [
            'pos_button_visibility/static/src/js/models_load.js',
        ],
        'web.assets_qweb': [
            'pos_button_visibility/static/src/xml/RewardButton.xml',
            'pos_button_visibility/static/src/xml/NumpadWidget.xml',
            'pos_button_visibility/static/src/xml/RefundButton.xml'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
