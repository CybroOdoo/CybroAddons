# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'LocationLink POS',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Syncing products with their location in the Point of Sale (POS) system.""",
    'description': """This module makes it easy for you to enhance the management of products within the POS system by categorizing them according to their physical location.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale', 'stock'],
    'data': [
        'views/res_config_setting_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_load_products_location/static/src/js/pos_store_path.js',
            'pos_load_products_location/static/src/js/ProductsWidget.js',
        ],
    },
    "images": ["static/description/banner.jpg"],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
