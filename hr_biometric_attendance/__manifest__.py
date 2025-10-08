# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': "HR Biometric Device Integration",
    'version': "16.0.1.0.0",
    'summary': "Integrating Zk Biometric Devices With HR Attendance",
    'description': '''This module integrates Odoo with ZK biometric devices, 
    incorporating features such as live capturing and user management''',
    'category': 'Human Resources',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup', 'hr_attendance', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/ir_action_data.xml',
        'wizards/user_management_views.xml',
        'wizards/employee_biometric_views.xml',
        'views/biometric_device_details_views.xml',
        'views/hr_employee_views.xml',
        'views/daily_attendance_views.xml',
        'views/res_config_settings_views.xml',
        'views/biometric_device_attendance_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_biometric_attendance/static/src/xml/stopwatch_view.xml',
            'hr_biometric_attendance/static/src/js/stopwatch.js',
        ]
    },
    'external_dependencies': {
        'python': ['pyzk'], },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
