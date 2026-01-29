# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Subina (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Scan Product Barcode for Sale & Purchase",
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Scan Barcode from Camera.""",
    'description': """Products can be added to sale or purchase orders by 
    scanning barcode of products through system camera. Products will be 
    automatically added to order line once the barcode is identified.""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale_management', 'purchase'],
    'data': [
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'barcode_capturing_sale_purchase/static/src/js/sale_barcode.js',
            'barcode_capturing_sale_purchase/static/src/js/purchase_barcode.js',
            'barcode_capturing_sale_purchase/static/src/js/quagga.js',
            'barcode_capturing_sale_purchase/static/src/css/styles.css'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
