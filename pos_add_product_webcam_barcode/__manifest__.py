# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
    'name': "Add Product using Webcam Barcode in Pos",
    'version': '15.0.1.0.0',
    'category': 'Point of sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'summary': 'Add the order-line using webcam scanner by adding barcode '
               'of products',
    'description': """This module helps you to scan a product barcode using
     Webcam and add the products to pos order-line.""",
    'images': ['static/description/banner.png'],
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'point_of_sale.assets': [
            'pos_add_product_webcam_barcode/static/src/css/dialog.css',
            'pos_add_product_webcam_barcode/static/src/js/quagga.js',
            'pos_add_product_webcam_barcode/static/src/js/PosBarcode.js',
        ],
        'web.assets_qweb': [
            'pos_add_product_webcam_barcode/static/src/xml/ProductScreen.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
    'application': False,
}
