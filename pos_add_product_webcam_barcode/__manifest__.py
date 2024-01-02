# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
#
#    You can modify it under the terms of the General Public License, (LGPL v3),
#    Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    General Public License, Version 3 (LGPL v3) for more details.
#
#    You should have received a copy of the General Public License, Version 3
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "Add Product using Webcam Barcode in Pos",
    'version': '14.0.1.0.0',
    'category': 'Point of Sale',
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
    'qweb': [
      'static/src/xml/PosBarcode.xml',
    ],
    'data': [
        'views/assets.xml',
    ],
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'auto_install': False,
}
