# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'version': "15.0.1.0.0",
    'category': "Point of Sale",
    'summary': "Advanced POS Receipt with Customer Details and Invoice "
               "Details",
    'description': "Advanced POS Receipt with Customer Details and Invoice "
                   "Details refers to a sophisticated and highly developed "
                   "Point of Sale (POS) receipt system that incorporates "
                   "comprehensive information about the customer and detailed "
                   "invoice specifics. ",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale', 'sale', 'account', 'web'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'web/static/lib/zxing-library/zxing-library.js',
            'pos_receipt_extend/static/src/js/payment.js',
        ],
        'web.assets_qweb': [
            'pos_receipt_extend/static/src/xml/order_receipt_templates.xml',
        ]
    },
    'images': ['static/description/banner.jpg',],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
