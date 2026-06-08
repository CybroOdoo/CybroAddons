# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
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
    'name': "Open HRMS Vacation Management",
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Vacation Management,manages employee vacation""",
    'description': """The 'Vacation Management System' is a robust platform
     designed to streamline and optimize the management of employee 
     vacations within an organization.""",
    'live_test_url': 'https://youtu.be/Pf7zf-PkdfA',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr','hr_leave_request_aliasing', 'project',
                'hr_payroll_community', 'account'],
    'data': [
        'security/hr_flight_ticket_rule.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'data/ir_sequence.xml',
        'data/hr_contribution_register_data.xml',
        'data/hr_salary_rule_data.xml',
        'data/mail_data_templates.xml',
        'data/res_partner_data.xml',
        'views/hr_flight_ticket_views.xml',
        'views/hr_leave_views.xml',
        'views/hr_payslip_views.xml',
        'views/pending_task_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/task_reassign_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
