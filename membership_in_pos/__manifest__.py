# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
    'name': 'Pos Membership',
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """This module is used to add membership discount in pos""",
    'description': """This is used to create membership types for customer and 
     also this customer can apply discounts for their orders using the membership
     code.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['pos_sale', 'sale', 'pos_loyalty', 'pos_discount','point_of_sale'],
    'data': {
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/customer_membership_views.xml',
        'views/membership_card_views.xml',
    },
    'assets': {
        'point_of_sale.assets': [
            'membership_in_pos/static/src/js/AbstractAwaitablePopup.js',
            'membership_in_pos/static/src/js/PaymentScreen.js',
            'membership_in_pos/static/src/js/ProductScreen.js',
            'membership_in_pos/static/src/xml/membership_pop_up.xml',
            'membership_in_pos/static/src/xml/PaymentScreen.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
