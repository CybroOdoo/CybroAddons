# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Advanced POS Receipt",
    "description": """Advanced POS Receipt with Customer Details and Invoice Details""",
    "summary": "Advanced POS Receipt with Customer Details and Invoice Details",
    "category": "Point of Sale",
    "version": "16.0.1.0.0",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'sale', 'account'],
    'data': [
        'views/res_config_settings.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_receipt_extend/static/src/xml/OrderReceipt.xml',
            'pos_receipt_extend/static/src/js/pos_order_receipt.js',
            'pos_receipt_extend/static/src/js/payment.js',
        ]
    },
    'images': ['static/description/banner.png', ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
