# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'ZKTeco Biometric Attendance (ADMS Push)',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'ZKTeco biometric devices push attendance to Odoo over the ADMS/iclock protocol',
    'description': """
        ZKTeco Biometric Attendance Integration (ADMS)
        ==============================================
        
        Devices push their data directly to Odoo over HTTP using the ZKTeco
        ADMS (iclock) push protocol - no static IP, no polling, no middleware.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': [
        'hr_attendance',
    ],
    'data': [
        'security/zkteco_security.xml',
        'security/ir.model.access.csv',
        'data/zkteco_status_code_data.xml',
        'data/ir_cron_data.xml',
        'wizard/zkteco_wizard_views.xml',
        'views/zkteco_device_views.xml',
        'views/zkteco_attendance_log_views.xml',
        'views/zkteco_device_user_views.xml',
        'views/zkteco_device_command_views.xml',
        'views/zkteco_status_code_views.xml',
        'views/zkteco_biometric_views.xml',
        'views/hr_employee_views.xml',
        'views/zkteco_menus.xml',
    ],
    # pyzk is only needed for Direct IP mode; the ADMS push side works
    # without it, so it must not become a hard install requirement.
    'external_dependencies': {'python': ['pytz']},
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,

}
