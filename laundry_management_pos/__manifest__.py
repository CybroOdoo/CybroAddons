# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "POS Laundry Management",
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Launch Automatic Laundry Orders After selling Through POS.""",
    'description': """It manages the Point of sale laundry process with assigning works to workers.We can create 
     Laundry orders with the help of POS.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'laundry_management'],
    'data': [
        'views/pos_config_views.xml',
        'views/laundry_order_views.xml',
        'views/pos_order_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'laundry_management_pos/static/src/css/pos.css',
        ],
         'point_of_sale.assets':  [
            'laundry_management_pos/static/src/xml/button/washing_type_button.xml',
            'laundry_management_pos/static/src/js/button/washing_type_button.js',
            'laundry_management_pos/static/src/js/screen/washing_type_popup.js',
            'laundry_management_pos/static/src/xml/screen/washing_type_popup.xml',
            'laundry_management_pos/static/src/js/models.js',
            'laundry_management_pos/static/src/js/order_line.js',
            'laundry_management_pos/static/src/js/pos_receipt.js',
            'laundry_management_pos/static/src/xml/pos_receipt.xml',
            'laundry_management_pos/static/src/js/product_img.js',
            'laundry_management_pos/static/src/xml/product_img.xml',
            'laundry_management_pos/static/src/js/screen/product_screen.js',
            'laundry_management_pos/static/src/css/pos.css',
            'laundry_management_pos/static/src/xml/button/product_create_button.xml',
            'laundry_management_pos/static/src/js/button/product_create_button.js',
            'laundry_management_pos/static/src/js/screen/product_create_popup.js',
            'laundry_management_pos/static/src/xml/screen/product_create_popup.xml'
         ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
