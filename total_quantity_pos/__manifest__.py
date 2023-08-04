# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R (odoo@cybrosys.com)
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
    'name': 'Total Items and Total Quantity in POS',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "To Show the Total Quantity and Total Items Ordered in POS",
    'description': "This app will shows the number of "
                   "products ordered and the total quantity"
                   " of products in the order summary in"
                   " the pos screen and bill.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'views/total_quantity_views.xml'
    ],
    'assets': {
       'point_of_sale.assets': [
            'total_quantity_pos/static/src/xml/TotalQuantitySummary.xml',
            'total_quantity_pos/static/src/xml/TotalQuantityReceipt.xml',
            'total_quantity_pos/static/src/js/QuantityOrderSummary.js',
            'total_quantity_pos/static/src/js/TotalQuantityReceipt.js',
       ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
