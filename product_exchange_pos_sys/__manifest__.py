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
    'name': 'POS Product Exchange',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "Allows to exchange the products in a pos order",
    'description': "The app allows user to select and change the product of pos"
                   "orders and add new products to the order during exchange.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_order_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'product_exchange_pos_sys/static/src/js/models.js',
            'product_exchange_pos_sys/static/src/js/AllOrderScreen.js',
            'product_exchange_pos_sys/static/src/js/OrderButton.js',
            'product_exchange_pos_sys/static/src/js/ExchangeOrder.js',
            'product_exchange_pos_sys/static/src/scss/pos.scss'
        ],
        'web.assets_qweb': [
            'product_exchange_pos_sys/static/src/xml/AllOrderScreen.xml',
            'product_exchange_pos_sys/static/src/xml/ExchangeOrder.xml',
            'product_exchange_pos_sys/static/src/xml/OrderButton.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
