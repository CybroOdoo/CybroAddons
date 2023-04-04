# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Pos Access Rights',
    'version': '16.0.1.0.0',
    'summary': 'Restrict Accesses',
    'category': 'Point of Sale',
    'description': 'Restrict Point of Sale Access',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/res_users_view.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_user_access_rights/static/src/js/product_screen_buttons.js',
            'pos_user_access_rights/static/src/js/ticket_screen.js',
            'pos_user_access_rights/static/src/js/numpad.js',
            'pos_user_access_rights/static/src/js/plus_minus.js',
            'pos_user_access_rights/static/src/js/numpad_keys.js',
            'pos_user_access_rights/static/src/js/partner_payment.js'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
