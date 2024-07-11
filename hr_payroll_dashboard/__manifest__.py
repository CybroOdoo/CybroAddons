# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    'name': "HR Payroll Dashboard",
    'version': '16.0.1.0.0',
    'category': 'Human Resource',
    'summary': """Detailed Dashboard View for Payroll Module""",
    'description': "This module helps you to see the Overview of Payroll, "
                   "here You can see the details of Attendance, Leaves, "
                   "Payslip contracts, etc.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr_payroll_community', 'hr_attendance', 'hr_expense'],
    'data': [
        'views/dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_payroll_dashboard/static/src/js/hr_payroll_dashboard.js',
            'hr_payroll_dashboard/static/src/css/lib/nv.d3.css',
            'hr_payroll_dashboard/static/src/css/dashboard.css',
            'hr_payroll_dashboard/static/src/css/style.scss',
            'hr_payroll_dashboard/static/src/js/lib/d3.min.js',
            'hr_payroll_dashboard/static/src/xml/payroll_dashboard.xml'
        ],
    },
    'images': ['static/description/banner.png'],
    "external_dependencies": {"python": ["pandas"]},
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': True,
}
