# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': "POS Restaurant Dine-in/TakeAway",
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "This module will add the options Dine-in and Take away in Odoo POS.",
    'description': """The POS user can make orders as Dine-in or Take
                    away and it will create separate token for Take away orders.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'pos_restaurant'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/pos_order_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_takeaway/static/src/xml/Screens/ProductScreen/ReceiptScreen/OrderReceipt.xml',
            'pos_takeaway/static/src/xml/Screens/ProductScreen/ReceiptScreen/ReceiptHeader.xml',
            'pos_takeaway/static/src/xml/Screens/ProductScreen/ControlButton/TakeAway.xml',
            'pos_takeaway/static/src/js/Screens/ProductScreen/ReceiptScreen/ReceiptScreen.js',
            'pos_takeaway/static/src/js/Screens/ProductScreen/ControlButton/TakeAway.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
