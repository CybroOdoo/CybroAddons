# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
################################################################################
{
    'name': 'Pos Membership',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """This module is used to add membership discount in pos""",
    'description': """This is used to create membership types for customer and 
     also this customer can apply discounts for their orders using the membership
     code.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['pos_sale', 'sale', 'pos_loyalty', 'pos_discount','point_of_sale','sale_pdf_quote_builder'],
    'data': [
        'security/ir.model.access.csv',
        'views/membership_card_views.xml',
        'views/res_config_settings_views.xml',
        'views/customer_membership_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'membership_in_pos/static/src/js/product_screen.js',
            'membership_in_pos/static/src/js/abstract_awaitable_popup.js',
            'membership_in_pos/static/src/xml/membership_pop_up.xml',
            'membership_in_pos/static/src/js/membership_button.js',
            'membership_in_pos/static/src/xml/payment_screen.xml'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
