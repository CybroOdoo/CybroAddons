# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
    'name': 'Open HRMS Biometric Device Integration',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Integrating Biometric Device With HR Attendance (Face + Thumb)',
    'description': 'This module integrates Odoo with the biometric device(Model: ZKteco uFace 202)',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base_setup', 'hr_attendance', 'web','hr_attendance_gantt'],
    'data': [
         'security/ir.model.access.csv',
        'security/biometric_device_details_security.xml',
        'data/biometric_device_details_data.xml',
        'data/hr_employee_data.xml',
        'wizard/user_management_views.xml',
        'wizard/employee_biometric_views.xml',
        'views/biometric_device_details_views.xml',
        'views/hr_employee_views.xml',
        'views/daily_attendance_views.xml',
        'views/res_config_settings_views.xml',
        'views/biometric_device_attendance_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'oh_hr_zk_attendance/static/src/xml/stopwatch_view.xml',
            'oh_hr_zk_attendance/static/src/js/stopwatch.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
