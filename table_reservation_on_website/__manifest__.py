# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
    'name': 'Table Reservation on Website',
    'version': '17.0.1.0.0',
    'category': 'eCommerce,Point of Sale',
    'summary': 'Reserve tables in POS from website',
    'description': """This module enables to reserve tables in POS from website.
     User will be able to select the floor, table, date and time.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'website_sale', 'pos_restaurant'],
    'data': [
        'security/ir.model.access.csv',
        'data/table_reservation_data.xml',
        'data/product_product_data.xml',
        'views/table_reservation_templates.xml',
        'views/table_reservation_on_website_menus.xml',
        'views/restaurant_table_views.xml',
        'views/restaurant_floor_views.xml',
        'views/table_reservation_views.xml',
        'views/sale_order_views.xml',
        'views/table_reserved_templates.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'table_reservation_on_website/static/src/js/PaymentScreen.js',
            'table_reservation_on_website/static/src/js/FloorScreen.js',
            'table_reservation_on_website/static/src/xml/FloorScreen.xml',
            'table_reservation_on_website/static/src/scss/style.css',
        ],
        'web.assets_frontend': [
            'table_reservation_on_website/static/src/js/table_reservation.js',
            'table_reservation_on_website/static/src/js/reservation_floor.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
