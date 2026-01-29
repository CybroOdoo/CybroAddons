# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin(<http://www.cybrosys.com>)
#
#    you can modify it under the terms of the GNU LESSER
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
##############################################################################
{
    'name': 'POS Category Wise Receipt',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Category wise receipt for Point of Sale',
    'description': """This module aims to print category-wise receipts for 
     products ordered from Point of Sale.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "http://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'assets': {
        'web.assets_backend': [
            'pos_category_wise_receipt/static/src/js/Screens/ReceiptScreen/OrderReceipt.js',
        ],
        'web.assets_qweb': [
            'pos_category_wise_receipt/static/src/xml/Screens/ReceiptScreen/OrderReceipt.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
