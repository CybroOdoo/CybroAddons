# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: JANISH BABU  (odoo@cybrosys.com)
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
    'name': "Work Anniversary Reminder",
    'version': '16.0.1.1.0',
    'category': 'Human Resources/Employees',
    'summary': """Automatically send work anniversary emails to 
    employees on their joining date.""",
    'description': """Module helps to Automatically Send Work 
    Anniversary Email to Employee on Their Joining date""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['hr', 'mail', 'hr_contract'],
    'data': ['data/work_anniversary_cron_reminder.xml',
             'data/anniversary_reminder_template.xml',
             'views/hr_employee.xml'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
