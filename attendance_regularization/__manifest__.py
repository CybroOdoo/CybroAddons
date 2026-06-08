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
    'name': "Open HRMS Attendance Regularization",
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manage employee attendance regularization requests for onsite work.',
    'description': """This module enables employees to submit attendance regularization requests for
    onsite work when their attendance is missing or incorrectly recorded. Employees can create requests 
    to update their attendance details, which are then reviewed and approved by managers.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr_attendance', 'hr_holidays',
                'oh_employee_creation_from_user'],
    'data': [
        'security/attendance_regularization_security.xml',
        'security/ir.model.access.csv',
        'views/reg_categories_views.xml',
        'views/attendance_regularization_views.xml',
    ],
    'demo': ['data/attendance_regular_demo.xml'],
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
