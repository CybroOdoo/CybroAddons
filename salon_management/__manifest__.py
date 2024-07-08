# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Beauty Spa Management',
    'version': '17.0.1.0.0',
    "category": "Services",
    'summary': 'Beauty Parlour Management with Online Booking System',
    'description': 'This module to helps your customers to do the online '
                   'booking for using the service. This module integrates with '
                   'other Odoo modules like accounting and website.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account', 'base_setup', 'mail', 'website', 'contacts'],
    'data': [
        'security/salon_management_groups.xml',
        'security/ir.model.access.csv',
        'data/salon_website_menu.xml',
        'data/salon_chair_cron_action.xml',
        'data/salon_management_mail_template.xml',
        'data/salon_chair_sequence.xml',
        'data/salon_order_sequence.xml',
        'data/salon_management_dashboard_tag.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/salon_booking_templates.xml',
        'views/salon_chair_views.xml',
        'views/salon_working_hours.xml',
        'views/salon_service_views.xml',
        'views/salon_booking_views.xml',
        'views/salon_order_views.xml',
        'views/salon_management_menus.xml',
    ],
    'demo': [
        'data/product_template_data.xml',
        'data/res_partner_data.xml',
        'data/salon_holiday_data.xml',
        'data/salon_stages_data.xml',
        'data/salon_working_hours_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'salon_management/static/src/css/salon_dashboard.css',
            'salon_management/static/src/xml/salon_dashboard.xml',
            'salon_management/static/src/js/salon_dashboard.js',
        ],
        'web.assets_frontend': [
            'salon_management/static/src/css/salon_website.css',
            'salon_management/static/src/js/website_salon_booking.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
