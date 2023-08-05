# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    'name': 'POS Order Management',
    'version': '15.0.1.0.0',
    'category': "Point of Sale",
    'summary': "Allows you to display all the old orders in Point of Sale",
    'description': "Detailed view of all orders with Order Reference, "
                   "Receipt Reference, Customer and Order Date",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/res_config_settings_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_all_orders/static/src/js/models.js',
            'pos_all_orders/static/src/js/all_order_button.js',
            'pos_all_orders/static/src/js/all_order_screen.js',
            'pos_all_orders/static/src/js/partner_screen.js',
            'pos_all_orders/static/src/scss/pos.scss'
        ],
        'web.assets_qweb': [
            'pos_all_orders/static/src/xml/all_order_button_templates.xml',
            'pos_all_orders/static/src/xml/all_order_screen_templates.xml',
            'pos_all_orders/static/src/xml/partner_screen_templates.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
