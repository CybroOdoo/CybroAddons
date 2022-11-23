# -*- coding: utf-8 -*-
###################################################################################
#    POS Order Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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
    'name': 'POS Order Management',
    'version': '16.0.1.0.0',
    'category': "POS All Order's Management",
    'summary': "POS All Order's Management",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'description': "POS All Order's Management",
    'depends': ['base', 'point_of_sale'],
    'images': ['static/description/banner.png'],
    'data': [
        'views/res_config_settings.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_all_orders/static/src/js/models.js',
            'pos_all_orders/static/src/js/all_order_button.js',
            'pos_all_orders/static/src/xml/all_order_button.xml',
            'pos_all_orders/static/src/xml/all_order_screen.xml',
            'pos_all_orders/static/src/js/all_order_screen.js',
            'pos_all_orders/static/src/xml/partner_screen.xml',
            'pos_all_orders/static/src/js/partner_screen.js',
            'pos_all_orders/static/src/scss/pos.scss'
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
