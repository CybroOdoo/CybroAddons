# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj(odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Sales Person On POS Order Line',
    'Version': '16.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'This module is used to set sales persons on pos order line',
    'description': 'This module allows you to assign salespersons to order'
                   'lines in the Point of Sale (POS)',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_orderline_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'salesperson_pos_order_line/static/src/js/pos_load_data.js',
            'salesperson_pos_order_line/static/src/js/pos_screen.js',
            'salesperson_pos_order_line/static/src/js/pos_orderline.js',
            'salesperson_pos_order_line/static/src/js/pos_popup.js',
            'salesperson_pos_order_line/static/src/xml/pos_screen_templates.xml',
            'salesperson_pos_order_line/static/src/xml/pos_popup_templates.xml',
            'salesperson_pos_order_line/static/src/xml/orderline_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
