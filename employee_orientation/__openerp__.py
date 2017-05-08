# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Employee Orientation & Training",
    'version': '9.0.1.0.0',
    "category": "Generic Modules/Human Resources",
    'summary': """Employee Orientation/Training Program""",
    'description': """Complete Employee Orientation/Training Program""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
    'depends': ['base', 'hr', 'mail', ],
    'data': [
        'views/orientation_checklist_line.xml',
        'views/orientation_checklist.xml',
        'views/employee_orientation.xml',
        'views/orientation_checklists_request.xml',
        'views/orientation_checklist_sequence.xml',
        'views/orientation_request_mail_template.xml',
        'views/employee_training.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
