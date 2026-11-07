# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Refer and Earn',
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': 'Earn reward points through referrals and redeem them for product discounts.',
    'description': """Refer and Earn system for Odoo eCommerce.
        Allows registered customers to share their unique referral code with friends.
        When new users register using the referral code, the referrer earns reward points.
        Accumulated points can be redeemed for order discounts directly during cart checkout.
        Configure signup reward points and tiered discount percentages easily from settings.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail', 'website_sale', 'contacts'],
    'data': [
        'security/ir.access.csv',
        'data/product_template_data.xml',
        'data/refer_and_earn_mail_template.xml',
        'data/lack_of_points_template.xml',
        'data/refer_and_earn_menu.xml',
        'views/refer_and_earn_template.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/auth_signup_login_templates.xml',
        'views/apply_points_template.xml',
        'views/apply_discounts_views.xml',
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'refer_friend_and_earn/static/src/js/website_sale.js',
            'refer_friend_and_earn/static/src/css/refer_and_earn.css',
        ],
        'web.assets_unit_tests': [
            'refer_friend_and_earn/static/src/**/*',
            'refer_friend_and_earn/static/tests/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
