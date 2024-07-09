# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
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
    'name': 'Find Products in Pos and Stock using Barcode',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Find Products in Pos and Stock using Barcode  utilizes barcode'
               ' scanning to quickly identify and track items. Each product'
               ' is assigned a unique barcode,',
    'description': 'Find Products in Pos and Stock using Barcode in the POS'
                   ' and inventory modules brings numerous benefits to '
                   'retailers.It enhances operational efficiency, reduces '
                   'manual errors, improves customer service, and provides '
                   'valuable insights for better inventory management and '
                   'business decision-making.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'stock'],
    'data': [
        'views/stock_views.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'product_detail_search/static/src/css/pos.css',
            'product_detail_search/static/src/js/find_product_button.js',
            'product_detail_search/static/src/js/find_product.js',
            'product_detail_search/static/src/js/product_details.js',
        ],
        'web.assets_qweb': [
            '/product_detail_search/static/src/xml/find_product_button_templates.xml',
            '/product_detail_search/static/src/xml/find_product_screen_templates.xml',
            '/product_detail_search/static/src/xml/product_details_templates.xml',
            '/product_detail_search/static/src/xml/chrome_templates.xml',
            '/product_detail_search/static/src/xml/dashboard_templates.xml',
        ],
        'web.assets_backend': [
            '/product_detail_search/static/src/css/barcode.css',
            '/product_detail_search/static/src/js/dashboard.js',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
