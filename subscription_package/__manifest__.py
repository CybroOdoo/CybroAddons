# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
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
    'name': 'Subscription Management',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'This module enhances subscription management with advanced features for efficiently managing '
               'subscription packages',
    'description': 'Subscription Package Management Module for Odoo 19. '
                   'This module aims to enhance subscription '
                   'management capabilities within the Odoo platform, '
                   'providing users with advanced features and '
                   'functionalities for efficiently handling subscription '
                   'packages.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'account', 'mail', 'uom'],
    'data': [
        'security/subscription_package_groups.xml',
        'security/ir.model.access.csv',
        'data/subscription_package_stop_data.xml',
        'data/subscription_stage_data.xml',
        'data/mail_subscription_renew_data.xml',
        'data/ir_cron_data.xml',
        'data/ir_sequence.xml',
        'views/subscription_package_views.xml',
        'views/product_template_views.xml',
        'views/subscription_package_plan_views.xml',
        'views/subscription_stage_views.xml',
        'views/subscription_package_stop_views.xml',
        'views/mail_activity_views.xml',
        'views/res_partner_views.xml',
        'views/recurrence_period_views.xml',
        'views/sale_order_views.xml',
        'views/product_product_views.xml',
        'report/subscription_report_view.xml',
        'wizard/subscription_close_views.xml',
    ],
    'demo': [
        'data/uom_demo_data.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
