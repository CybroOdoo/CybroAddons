# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
{
    'name': 'Enterprise OpenHRMS Multi-Company',
    'version': '19.0.1.0.0',
    'category': 'Generic Modules/Human Resources',
    'summary': """Enables Multi-Company""",
    'description': """This module enables HR multi company, hence HR manager 
     can easily handle multi company process separately. We can activate
     multi company feature in general settings as usual. This will
     automatically add company field in every HR related records""",
    'author': 'Cybrosys Techno Solutions, Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base',
                'hr',
                'hr_payroll',
                'hr_expense',
                'hr_attendance',
                'hr_holidays'],
    'data': [
        'security/hr_attendance_security.xml',
        'security/hr_department_security.xml',
        'security/hr_expense_security.xml',
        'security/hr_leave_security.xml',
        'security/hr_payslip_security.xml',
        'security/hr_salary_rule_category_security.xml',
        'views/hr_attendance_views.xml',
        'views/hr_salary_rule_category_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
