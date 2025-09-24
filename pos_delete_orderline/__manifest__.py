# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
{
    'name': "Remove Order Line In POS",
    'version': '18.0.1.0.1',
    'category': 'Point of Sale',
    'summary': """Remove Individual Orderlines In Point Of Sale. """,
    'description': """Remove each lines from selected order by simply 
    clicking X button or clear all order with a single click.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_delete_orderline/static/src/app/control_buttons/control_buttons.js',
            'pos_delete_orderline/static/src/app/control_buttons/control_buttons.xml',
            'pos_delete_orderline/static/src/app/screens/product_screen/product_screen.js',
            'pos_delete_orderline/static/src/app/screens/product_screen/product_screen.xml',
            'pos_delete_orderline/static/src/scss/style.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
