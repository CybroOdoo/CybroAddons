# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    'name': 'Refer and Earn',
    'version': '14.0.1.0.0',
    'category': 'Website',
    'summary': "Refer your friend by using referral code and have points while"
               "they log in with that referral code. According to the secured"
               "points, it is possible to have discount on products",
    'description': "By using this module,we are able to share a referral code"
                   "with our friends and they are able to log in by that"
                   "referral code. Here it is possible to set a  sign up points"
                   "in the settings and it is also able to give the discounts in"
                   "percentage, for each points. Log in with our referral code"
                   "will helps to have points, and by using that points,"
                   "purchase the product at discount price",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail', 'website_sale', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_template_data.xml',
        'data/lack_of_points_templates.xml',
        'data/website_menu_data.xml',
        'data/refer_and_earn_mail_data.xml',
        'views/assets.xml',
        'views/refer_and_earn_template.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/auth_signup_login_templates.xml',
        'views/apply_points_templates.xml',
        'views/apply_discounts_views.xml',
        'views/sale_order_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
