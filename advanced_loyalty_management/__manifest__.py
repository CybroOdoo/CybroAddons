# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Advanced Loyalty Management',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Advanced loyalty Management',
    'description': """When an order is refunded, any loyalty points gained from 
    that purchase are also revoked. This means that the points earned through
    the refunded transaction will be deducted from the customer's loyalty
    points balance.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['pos_loyalty', 'sale'],
    'data': [
        'views/loyalty_program_views.xml',
        'views/loyalty_reward_rule_views.xml',
        'views/res_partner_views.xml',
        'views/pos_order_line_views.xml',
        'views/loyalty_kanban_views.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'advanced_loyalty_management/static/src/xml/pos_loyalty_refund.xml',
            'advanced_loyalty_management/static/src/js/pos_loyalty_deduction.js',
            'advanced_loyalty_management/static/src/xml/pos_loyalty_receipt.xml',
            'advanced_loyalty_management/static/src/js/pos_loyalty_deduction_receipt.js',
            'advanced_loyalty_management/static/src/xml/pos_loyalty_change.xml',
            'advanced_loyalty_management/static/src/js/pos_loyalty_change.js',
            'advanced_loyalty_management/static/src/xml/pos_loyalty_popup.xml',
            'advanced_loyalty_management/static/src/js/pos_loyalty_popups.js',
            'advanced_loyalty_management/static/src/js/pos_reward_button.js',
            'advanced_loyalty_management/static/src/xml/pos_redeem_reward_popup.xml',
            'advanced_loyalty_management/static/src/js/pos_reward_redeem_popup.js',
            'advanced_loyalty_management/static/src/js/pos_loyalty_card.js',
            'advanced_loyalty_management/static/src/js/pos_payment_screen.js',
            'advanced_loyalty_management/static/src/js/pos_ticketscreen.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
