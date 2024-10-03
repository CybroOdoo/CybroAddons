# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technogies @cybrosys(odoo@cybrosys.com)
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
    'name': 'Advance HR Attendance Dashboard',
    'version': '15.0.1.0.0',
    'category': "Human Resources",
    'summary': """This module helps you to view leaves of employee based on
     different leave types.""",
    'description': """Advance HR Attendance Dashboard helps for 
     filtering attendance data,  finding specific employees attendance data,
     and for displaying attendance information, also we can print the
     attendance in pdf format .""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ["hr_holidays", "hr", "hr_attendance"],
    'data': [
        "views/hr_leave_type_views.xml",
        "views/advance_hr_attendance_dashboard_menus.xml",
        "views/res_config_settings_views.xml",
        "report/hr_attendance_reports.xml",
        "report/hr_attendance_templates.xml",
    ],
    "assets": {
        'web.assets_backend': [
            "advance_hr_attendance_dashboard/static/src/js/attendance_dashboard.js",
            "advance_hr_attendance_dashboard/static/src/scss/attendance_dashboard.scss",
        ],
        'web.assets_qweb': [
            "advance_hr_attendance_dashboard/static/src/xml/attendance_dashboard_templates.xml",
        ],
    },
    "external_dependencies": {
        "python": ["pandas"],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False
}
