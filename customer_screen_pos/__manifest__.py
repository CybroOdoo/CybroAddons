# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Customer Screen POS",
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'This helps customers finalize their order and may add rating '
               'and review.',
    'description': "A separate POS screen for customers to know their ordered "
                   "products and add their review and rating about services",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_config_views.xml',
        'views/pos_order_views.xml',
        'views/pos_orderlines_templates.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            '/customer_screen_pos/static/src/js/pos_systray_icon.js',
            '/customer_screen_pos/static/src/js/product_click.js',
        ],
        'web.assets_qweb': [
            '/customer_screen_pos/static/src/xml/pos_systray_icon.xml',
        ],
        'web.assets_frontend': [
            'customer_screen_pos/static/src/css/customer_screen_pos.css'
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
