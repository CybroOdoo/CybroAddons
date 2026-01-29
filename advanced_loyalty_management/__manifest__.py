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
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Enhanced Loyalty Program Features',
    'description': """In this module, we have incorporated new features such as
    converting changes into loyalty points, displaying claimed rewards history, and
    introducing a new type of reward. These enhancements aim to provide a more 
    comprehensive and rewarding experience for customers engaging with the loyalty 
    program.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'pos_loyalty', 'base', 'sale_management'],
    'data': [
        'views/res_partner_views.xml',
        'views/loyalty_rewards_views.xml',
        'views/loyalty_program_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'advanced_loyalty_management/static/src/js/pos_payment_screen.js',
            'advanced_loyalty_management/static/src/js/pos_change_popup.js',
            'advanced_loyalty_management/static/src/js/pos_order_line.js',
            'advanced_loyalty_management/static/src/js/pos_order.js',
            'advanced_loyalty_management/static/src/js/rewardbutton.js',
            'advanced_loyalty_management/static/src/js/reward_popup.js',
        ],
        'web.assets_qweb': [
            'advanced_loyalty_management/static/src/xml/pos_loyalty_change.xml',
            'advanced_loyalty_management/static/src/xml/pos_change_popup.xml',
            'advanced_loyalty_management/static/src/xml/reward_popup.xml',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
