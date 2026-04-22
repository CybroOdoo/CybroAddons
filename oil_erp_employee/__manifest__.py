# -*- coding: utf-8 -*-
#############################################################################
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
    'name': 'Oil & Gas Employee',
    'version': '19.0.1.0.0',
    'category': 'Oil ERP/Upstream',
    'summary': 'Track daily employee expenses on project tasks',
    'description': """
Adds an hourly wage field to employees and links employees to project tasks.
Provides a wizard on tasks to compute daily expenses from timesheet lines for
a selected date, creating per-employee expense records. Includes task-level
expense views and a smart button to review generated daily expenses.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'oil_erp_project',
        'oil_erp_equipment',
        'hr_timesheet',
        'hr_expense',
    ],
    'data': [
        'security/oil_employee_security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/project_task_views.xml',
        'views/task_daily_expense_views.xml',
        'views/hr_expense_views.xml',
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/daily_expense_wizard_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
