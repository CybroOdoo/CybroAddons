# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
    'name': 'POS Booking Order',
    'version': '15.0.1.0.1',
    'summary': """Users can now book pickup or delivery orders directly 
     from the Point of Sale (POS) session, later can confirm as POS order.""",
    'description': """The module helps you to book orders from Shop,
                  Bar/Restaurant in POS.User can create pickup or delivery 
                  orders,later confirm booked orders to POS orders.""",
    'category': 'Point of Sale',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'point_of_sale'],
    'images': ['static/description/banner.jpg'],
    'data': ['security/ir.model.access.csv',
             'data/ir_sequence_data.xml',
             'views/pos_config_views.xml',
             'views/book_order_views.xml',
             'views/pos_order_views.xml'
             ],
    'assets': {
        'point_of_sale.assets': [
            '/pos_book_order/static/src/js/BookOrderPopup.js',
            '/pos_book_order/static/src/js/Ticketscreen.js',
            '/pos_book_order/static/src/js/BookOrderButton.js',
            '/pos_book_order/static/src/js/BookedOrdersButton.js',
            '/pos_book_order/static/src/js/BookedOrdersScreen.js',
            '/pos_book_order/static/src/js/models.js',
        ],
        'web.assets_qweb': [
            '/pos_book_order/static/src/xml/Buttons.xml',
            '/pos_book_order/static/src/xml/BookOrderPopup.xml',
            '/pos_book_order/static/src/xml/BookedOrdersScreen.xml',
            '/pos_book_order/static/src/xml/OrderReceipt.xml',
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
