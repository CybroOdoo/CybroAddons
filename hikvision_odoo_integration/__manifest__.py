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
    'name': 'Hikvision Odoo Integration',
    'version': '18.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Hikvision Biometric Device Integration with Employee Management',
    'description': """Automatically sync attendance data between Hikvision biometric devices and Odoo. 
     Download attendance records, manage device users, 
     track employee check-ins/outs, and handle HR approvals for incomplete work hours.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr', 'hr_attendance','queue_job_cron_jobrunner','queue_job','mail','hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/email_template.xml',
        'data/queue_job_config.xml',
        'data/cron_job.xml',
        'wizard/hikvision_management_views.xml',
        'views/hikvision_logs_views.xml',
        'views/attendance_approval_views.xml',
        'views/hikvision_device_views.xml',
        'views/hikvision_employee_attendance_views.xml',
        'views/res_config_settings_views.xml',
		'wizard/attendance_rejection_views.xml',
],
    'assets': {
            'web.assets_backend': [
                'hikvision_odoo_integration/static/src/css/attendance_rejection.scss',
            ],
    },
    'license': 'AGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
