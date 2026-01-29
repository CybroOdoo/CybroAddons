# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
    'name': 'Cleaning Management',
    'version': '15.0.1.0.0',
    "category": "Industries",
    'summary': """Cleaning Management with Online Booking System""",
    'description': """This module facilitates the booking of cleaning processes 
    and effectively manages the cleaning procedures.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://cybrosys.com/",
    'depends': ['base', 'website', 'hr', 'account'],
    'data': [
        "security/cleaning_management_groups.xml",
        'security/ir.model.access.csv',
        'views/cleaning_team_views.xml',
        'views/cleaning_team_duty_views.xml',
        'views/employee_details_views.xml',
        'views/cleaning_shift_views.xml',
        'views/cleaning_booking_views.xml',
        'views/cleaning_inspection_views.xml',
        'views/cleaning_management_website_template.xml',
        'views/building_type_views.xml',
        'views/cleaning_management_dashboard_views.xml',
        'views/cleaning_management_menus.xml',
        'data/cleaning_management_data.xml',
        'data/building_type_demo.xml',
        'data/cleaning_shift_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            '/cleaning_management/static/src/js/cleaning_management_website.js',
        ],
        'web.assets_backend': [
            '/cleaning_management/static/src/js/'
            'cleaning_management_dashboard.js',
            '/cleaning_management/static/src/css/'
            'cleaning_management_dashboard.css',
            'https://cdn.jsdelivr.net/npm/chart.js',
        ],
        'web.assets_qweb': [
            '/cleaning_management/static/src/xml/'
            'cleaning_management_dashboard_template.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
