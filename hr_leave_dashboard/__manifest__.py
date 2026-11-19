# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
{
    'name': 'HR Leave Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Human Resources',
    'summary': """HR Leave Dashboard, Time Off Dashboard, Leave Approval Status, Employee Org Chart, Leave Report, Odoo20 HR Dashboard""",
    'description': """
     Extends the Time Off dashboard with an employee profile card, an org chart
     with team lists, the department's absentees and upcoming public holidays,
     the team's leave approval status by period, and a PDF leave report.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr', 'hr_holidays'],
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
        ],
    },
    'license': 'OPL-1',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
