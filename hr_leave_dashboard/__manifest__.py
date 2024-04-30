# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Hr Leave Dashboard",
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Advanced Leave Dashboard helps to view your and your 
     subordinate's details""",
    'description': """Advanced Leave Dashboard  brings a multipurpose graphical 
     dashboard for Time Off module and making the relationship management better 
     and easier""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'hr_holidays', 'hr_org_chart'],
    'data': [
        'report/hr_leave_reports.xml',
        'report/hr_leave_report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_leave_dashboard/static/src/js/calendar_model.js',
            'hr_leave_dashboard/static/src/js/calendar_year_renderer.js',
            'hr_leave_dashboard/static/src/js/hooks.js',
            'hr_leave_dashboard/static/src/js/emp_org_chart.js',
            'hr_leave_dashboard/static/src/js/time_off_emp_card.js',
            'hr_leave_dashboard/static/src/js/time_off_emp_dashboard.js',
            'hr_leave_dashboard/static/src/xml/approval_status_card_templates.xml',
            'hr_leave_dashboard/static/src/xml/time_off_emp_dashboard_templates.xml',
            'hr_leave_dashboard/static/src/xml/emp_org_chart_templates.xml',
            'hr_leave_dashboard/static/src/xml/emp_department_card_templates.xml',
            'hr_leave_dashboard/static/src/xml/time_off_emp_card_templates.xml',
            'hr_leave_dashboard/static/src/css/hr_leave_dashboard.css',
            'hr_org_chart/static/src/fields/hr_org_chart.scss',
            'hr_leave_dashboard/static/src/scss/time_off_dashboard.scss',
            'hr_holidays/static/src/dashboard/time_off_card.scss',
            'hr_leave_dashboard/static/src/scss/calendar_renderer.scss'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
