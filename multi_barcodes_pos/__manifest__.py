# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
#############################################################################
{
    'name': 'POS Product Multi Barcode',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Allows to create multiple barcode for a single product""",
    'description': """This module allows you to set multiple barcodes for a 
     product and product varients""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com/',
    'depends': ['product', 'point_of_sale', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/product_product_views.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'multi_barcodes_pos/static/src/js/PosStore.js',
            'multi_barcodes_pos/static/src/js/pos_scan.js',
            'multi_barcodes_pos/static/src/js/ProductWidget.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
