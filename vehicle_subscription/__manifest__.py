# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
    'name': 'Vehicle Subscription Management',
    'version': "16.0.1.0.0",
    'category': 'Fleet',
    'summary': """Vehicle Subscription Management From Website""",
    'description': """Vehicle Subscription Management From Website""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'contacts', 'fleet', 'account', 'sale', 'website',
                'portal', ],
    'data': [
        'security/vehicle_subscription_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/product_template_data.xml',
        'data/website_menu_data.xml',
        'data/mail_data.xml',
        'views/website_portal_subscription_template.xml',
        'views/fleet_vehicle_model_views.xml',
        'views/fleet_subscription_views.xml',
        'views/vehicle_insurance_views.xml',
        'views/subscription_request_views.xml',
        'views/insurance_type_views.xml',
        'views/online_subscription_template.xml',
        'views/online_vehicle_template.xml',
        'views/account_move_views.xml',
        'views/subscription_form_success_template.xml',
        'views/online_vehicle_cancellation_template.xml',
        'views/cancellation_request_views.xml',
        'views/change_vehicle_subscription_template.xml',
        'wizard/change_subscription_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'vehicle_subscription/static/src/js/website_subscription.js',
            'vehicle_subscription/static/src/js/vehicle_booking.js',
            'vehicle_subscription/static/src/js/subscription_cancellation.js',
            'vehicle_subscription/static/src/js/change_subscription_form.js',
            'vehicle_subscription/static/src/js/vehicle_subscription_success.js',
            'vehicle_subscription/static/src/js/change_subscription_request.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
