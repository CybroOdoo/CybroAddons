# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER 
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Ecommerce Barcode Search',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Search for website products using barcodes',
    'description': """
        This module enables users to search for products on the website using barcodes.
        It adds a barcode scanner button and camera modal to the website shop page,
        allowing customers to quickly find specific products by scanning barcodes.
        Scanning a product barcode automatically redirects to the product page and selects
        the corresponding product variant.
    """,

    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': [
        'views/website_sale_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ecommerce_barcode_search/static/src/scss/website_sale_barcode.scss',
            'ecommerce_barcode_search/static/src/js/WebsiteSaleBarcode.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
