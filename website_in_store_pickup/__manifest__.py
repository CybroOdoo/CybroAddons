# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
    'name': "Website In-Store Pickup",
    'version': '16.0.1.0.0',
    'category': 'eCommerce',
    'summary': 'To manage the in-store pickups of orders ',
    'description': "To facilitate the management of in-store pickups, we have"
                   "implemented a system to handle customer orders that can "
                   "be picked up at the physical store location. This system "
                   "allows customers to place orders online and then select "
                   "the option to pick up their purchases at the store.",
    'author': " Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'delivery', 'stock', 'website_sale'],
    'data': [
        'views/stock_warehouse_views.xml',
        'views/delivery_carrier_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_in_store_pickup/static/src/js/website_in_store_pickup.js',
            'website_in_store_pickup/static/src/xml/website_in_store_pickup_'
            'templates.xml',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
