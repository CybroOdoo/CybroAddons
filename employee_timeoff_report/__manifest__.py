# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
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
    'name': 'Employee Timeoff Report From Website',
    'version': '16.0.1.0.0',
    'summary': 'Employee timeoff report with OTP authentication for website',
    'description': """
        This module allows employees to securely view and print their time off
        reports on the website. """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Human Resources',
    'depends': ['website', 'hr_holidays'],
    'data': [
        'views/menus.xml',
        'views/auth_templates.xml',
        'views/templates.xml',
        'views/report_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'employee_timeoff_report/static/src/js/timeoff_auth.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,

    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
}
