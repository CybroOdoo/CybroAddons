# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreenath K, Shafna K (odoo@cybrosys.com)
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
    'name': 'Geolocation in HR Attendance',
    'version': '16.0.1.0.0',
    'summary': "The attendance location of the employee",
    'description': "This module helps to identify the checkin/out location of the employee",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Human Resources',
    'depends': ['base', 'hr', 'hr_attendance'],
    'data': [
        'views/hr_attendance_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_attendance_user_location/static/src/js/my_attendances.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'external_dependencies': {'python': ['geopy']},
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
