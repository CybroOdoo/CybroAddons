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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Show Booking Management",
    'version': '20.0.1.0.0',
    'category': 'Services',
    'summary': "Manage shows and book shows easily.",
    'description': """A module for show booking management. Administrators
    manage the shows and users book them on the website by selecting the date,
    screen, time slot and seats.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail', 'product', 'account_payment', 'portal', 'website'],
    'data': [
        'security/show_booking_management_groups.xml',
        'security/ir.access.csv',
        'data/product_product_data.xml',
        'data/report_paperformat_data.xml',
        'data/mail_template_data.xml',
        'data/ir_sequence_data.xml',
        'data/website_menu_data.xml',
        'data/portal_entry_data.xml',
        'data/ir_cron_data.xml',
        'views/movie_movie_views.xml',
        'views/show_type_views.xml',
        'views/cast_type_views.xml',
        'views/movie_cast_views.xml',
        'views/time_slots_views.xml',
        'views/movie_screen_views.xml',
        'views/movie_registration_views.xml',
        'views/account_move_views.xml',
        'views/website_templates.xml',
        'views/portal_template.xml',
        'report/movie_registration_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'show_booking_management/static/src/js/time_widget.js',
            'show_booking_management/static/src/xml/**/*.xml',
        ],
        'web.assets_frontend': [
            'show_booking_management/static/src/js/bookShow.js',
            'show_booking_management/static/src/js/selectSeat.js',
            'show_booking_management/static/src/css/show_booking_management.css',
        ],
        'web.assets_tests': [
            'show_booking_management/static/tests/tours/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
