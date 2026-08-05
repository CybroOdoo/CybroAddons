# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Harshitha AP (odoo@cybrosys.com)
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
    'name': 'Enterprise WPS Report Generation for UAE',
    'version': '19.0.1.0.0',
    'category': 'Generic Modules/Human Resources',
    'summary': 'Open HRMS Wps Payroll System For UAE',
    'description': """The module helps to print the salary information file for 
    a month in XLS format.""",
    'author': 'Cybrosys Techno Solutions, Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'depends': [
        'hr_payroll',
        'account_accountant',
        'hr_holidays',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/res_bank_views.xml',
        'views/res_company_views.xml',
        'wizard/hr_wps_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ent_uae_wps_report/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}