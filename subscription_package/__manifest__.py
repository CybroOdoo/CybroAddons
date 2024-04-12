# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: JANISH BABU (<https://www.cybrosys.com>)
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
    'name': 'Subscription Management',
    'version': '17.0.1.0.1',
    'summary': 'Subscription Package Management Module For Odoo17 Community',
    'description': 'Subscription Package Management Module specifically '
                   'designed for Odoo 17 Community edition. '
                   'This module aims to enhance the subscription '
                   'management capabilities within the Odoo platform, '
                   'providing users with advanced features and '
                   'functionalities for efficiently handling subscription '
                   'packages in the community version of Odoo 17.',
    'category': 'Sales',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale_management'],
    'data': [
        'security/subscription_package_groups.xml',
        'security/ir.model.access.csv',

        'data/uom_demo_data.xml',
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
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
