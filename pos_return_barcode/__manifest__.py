# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjhana A K (odoo@cybrosys.com)
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
    'name': 'POS Return Barcode',
    'version': '17.0.1.0.0',
    'summary': """This module in Odoo 17 allows to  return product effortless 
     via receipt barcode scanning.""",
    'description': """The POS Return Barcode module in Odoo 17 streamlines the
     return process by enabling users to return products through the scanning
      of the receipt barcode""",
    'category': 'Point of Sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/pos_order_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_return_barcode/static/src/js/return_product.js',
            'pos_return_barcode/static/src/js/order.js',
            'pos_return_barcode/static/src/js/barcode_popup.js',
            'pos_return_barcode/static/src/xml/return_product_template.xml',
            'pos_return_barcode/static/src/xml/barcode_popup.xml',
            'pos_return_barcode/static/src/xml/order_receipt.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
    'auto_install': False,
}
